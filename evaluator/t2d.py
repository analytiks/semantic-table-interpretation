"""T2D evaluator"""

from os import walk
from os.path import isfile, join, exists
import logging
from table import Table
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("evaluator-t2d")

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

    for table_file in filenames:
        has_column_annotated = True
        #check if the column annotator exist
        if not isfile(join(column_ann_dir, table_file)):
            logger.warn("Column annotator file not found for: %s" % table_file)
            has_column_annotated = False
        
        #parse the source table
        try:
            tb = Table()
            tb.parse_csv(join(data_dir, table_file))
            tb = algorithm(tb)

            print tb.columns[0].predicted_labels
            tb.visualize()
        except Exception as e:
            logger.error("Error parsing table: %s" % table_file)
            logger.error("Error message : %s" % e.message)
        
        break



        
