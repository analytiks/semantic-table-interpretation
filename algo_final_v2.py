from table import Table
from modules.DBPediaQueryInterface import get_exact_label_match, \
                                          get_all_properties_by_class, \
                                          get_all_property_relations_by_instance, \
                                          get_all_instance_properties, \
                                          get_parents
import re
import itertools
import logging
from tqdm import tqdm
import pprint
import networkx as nx
import matplotlib.pyplot as plt
from sumproduct import Variable, Factor, FactorGraph
import numpy as np
import math
from whoosh.analysis import NgramAnalyzer
from whoosh.fields import Schema, NGRAMWORDS, TEXT
from whoosh.qparser import QueryParser
import os, os.path
from whoosh import index
from whoosh.filedb.filestore import RamStorage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("algo-basic")

class Entity(object):
    def __init__(self, iid, itype, uri):
        self.id = iid
        self.type = itype
        self.uri = uri
        self.values = set()
    
    def add_value(self, value):
        self.values.add(value)

def get_common_cases(val):
    """ For a given value create the possible variations
        to search the ontology
    """
    cases = list()
    cases.append(val.upper())
    cases.append(val.lower())
    cases.append(val.title())
    return cases

def formatURI(uri, etype):
    """ Format the URI to a friendly version
    """ 
    if etype == "class":
        return "dbo:" + uri.replace("http://dbpedia.org/ontology/", "")
    elif etype == "property":
        return "dbp:" + uri.replace("http://dbpedia.org/ontology/", "")
    elif etype == "instance":
        return "dbr:" + uri.replace("http://dbpedia.org/resource/", "")
    return uri

def create_entity(entities, graph, candidate, etype):
    iid = formatURI(candidate, etype)
    if iid not in entities:
        entities[iid] = Entity(iid, etype, candidate)
        graph.add_node(iid)
    return iid

def delete_entity(entities, graph, iid):
    if iid in entities:
        entities.pop(iid)
        graph.remove_node(iid)

def get_cell_instance_classes(table, graph, entities):
    """ Function to find the possible candidates for each NE cell
        and corresponding class types of each cell candidate
    """
    #search only for the NE cells
    ne = table.get_NE_cols()
    col_count = 1
    for column in ne.columns:
        col_id = create_entity(entities, graph, "C_%d" % col_count, "column")
        col_count += 1
        column.candidates.add(create_entity(entities, graph, "None", "None"))

        for cell in tqdm(column.cells):
            #make sure that non NE cells are not here
            try:
                #TODO: find what's ging on here
                cell.value.split()
            except:
                continue

            value = " ".join(cell.value.split()).strip()
            value_perms =  get_common_cases(value)

            for perm in value_perms:
                candidates = get_exact_label_match(perm)

                if candidates is not None and len(candidates) > 0:
                    cell_candidate = None

                    for candidate in candidates:
                        column_candidate = candidate["type"]["value"]

                        if column_candidate.find("http://dbpedia.org/ontology") == -1:
                            continue
                        
                        if cell_candidate is None:
                            cell_candidate = candidate["uri"]["value"]
                            cell_id = create_entity(entities, graph, cell_candidate, "instance")
                            cell.candidates.add(cell_id)
                        
                        column_id = create_entity(entities, graph, column_candidate, "class")
                        column.candidates.add(column_id)
                        #add the created relations to the graph structure
                        graph.add_edge(cell_id, column_id)

                        #this one is the column itself
                        graph.add_edge(col_id, cell_id)
                    break
        

