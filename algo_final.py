from table import Table
from modules.DBPediaQueryInterface import get_exact_label_match, \
                                          get_all_properties_by_class, \
                                          get_all_property_relations_by_instance, \
                                          get_all_instance_properties
import re
import itertools
import logging
from tqdm import tqdm
import pprint
import networkx as nx
import matplotlib.pyplot as plt
from sumproduct import Variable, Factor, FactorGraph
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("algo-basic")

data = {

}

instance_class_matrix = dict()
instance_property_matrix = dict()
class_property_matrix = dict()
class_property_by_instance_matrix = dict()

class Entity(object):
    def __init__(self, iid, type):
        self.id = iid
        self.type = type

def get_common_cases(val):
    cases = list()
    cases.append(val.upper())
    cases.append(val.lower())
    cases.append(val.title())
    return cases

def process_candidates(candidate_space, concepts, is_header=False):
    cell_label = None
    for concept in concepts:
        if is_header:
            candidate = concept["uri"]["value"]
        else:
            candidate = concept["type"]["value"].encode("utf-8")
       
        if candidate.find("http://dbpedia.org/ontology") == -1:
            continue

        if cell_label is None:
            cell_label = concept["uri"]["value"]

        if cell_label not in instance_class_matrix:
            instance_class_matrix[cell_label] = set()

        if candidate not in candidate_space:
            candidate_space[candidate] = {
                "type": "class",
                "count": 0
            }
        candidate_space[candidate]["count"] += 1
        instance_class_matrix[cell_label].add(candidate)
    
    return cell_label

def find_cell_and_header_entities(table):
    """ First use exact string matching to
            1. header --> column classes
            2. cells --> instances
    """
    ne = table.get_NE_cols()

    #column and cell annotation
    for column in ne.columns:
        candidate_classes = dict()

        # logger.info("Processing header: %s" % column.header)
        # for val in get_common_cases(column.header):
        #     concept = get_exact_label_match(val)
        #     if concept is not None and len(concept) > 0:
        #         process_candidates(candidate_classes, concept, True)
        #         break

        for cell in tqdm(column.cells):
            value = " ".join(cell.value.split()).strip()
            value_perms =  get_common_cases(value)

            # logger.info("Processing cell: %s" % value)
            for perm in value_perms:
                concept = get_exact_label_match(perm)
                if concept is not None and len(concept) > 0:
                    # logger.info("--candidate found!")
                    cell.predicted_labels = [[process_candidates(candidate_classes, concept), "instance", 0]]
                    break     
        
        # column.predicted_labels = candidate_classes.items()
        data[column.header] = candidate_classes

def get_class_properties(table):
    """ Function to find all properties of all column classes
        Later used for inference
    """
    ne = table.get_NE_cols()

    #column and cell annotation
    for column in ne.columns:
        for clazz in data[column.header]:
            if clazz not in class_property_matrix:
                class_property_matrix[clazz] = set()
           
            properties = get_all_properties_by_class(clazz)

            if properties is not None:
                for p in properties:
                    prop = p["property"]["value"]
                    
                    if prop.find("http://dbpedia.org/ontology") == -1:
                            continue

                    class_property_matrix[clazz].add(prop)

def get_instance_properties(table):
    """ Function gets all possible properties for every entity candidate (usually 1)
        Append it to the column candidate classes
    """
    ne = table.get_NE_cols()
    #column and cell annotation
    for column in ne.columns:
        candidate_classes = data[column.header]

        for cell in tqdm(column.cells):
            for concept in cell.predicted_labels:
                instance = concept[0]

                if instance is None:
                    continue
                    
                if instance not in instance_property_matrix:
                    instance_property_matrix[instance] = set()

                if instance not in class_property_by_instance_matrix:
                    class_property_by_instance_matrix[instance] = set()

                #this one find the properties that are candidates for the column
                #finds column property candidate space
                properties = get_all_property_relations_by_instance(instance)
                if properties is not None:
                    for p in properties:
                        prop = p["property"]["value"]

                        if prop.find("http://dbpedia.org/ontology") == -1:
                            continue
                        
                        instance_property_matrix[instance].add(prop)
                
                #this one find the properties suggested to the belonging class
                #properties of the instance
                properties = get_all_instance_properties(instance)
                if properties is not None:
                    for p in properties:
                        prop = p["property"]["value"]

                        if prop.find("http://dbpedia.org/ontology") == -1:
                            continue
                        
                        class_property_by_instance_matrix[instance].add(prop)
        
        data[column.header] = candidate_classes

def calcualte_probability_score(graph, cand1, cand2):
    """Function takes in the candidate space graph and
       calculate the probabilities accoridngly
    """
    delta = 0.0000001
    if cand1.type == "class" and cand2.type == "class":
        return delta
    elif cand1.type == "class" and cand2.type == "instance":
        #first check if cand1 and cand2 are related
        if graph.has_edge(cand1.id, cand2.id):
            #find ambiguity score
            ambiguity = graph.degree(cand1.id)
            return 1.0/ambiguity
        else:
            return delta
    elif cand1.type == "property" and cand2.type == "instance":
        #first check if cand1 and cand2 are related
        if graph.has_edge(cand1.id, cand2.id):
            print 1.0
            return 1.0
        else:
            return delta

    
    return delta
        
