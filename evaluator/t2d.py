"""T2D evaluator"""

from os import walk
from os.path import isfile, join, exists
import logging
from table import Table
import csv
import coloredlogs

coloredlogs.install()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("evaluator-t2d")

def get_metrics(tp, fp, fn):
    if tp == 0 and fp == 0:
        P = 0
    else:
        P = tp/float(tp+fp)*100
    
    if tp == 0 and fn == 0:
        R = 0
    else: 
        R = tp/float(tp+fn)*100

    if P == 0 and R == 0:
        F1 = 0
    else:
        F1 = 2*P*R/(P+R)

    return P, R, F1

def calculate_fp_fp_fn(table_entity_array):
    """ Function to caluculate the
        TP - True Positives
        FP - False Positive
        FN - False Negatives
        based on the true_label and predicted_labels
    """
    tp = 0
    fp = 0
    fn = 0

    for entity in table_entity_array:
        if entity.true_label is None:
            continue

        true = [entity.true_label]
        predicted = [c[0] for c in entity.predicted_labels]
        labels = set(true + predicted)
        
        for label in labels:
            if label in true:
                if label in predicted:
                    tp += 1
                else:
                    fn += 1
            else:
                fp += 1
    
    return tp, fp, fn


def evaluate_t2d_complete(data_dir, class_ann, column_ann_dir, algorithm):
    """ Function to evaluate T2D compelete dataset
        Args:
            data_dir        directory where the source tables exist
            class_ann       .csv file with table-class annotations
            column_ann_dir  directory where column-class annotation per file exist
            algorithm       a method object to call to annotated the table
    """

    if not exists(data_dir):
        logger.error("Data directory: %s does not exist")
        return None

    logger.info("Reading t2d complete data set")
    (_, _, filenames) = walk(data_dir).next()

    #check if the table ann exist
    if not isfile(class_ann):
        logger.error("Invalid table annotation file")
        return None

    #read the table_ann file to get table classes
    gs_tables = {}
    with open(class_ann, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            gs_tables[row[0].replace(".tar.gz", "")] = row[2]
    
    t_col_fp = 0
    t_col_fn = 0
    t_col_tp = 0

    t_tab_fp = 0
    t_tab_fn = 0
    t_tab_tp = 0
    
    for table_file in filenames:
        logger.info("Annotating : %s" % table_file)

        
        has_column_annotated = True
        has_table_annotated = True
        #check if the column annotator exist
        if not isfile(join(column_ann_dir, table_file)):
            logger.warn("Column annotator file not found for: %s" % table_file)
            has_column_annotated = False
            # continue
        
        #parse the source table
        try:
            tb = Table()
            tb.parse_csv(join(data_dir, table_file))

            #set actual table class
            table_name = table_file.replace(".csv", "")
            if table_name in gs_tables:
                tb.true_label = gs_tables[table_name]
            else:
                has_table_annotated = False

            tb = algorithm(tb)

            #find a subject column
            for column in tb.columns:
                if column.is_subject_column:
                    logger.info("Subject column found: %s" % column.header)
                    logger.info("Subject column candidates: %s" % column.predicted_labels)

                    if len(column.predicted_labels) == 0:
                        tb.predicted_labels = [("http://www.w3.org/2002/07/owl#Thing", 0)]
                    else:
                        tb.predicted_labels = column.predicted_labels
                        
                    column.predicted_labels = [("http://www.w3.org/2000/01/rdf-schema#label",0)]

                    break
            else:
                #if no subject column found by the algorithm
                #put empty list as the predicted labels
                tb.predicted_labels = []

            TP = 0
            FP = 0
            FN = 0

            #read the gold standard
            gs_columns = None
            if has_column_annotated:
                with open(join(column_ann_dir, table_file), 'r') as f:
                    reader = csv.reader(f)
                    gs_columns = list(reader)
                
                for row in gs_columns:
                    tb.columns[int(row[3])].true_label = row[0]
                
                #run evaluator for columns
                tp, fp, fn = calculate_fp_fp_fn(tb.columns)
                t_col_tp += tp
                t_col_fp += fp
                t_col_fn += fn
                # logger.info("COLUMN EVALUATION")
                # logger.info("TP: %d, FP: %d, FN: %d" % (tp,fp,fn))
                # logger.info("P: %f, R: %f, F1: %f" % get_metrics(tp, fp, fn))

            if has_table_annotated:
                #run evaluator for table
                logger.info("TABLE EVALUATION")
                tp, fp, fn = calculate_fp_fp_fn([tb])
                t_tab_tp += tp
                t_tab_fp += fp
                t_tab_fn += fn
                # logger.info("TP: %d, FP: %d, FN: %d" % (tp,fp,fn))
                # logger.info("P: %f, R: %f, F1: %f" % get_metrics(tp, fp, fn))

            
            tb.visualize()

            logger.info("COLUMN EVALUATION")
            logger.info("TOTAL: P: %f, R: %f, F1: %f" % get_metrics(t_col_tp, t_col_fp, t_col_fn))

            logger.info("TABLE EVALUATION")
            logger.info("TOTAL: P: %f, R: %f, F1: %f" % get_metrics(t_tab_tp, t_tab_fp, t_tab_fn))

        except Exception as e:
            logger.error("Error parsing table: %s" % table_file)
            logger.exception("Issue")
            # raw_input()
        
        # raw_input()
        # break



        
