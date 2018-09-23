from table import Table
from modules.DBPediaQueryInterface import get_exact_label_match, get_relationship_and_class, get_relationship_and_sub_classes
import re
import itertools
import logging
from tqdm import tqdm
import coloredlogs
import pprint

coloredlogs.install()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("algo-basic")

def get_common_cases(val):
    cases = list()
    cases.append(val.upper())
    cases.append(val.lower())
    cases.append(val.title())
    return cases

def process_candidates(candidate_space, concepts, is_header=False):
    for concept in concepts:
        if is_header:
            candidate = concept["uri"]["value"]
        else:
            candidate = concept["type"]["value"].encode("utf-8")
       
        if candidate.find("http://dbpedia.org/ontology") == -1:
            continue

        if candidate not in candidate_space:
            candidate_space[candidate] = 0
        candidate_space[candidate] += 1

def merge_lists(list1, list2):
    merger = dict()
    
    for ele in list1+list2:
        if ele[0] not in merger:
            merger[ele[0]] = 0
        
        merger[ele[0]] += 1
    
    return [(k,v) for k, v in merger.items()]

def merge_column_candidates(pair_candidates, instance_candidates):
    merged_cadidates = {}

    for c1 in pair_candidates:
        for c2 in instance_candidates:
            if c1 == c2[0]:
                merged_cadidates[c1] = pair_candidates[c1]
    
    return merged_cadidates

def process_header(header_val):
    header_val = " ".join(header_val.split()).strip()
    logger.info("Processing header: %s" % header_val)

    for val in get_common_cases(header_val):
        results = get_exact_label_match(val)
        concepts = set()
        if results is not None and len(results) > 0:
            for result in results:
                candidate = result["uri"]["value"]

                if candidate.find("http://dbpedia.org/ontology") > -1:
                    concepts.add(candidate)

            return concepts
    
    return []

def algo(table):
    ne = table.get_NE_cols()

    #column and cell annotation
    for column in table.columns:
        candidate_classes = dict()

        column.header = " ".join(column.header.split()).strip()
        logger.info("Processing header: %s" % column.header)
        for val in get_common_cases(column.header):
            concept = get_exact_label_match(val)
            if concept is not None and len(concept) > 0:
                process_candidates(candidate_classes, concept, True)
                break
        
        if not column.NE_col:
            continue

        for cell in tqdm(column.cells):
            value = " ".join(cell.value.split()).strip()
            value_perms =  get_common_cases(value)

            # logger.info("Processing cell: %s" % value)
            for perm in value_perms:
                concept = get_exact_label_match(perm)
                if concept is not None and len(concept) > 0:
                    # logger.info("--candidate found!")
                    process_candidates(candidate_classes, concept)
                    cell.predicted_labels = [(concept[0]['uri']['value'],0)]
                    # print cell.predicted_labels
                    break      

        #annotate column based on the majority cote
        column.predicted_labels = sorted(candidate_classes.items(), key=lambda (k, v): v, reverse=True)

    column_matrix = [dict() for column in table.columns]
    #try to suggest columns for other classes by using value pairs
    for i, column in enumerate(ne.columns): 

        for j, target_column in enumerate(ne.columns):
            if i == j:
                continue

            # for select column pair, find properties by sampling 
            # the rows
            iterations = 0
            for k, cell in tqdm(enumerate(column.cells)):
                if iterations == 100:
                    continue
                
                iterations += 1

                target_cell = target_column.cells[k]

                if cell.predicted_labels is not None and \
                    target_cell.predicted_labels is not None and \
                    len(cell.predicted_labels) > 0 and \
                    len(target_cell.predicted_labels) > 0 :

                    print(cell.predicted_labels)
                    
                    result = get_relationship_and_sub_classes(target_cell.predicted_labels[0][0], 
                                                        cell.predicted_labels[0][0])
                    print(result)
                    if result is None:
                        continue
                    
                    if len(result) == 0:
                        continue

                    candidates = [{
                        "class": result[0]['class']['value'],
                        "property": result[0]['property']['value']
                    }]
                    for r in result:
                        candidates.append({
                            "class": r['subclass']['value'],
                            "property": r['property']['value']
                        })
                    
                    for candidate in candidates:                   
                        clazz = candidate["class"]
                        prop = candidate["property"]

                        if clazz not in column_matrix[i]:
                            column_matrix[i][clazz] = {
                                "type": "class",
                                "instance_score": 1,
                                "relations": {
                                    j: { 
                                        prop: 1
                                    }
                                }
                            }
                        else:
                            column_matrix[i][clazz]["instance_score"] += 1

                            if prop not in column_matrix[i][clazz]["relations"][j]:
                                column_matrix[i][clazz]["relations"][j][prop] = 0
                            column_matrix[i][clazz]["relations"][j][prop] += 1
                    
                    # print candidates
                    
    for i, column in enumerate(ne.columns): 
        column_matrix[i] = merge_column_candidates(column_matrix[i], column.predicted_labels)
        column_matrix[i] = sorted(column_matrix[i].items(), key=lambda (k, v): v["instance_score"], reverse=True)
        print process_header(column.header)

    print column_matrix
            

    return table
    