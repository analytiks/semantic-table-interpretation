import pandas as pd
import DBPediaQueryInterface as dbpedia


def get_string_column_names(df):
    return df.select_dtypes(['object']).columns.values.tolist()


def annotate_column_headers(df):
    stringColumns = get_string_column_names(df)
    for (i, columnHeader) in enumerate(stringColumns):
        print dbpedia.get_exact_label_match(columnHeader)
