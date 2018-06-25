from table import Table
from modules.DBPediaQueryInterface import get_exact_label_match, get_included_labels
import re
import itertools
import logging

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

# for perm in get_common_cases('London'):
#     print perm, get_exact_label_match(perm)

input_csv = "21337553_0_8832378999628437599.csv"
input_path = "./dataset/t2d/table_instance/" + input_csv

tb = Table()
tb.parse_csv(input_path)

ne = tb.get_NE_cols()
for column in ne.columns:
    candidate_classes = dict()

    logger.info("Processing header: %s" % column.header)
    for val in get_common_cases(column.header):
        concept = get_exact_label_match(val)
        if concept is not None and len(concept) > 0:
            process_candidates(candidate_classes, concept, True)
            break

    for cell in column.cells:
        value = " ".join(cell.value.split()).strip()
        value_perms =  get_common_cases(value)

        logger.info("Processing cell: %s" % value)
        for perm in value_perms:
            concept = get_exact_label_match(perm)
            if concept is not None and len(concept) > 0:
                logger.info("--candidate found!")
                process_candidates(candidate_classes, concept)
                break           
    
    print sorted(candidate_classes.items(), key=lambda (k, v): v, reverse=True)[0:5]
    