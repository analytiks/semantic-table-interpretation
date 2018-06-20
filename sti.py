import sys
import modules.CSVParser as csvparser
import modules.DBPediaQueryInterface as dbpedia
import modules.ColumnAnotator as clmannotator


# table = csvparser.csv_to_df(sys.argv[1])
# print "column header annotations"
# clmannotator.annotate_column_headers(table)
# # print dbpedia.get_included_labels("car")
# print dbpedia.get_class_of_instance("Stephen_King")

print dbpedia.get_exact_label_match("tab")
