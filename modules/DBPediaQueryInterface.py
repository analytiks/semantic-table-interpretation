from SPARQLWrapper import SPARQLWrapper, JSON


def execute_sparql_query(query):
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.addDefaultGraph("http://dbpedia.org")
    sparql.setReturnFormat(JSON)
    sparql.setQuery(query)

    return sparql.query().convert()["results"]["bindings"]


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


def get_exact_label_match(value):
    query = """
            SELECT DISTINCT ?uri ?label
            WHERE {
                ?uri rdfs:label ?label .
                FILTER (?label='""" + value + """'@en)
            }
            """
    result = execute_sparql_query(query)

    return result[0] if result else None


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