def get_class_properties(table, graph, entities):
    """ Function to use the candidates of the cells to retrieve
        the properties where 
                        <candidate> of property
                        property of <candidate>
    """
    ne = table.get_NE_cols()
    for column in ne.columns:
        column_candidates = column.candidates

        column_property_candidates = {}

        for cell in tqdm(column.cells):
            for candidate in cell.candidates:
                #for some reason if the candidate is null
                if candidate is None:
                    continue
                

                #this one find the properties suggested to the belonging class
                #properties of the instance
                #these ones we add to the graph and then connect to the candidate classes
                properties = get_all_instance_properties(entities[candidate].uri)
                if properties is not None:
                    for p in properties:
                        prop = p["property"]["value"]

                        if prop.find("http://dbpedia.org/ontology") == -1:
                            continue

                        exclusion = [
                            "http://dbpedia.org/ontology/abstract",
                            "http://dbpedia.org/ontology/thumbnail",
                            "http://dbpedia.org/ontology/wikiPageID",
                            "http://dbpedia.org/ontology/wikiPageRevisionID",
                            "http://dbpedia.org/ontology/wikiPageExternalLink"
                        ]

                        if prop in exclusion:
                           continue
                        
                        prop_id = create_entity(entities, graph, prop, "property")
                        if prop_id not in column_property_candidates:
                            column_property_candidates[prop_id] = 0
                        column_property_candidates[prop_id] += 1

                        #TODO: modify this to include only the parents of
                        #related cell instances?
                        for column_candidate in column_candidates:
                            #check if cell and column candidates are related
                            if graph.has_edge(candidate, column_candidate):
                                graph.add_edge(column_candidate, prop_id)
                        
                        #adding the property labels
                        entities[prop_id].add_value(p["callret-1"]["value"])
        
        #now filter the column_property_space to select the top 50%
        if len(column_property_candidates) > 0:
            cmax = column_property_candidates[max(column_property_candidates, key=column_property_candidates.get)]
            selected_property_candidates = filter(lambda k: column_property_candidates[k] > cmax*0.5, 
                                                          column_property_candidates)
        
            #keep the winning properties in the graph and remove the rest
            for prop in column_property_candidates:
                if prop not in selected_property_candidates:
                    delete_entity(entities, graph, prop)

def get_column_parents(table, graph, entities):
    """This binds any super classes of the column candidates"""

    ne = table.get_NE_cols()
    for column in ne.columns:
        for candidate in column.candidates:
            if candidate == "None":
                continue

            parents = get_parents(candidate)
            
            for parent in parents:
                pcand = parent['c']['value']
                if "http://dbpedia.org/ontology" not in pcand:
                    continue
                
                parent_id = formatURI(pcand, "class")
                if parent_id in entities:
                    for cell in column.cells:
                        for cell_candidate in cell.candidates:
                            if graph.has_edge(cell_candidate, candidate):
                                graph.add_edge(cell_candidate, parent_id)

                    graph.add_edge(candidate, parent_id)
                
def get_column_properties(table, graph, entities):
    """ Function to use the candidates of the cells to retrieve
        the properties where 
                        <candidate> of property
                        property of <candidate>
    """
    ne = table.get_NE_cols()
    for column in ne.columns:
        for cell in tqdm(column.cells):
            for candidate in cell.candidates:
                #for some reason if the candidate is null
                if candidate is None:
                    continue

                #this one find the properties that are candidates for the column
                #finds column property candidate space
                #we append these to the graph but leave as it is to check
                #if a class would link to them as their own properties
                properties = get_all_property_relations_by_instance(entities[candidate].uri)
                if properties is not None:
                    for p in properties:
                        prop = p["property"]["value"]

                        if prop.find("http://dbpedia.org/ontology") == -1:
                            continue

                        exclusion = [
                            "http://dbpedia.org/ontology/wikiPageRedirects",
                            "http://dbpedia.org/ontology/wikiPageDisambiguates"
                        ]

                        if prop in exclusion:
                           continue
                        
                        prop_id = formatURI(prop, "property")
                        if prop_id in entities:
                            column.candidates.add(prop_id)
                            graph.add_edge(candidate, prop_id)
                        
                            #adding the property labels
                            entities[prop_id].add_value(p["callret-1"]["value"])

def search_column_headers(entities, graph, table):
    #initiallize the Bigram index
    schema = Schema(
        title=NGRAMWORDS(minsize=2, maxsize=4, stored=True, field_boost=1.0, 
                         tokenizer=None, at='start', queryor=False, sortable=False),
        uri=TEXT(stored=True)
    )

    storage = RamStorage()
    ix = storage.create_index(schema)
    writer = ix.writer()
    for e in entities:
        entity = entities[e]
        if entity.type != "property":
            continue
        
        for value in entity.values:
            writer.add_document(title=unicode(value), uri=unicode(e))
    
    writer.commit()

    #loop the literal colunm headers
    for column in table.columns:
        query = column.header
        qp = QueryParser("title", schema=ix.schema)

        with ix.searcher() as searcher:
            for word in query.split():
                q = qp.parse(word.strip())
                results = searcher.search(q)
                for result in results:
                    column.candidates.add(result['uri'])

