import sys
import modules.CSVParser as csvparser
import modules.DBPediaQueryInterface as dbpedia
import modules.ColumnAnotator as clmannotator

# print dbpedia.lookup_without_stopwords("USA and China")
# print dbpedia.lookup_regex('China')
# print dbpedia.lookup_regex('China')
# print dbpedia.get_all_properties("http://dbpedia.org/ontology/Person")
# print dbpedia.get_relationship("http://dbpedia.org/resource/Peter_Gallagher", "http://dbpedia.org/resource/Sandy_Cohen")
# print dbpedia.get_relationship_and_class("http://dbpedia.org/resource/Peter_Gallagher", "http://dbpedia.org/resource/Sandy_Cohen")
print dbpedia.test()