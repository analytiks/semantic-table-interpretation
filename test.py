from evaluator import t2d
from algo_basic import algo

if __name__ == "__main__":
    t2d.evaluate_t2d_complete("./dataset/t2d/table_all",
                          "./dataset/t2d/table_ann.csv",
                          "./dataset/t2d/table_column_ann",
                          algo)