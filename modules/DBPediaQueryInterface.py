from SPARQLWrapper import SPARQLWrapper, JSON
import cache
import json

'''
Todo:
    1. Using pagerank for dbpedia
    2. For one word regex, sort by lesser string length first
    3. For more than one word, find the concepts that are common to all
'''

def execute_sparql_query(query):
    #first try the cache
    result = cache.get(query)
    if result is not None:
        return result

    #if no result in cache
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    # sparql = SPARQLWrapper("http://35.196.96.177:8890/sparql")
    sparql.addDefaultGraph("http://dbpedia.org")
    sparql.setReturnFormat(JSON)
    sparql.setQuery(query)
    result = sparql.query().convert()["results"]["bindings"]

    cache.put(query, result)

    return result


def get_class_of_instance(instance):
    query = """
            SELECT DISTINCT ?type
            WHERE{
                dbr:""" + instance + """ a ?type .
                FILTER not exists {
                    ?subtype ^a dbr:""" + instance + """;
                    rdfs:subClassOf ?type .
                }
            }
            """
    return execute_sparql_query(query)

'''
PREFIX vrank:<http://purl.org/voc/vrank#>           

 SELECT DISTINCT ?uri ?label ?v
FROM <http://dbpedia.org> 
FROM <http://people.aifb.kit.edu/ath/#DBpedia_PageRank> 
            WHERE {
                ?uri rdfs:label ?label .
?uri vrank:hasRank/vrank:rankValue ?v.
                FILTER (?label='London'@en)
            }
'''
def get_exact_label_match(value):
    query = """
            SELECT DISTINCT ?uri ?label ?type
            WHERE {
                ?uri rdfs:label ?label .
                ?uri rdf:type ?type .
                FILTER (?label="%s"@en)
            }
            """% value
    result = execute_sparql_query(query)

    return result if result else None


def get_included_labels(value):
    query = """
            SELECT ?uri ?label ?type
            WHERE {
                ?uri rdfs:label ?label .
                ?uri <http://dbpedia.org/ontology/type> ?type .
                FILTER regex(str(?label), '""" + value + """') .
                FILTER (lang(?label) = "en")
            }
            limit 10
            """

    return execute_sparql_query(query)