def algo(table):
    find_cell_and_header_entities(table)
    get_class_properties(table)
    get_instance_properties(table)

    pp = pprint.PrettyPrinter(depth=6)
    # pp.pprint(entities)

    #putting all in a graph for easier inference
    graph = nx.Graph()

    #first we create a set of Entity instances
    entities = dict()
    for (instance, obj) in instance_class_matrix.items():
        i_id = "dbr:" + instance.replace("http://dbpedia.org/resource/", "")
        if instance not in entities:
            entity = Entity(i_id, "instance")
            entities[i_id] = entity
            graph.add_node(i_id, node_color="blue")
        
        for clazz in obj:
            c_id = "dbo:" + clazz.replace("http://dbpedia.org/ontology/", "")
            if clazz not in entities:
                entity = Entity(c_id, "class")
                entities[c_id] = entity
                graph.add_node(c_id)

            graph.add_edge(i_id, c_id)
    

    # intance property intersection
    # here we intersect the properties suggested to the column
    # it combines to be the property space of the column
    ne = table.get_NE_cols()
    for column in ne.columns:
        candidate_classes = data[column.header]
        column_property_space = None
        class_property_space = None

        for cell in column.cells:
            for concept in cell.predicted_labels:
                instance = concept[0]

                #intersecting the suggested column property space
                if instance in instance_property_matrix:
                    if column_property_space is None:
                        column_property_space = instance_property_matrix[instance]
                    else:
                        column_property_space.intersection(instance_property_matrix[instance])
                
                if instance in class_property_by_instance_matrix:
                    if class_property_space is None:
                        class_property_space = class_property_by_instance_matrix[instance]
                    else:
                        class_property_space.intersection(class_property_by_instance_matrix[instance])

        #now column_property_space contains the possible properties that
        #the column could take, ie: capital, country
        #we just add it to the graph
        for prop in column_property_space:
            if prop not in candidate_classes:
                candidate_classes[prop] = {
                    "type": "property",
                    "count": 0
                }
            p_id = "dbp:" + prop.replace("http://dbpedia.org/ontology/", "")
            if prop not in entities:
                entity = Entity(p_id, "property")
                entities[p_id] = entity
                graph.add_node(p_id)

            for cell in column.cells:
                for concept in cell.predicted_labels:
                    instance = concept[0]

                    i_id = "dbr:" + instance.replace("http://dbpedia.org/resource/", "")
                    graph.add_edge(i_id, p_id)


        

        #the class_property_space contains properties suggested by
        #instances as properties of the column class
        #ex: for Country class, capital property is suggested
        #we need to add this set to each of the column classes
        #first we add them to the graph
        for prop in class_property_space:   
            p_id = "dbp:" + prop.replace("http://dbpedia.org/ontology/", "")         
            if prop not in entities:
                entity = Entity(p_id, "property")
                entities[p_id] = entity
                graph.add_node(p_id)
        
        #now we extend the candidate class's property set to
        #include those given by the class_propert_space
        for candidate in candidate_classes:
            if candidate_classes[candidate]["type"] == "class":
                # if candidate not in class_property_matrix:
                #     class_property_matrix[candidate] = set()
                # class_property_matrix[candidate].union(class_property_space)
                class_property_matrix[candidate] = class_property_space
    
    #now we add the class-properties to the graph
    for (clazz, prop_set) in class_property_matrix.items():
        c_id = "dbo:" + clazz.replace("http://dbpedia.org/ontology/", "")

        for prop in prop_set:
            p_id = "dbp:" + prop.replace("http://dbpedia.org/ontology/", "")
            if prop not in entities:
                entity = Entity(p_id, "property")
                entities[p_id] = entity
                graph.add_node(p_id)

            graph.add_edge(c_id, p_id)

    graph.remove_nodes_from(nx.isolates(graph))
    

    
    mapping = {
        "class": "blue",
        "instance": "green",
        "col_property": "red",
        "clz_property": "yellow"
    }
    node_color = map(lambda node: mapping[entities[node].type],graph.nodes())
    nx.draw(graph, with_labels=True, node_color=node_color)
    plt.show()
    
    #now we take a deep breath and start to put all this shit into the 
    #markov model
    #we first imagine the factor graph
    markov_net = FactorGraph(silent=True)
    
    for c in range(len(ne.columns)):
        column = ne.columns[c]
        #name columns as : C_1, C_2
        column_name = "C_%d" % c
        column_candidates = data[column.header].items()
        column_card = len(column_candidates)
        var1 = Variable(column_name, column_card)

        for r in range(len(column.cells)):
            cell = column.cells[r]
            #name cells as : D_1_1, D_2_1
            cell_name = "D_%d_%d" % (r, c)
            cell_candidates = cell.predicted_labels
            cell_card = len(cell_candidates)
            var2 = Variable(cell_name, cell_card)

            #for each pair of column-cell, create a factor now
            #needs to hold transition matrix of |col|x|cell|
            #usually it would be nx1
            mat = np.zeros([column_card, cell_card])

            #now using the graph, calculate the probabilities
            #CAREFULLY
            for i in range(column_card):
                col_candidate = column_candidates[i][0]

                if column_candidates[i][1]["type"] == "class":
                    col_id =  "dbo:" + col_candidate.replace("http://dbpedia.org/ontology/", "")
                else:
                    col_id =  "dbp:" + col_candidate.replace("http://dbpedia.org/ontology/", "")

                col_entity = entities[col_id]

                for j in range(cell_card):
                    cell_candidate = cell_candidates[j][0]
                    cell_id = "dbr:" + cell_candidate.replace("http://dbpedia.org/resource/", "")
                    cell_entity = entities[cell_id]

                    score = calcualte_probability_score(graph, col_entity, cell_entity)

                    mat[i][j] = score
            
            print mat





    

    