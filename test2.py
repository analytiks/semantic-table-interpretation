from evaluator import t2d
# from algo_basic import algo
# from algo_subcol import algo
from algo_final_v2 import algo

if __name__ == "__main__":
    # t2d.evaluate_t2d_complete("./dataset/t2d/table_all",
    #                       "./dataset/t2d/table_ann.csv",
    #                       "./dataset/t2d/table_column_ann",
    #                       algo)
    
    # t2d.evaluate_t2d_complete("./dataset/custom/ds",
    #                       "./dataset/t2d/table_ann.csv",
    #                       "./dataset/t2d/table_column_ann",
    #                       algo)
    
    t2d.evaluate_t2d_complete("./dataset/TAIPAN-Datasets-master/T2DStar/tables",
                          "./dataset/t2d/table_ann.csv",
                          "./dataset/t2d/table_column_ann",
                          algo)
    
    # t2d.evaluate_t2d_complete("./dataset/t2d/table_all",
    #                       "./dataset/t2d/table_ann.csv",
    #                       "./dataset/t2d/table_column_ann",
    #                       algo)

    # t2d.evaluate_t2d_complete("./dataset/t2d/table_all",
    #                       "./dataset/t2d/table_ann.csv",
    #                       "./dataset/t2d/table_column_ann",
    #                       algo)