def calcualte_probability_score(entities, graph, cand1, cand2):
    """Function takes in the candidate space graph and
       calculate the probabilities accoridngly
    """
    delta = 0.00000000001
    if cand1.type == "class" and cand2.type == "class":
        return 0.0
    elif cand1.type == "class" and cand2.type == "instance":
        #first check if cand1 and cand2 are related
        # if graph.has_edge(cand1.id, cand2.id):
        if cand1.type == "None":
            return delta

        if nx.has_path(graph, cand2.id, cand1.id):
            #find ambiguity score
            ambiguity = 0
            for e in entities:
                if entities[e].type == "column":
                    if nx.has_path(graph, e, cand1.id):
                        if nx.shortest_path_length(graph, e, cand1.id) == 2:
                            ambiguity += 1
            
            specficiy = 0
            for node in graph.neighbors(cand1.id):
                if entities[node].type == "class":
                    specficiy += 1

            # if ambiguity == 0:
            #     return 1.0
            # print cand1.id, specficiy
            return 1.0*specficiy
        else:
            return delta
    elif cand1.type == "property" and cand2.type == "instance":
        # print cand1.id, cand2.id, graph.has_edge(cand1.id, cand2.id)
        #first check if cand1 and cand2 are related
        if cand1.type == "None":
            return delta

        neigh = 0
        for node in graph.neighbors(cand1.id):
            if entities[node].type == "instance":
                neigh += 1

        if graph.has_edge(cand2.id, cand1.id):
            return 1.0
        else:
            return delta
    elif (cand1.type == "class" and cand2.type == "property") or \
         (cand1.type == "property" and cand2.type == "class"):
            if cand1.type == "None" or cand2.type == "None":
                return 1.0
            
            if graph.has_edge(cand1.id, cand2.id) or \
               graph.has_edge(cand2.id, cand1.id):
                # print cand1.id, cand2.id
                return 1.0
            else:
                return delta
    elif cand1.type == "property" and cand2.type == "property":
        #first check if cand1 and cand2 are related
        # if nx.has_path(graph, cand1.id, cand2.id):
        #     return 1.0
        # else:
        #     return delta
        return 1.0

    return delta

def generate_markov_net(entities, graph, table):
    #now we take a deep breath and start to put all this shit into the 
    #markov model
    #we first imagine the factor graph
    markov_net = FactorGraph(silent=True)
    
    for c in range(len(table.columns)):
        column = table.columns[c]
        #name columns as : C_1, C_2
        column_name = "C_%d" % c
        column_candidates = list(column.candidates)
        column_card = len(column_candidates)
        var1 = Variable(column_name, column_card)

        if column_card == 0:
            continue

        for r in range(len(column.cells)):
            cell = column.cells[r]
            #name cells as : D_1_1, D_2_1
            cell_name = "D_%d_%d" % (r, c)
            cell_candidates = list(cell.candidates)
            cell_card = len(cell_candidates)
            var2 = Variable(cell_name, cell_card)

            if cell_card == 0:
                continue
            
            #for each pair of column-cell, create a factor now
            #needs to hold transition matrix of |col|x|cell|
            #usually it would be nx1
            mat = np.zeros([column_card, cell_card])

            #now using the graph, calculate the probabilities
            #CAREFULLY
            for i in range(column_card):
                col_id = column_candidates[i]
                col_entity = entities[col_id]

                for j in range(cell_card):
                    cell_id = cell_candidates[j]
                    cell_entity = entities[cell_id]

                    score = calcualte_probability_score(entities, graph, col_entity, cell_entity)

                    mat[i][j] = score
            
            # print mat
            factor_name = "%s_%s" % (column_name, cell_name)
            factor = Factor(factor_name, mat)
            markov_net.add(factor)
            markov_net.append(factor_name, var1)
            markov_net.append(factor_name, var2)
    
    #now that shit works then, we add column-column factor nodes
    for c1 in range(len(table.columns)-1):
        #create nodes for both columns
        column_1 = table.columns[c1]
        column_1_name = "C_%d" % c1
        column_1_candidates = list(column_1.candidates)
        column_1_card = len(column_1_candidates)
        var1 = Variable(column_1_name, column_1_card)

        if column_1_card == 0:
            continue

        for c2 in range(c1+1, len(table.columns)):
            column_2 = table.columns[c2]
            column_2_name = "C_%d" % c2
            column_2_candidates = list(column_2.candidates)
            column_2_card = len(column_2_candidates)
            var2 = Variable(column_2_name, column_2_card)

            if column_2_card == 0:
                continue 
            
            #for each pair of column-cell, create a factor now
            #needs to hold transition matrix of |col1|x|col2|
            #usually it would be nx1
            mat = np.zeros([column_1_card, column_2_card])

            #we gotta loop candidates of both now
            for i in range(column_1_card):
                col_1_id = column_1_candidates[i]
                col_1_entity = entities[col_1_id]

                for j in range(column_2_card):
                    col_2_id = column_2_candidates[j]
                    col_2_entity = entities[col_2_id]

                    score = calcualte_probability_score(entities, graph, col_1_entity, col_2_entity)

                    mat[i][j] = score
            
            # C_1_C_2
            factor_name = "%s_%s" % (column_1_name, column_2_name)
            factor = Factor(factor_name, mat)
            markov_net.add(factor)
            markov_net.append(factor_name, var1)
            markov_net.append(factor_name, var2)
    
    return markov_net

