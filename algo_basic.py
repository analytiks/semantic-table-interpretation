from table import Table
from modules.DBPediaQueryInterface import get_exact_label_match
import re
import itertools
import logging
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("algo-basic")

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

        if candidate not in candidate_space:
            candidate_space[candidate] = 0
        candidate_space[candidate] += 1
    
    return cell_label

def algo(table):
    ne = table.get_NE_cols()

    nomatch = 0
    #column and cell annotation
    for column in ne.columns:
        candidate_classes = dict()

        logger.info("Processing header: %s" % column.header)
        for val in get_common_cases(column.header):
            concept = get_exact_label_match(val)
            if concept is not None and len(concept) > 0:
                process_candidates(candidate_classes, concept, True)
                break

        for cell in tqdm(column.cells):
            value = " ".join(cell.value.split()).strip()
            value_perms =  get_common_cases(value)

            # logger.info("Processing cell: %s" % value)
            for perm in value_perms:
                concept = get_exact_label_match(perm)
                if concept is not None and len(concept) > 0:
                    # logger.info("--candidate found!")
                    cell.predicted_labels = [process_candidates(candidate_classes, concept), 0]
                    print cell.predicted_labels
                    break    
            else:
                nomatch += 1  
     

        #annotate column based on the majority cote
        column.predicted_labels = sorted(candidate_classes.items(), key=lambda (k, v): v, reverse=True)[0:5]
    print "NOMATCH", nomatch
    #subject column ID
    subject_col = None
    subject_col_thresh = 0.75

    for column in ne.columns:
        unique = column.get_cardinality()/float(len(column.cells))
        column.unique = unique

        if unique >= subject_col_thresh:
            if subject_col is None:
                subject_col = column
            else:
                if subject_col.unique < unique:
                    subject_col = column 

    if subject_col is not None:
        subject_col.is_subject_column = True

    return table
    