def visualize_graph(graph, entities):
    mapping = {
        "class": "blue",
        "instance": "green",
        "col_property": "red",
        "clz_property": "yellow",
        "property": "pink",
        "column": "yellow",
        "None": "black"
    }
    node_color = map(lambda node: mapping[entities[node].type],graph.nodes())
    nx.draw(graph, with_labels=True, node_color=node_color)
    plt.show()
        
def algo(table):
    #graph data structure to hold the instance, class and property candidates
    graph = nx.DiGraph()

    #entities hold all the entity instances added to the graph
    entities = dict()

    #get cell instance candidates from ontology along with the belonging classes
    #these will be added to entities and the graph as well
    get_cell_instance_classes(table, graph, entities)

    # visualize_graph(graph, entities)
    
    get_column_parents(table, graph, entities)

    # visualize_graph(graph, entities)

    get_class_properties(table, graph, entities)

    get_column_properties(table, graph, entities)

    # visualize_graph(graph, entities)

    search_column_headers(entities, graph, table)

    

    markov_net = generate_markov_net(entities, graph, table)    
    markov_net.compute_marginals()

    table_class = None

    for c in range(len(table.columns)):
        try:
            # print c.candidates
            marginals =  markov_net.nodes['C_%d' % c].marginal().tolist()
            prediction = [max(marginals), list(table.columns[c].candidates)[marginals.index(max(marginals))]]
            print list(table.columns[c].candidates) 
            print marginals
            label = "http://dbpedia.org/ontology/" + prediction[1][4:]

            table.columns[c].predicted_labels = [[label, prediction[0]]]
            
            if table_class is None and "dbo" in prediction[1]:
                table_class = label
                table.columns[c].is_subject_column = True
        except Exception as e:
            print "ERROR", e
            pass
    
    if table_class is None:
        best_marginal = -1
        subcol = -1
        for c in range(len(table.columns)):
            try:
                # print c.candidates
                marginals =  markov_net.nodes['C_%d' % c].marginal().tolist()
                predictions = list(table.columns[c].candidates)

                for i in range(len(marginals)):
                    if "dbo" in predictions[i]:
                        if marginals[i] > best_marginal:
                            # print predictions[i]
                            table_class = predictions[i]
                            best_marginal = marginals[i]
                            subcol = c
                    
            except Exception as e:
                # print "ERROR", e
                pass

        if subcol > -1:
            print "FINAL", table_class
            label = "http://dbpedia.org/ontology/" + table_class[4:]
            table.columns[subcol].predicted_labels = [[label, best_marginal]]
            table.columns[subcol].is_subject_column = True

    # print table_class
    # visualize_graph(graph, entities)
    
    return table
        
