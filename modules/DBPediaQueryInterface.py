from SPARQLWrapper import SPARQLWrapper, JSON
import cache
import json
import nltk
from nltk.corpus import stopwords


'''
Todo:
    1. Using pagerank for dbpedia
    2. For one word regex, sort by lesser string length first
    3. For more than one word, find the concepts that are common to all
'''

def execute_sparql_query(query, cached=True):
    #first try the cache
    if cached:
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

    return result if result else None


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
    result = execute_sparql_query(query)

    return result

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
            """ % unicode(value, "utf-8")
    result = execute_sparql_query(query)

    return result


def lookup_regex(value):
    query = """
            SELECT DISTINCT ?uri ?label ?type
            WHERE {
                ?uri rdfs:label ?label .
                ?uri rdf:type ?type .
                FILTER (regex(?label, '%s','i')) .
                FILTER (lang(?label) = 'en')
            }
            order by strlen(str(?label))
            limit 10
            """ % value
    result = execute_sparql_query(query)

    return result


def lookup_without_stopwords(value):
    results = {}
    word_list = value.split(" ")
    filtered_words = [word for word in word_list if word not in stopwords.words('english')]
    for (i, word) in enumerate(filtered_words):
        result = get_exact_label_match(word)
        results[word] = result

    return results

def get_all_properties(class_uri):
    query = """
            SELECT DISTINCT ?property 
            WHERE {
                ?instance a <%s> . 
                ?instance ?property ?object . 
            }
            """ % class_uri
    result = execute_sparql_query(query)

    return result

def get_relationship(resource_uri_1, resource_uri_2):
    query = """
        SELECT DISTINCT ?property 
        WHERE {
            <%s> ?property <%s> . 
        }
        """% (resource_uri_1, resource_uri_2)
    result = execute_sparql_query(query)

    return result

def get_relationship_and_class(property_instance_uri, class_instance_uri):
    query = """
            select distinct ?class ?property where {
                ?instance ?property <%s> .
                ?property <http://www.w3.org/2000/01/rdf-schema#domain> ?class
                FILTER(?instance = <%s>)
            }
            """% (property_instance_uri, class_instance_uri)
    result = execute_sparql_query(query)

    return result

def get_relationship_and_sub_classes(property_instance_uri, class_instance_uri):
    query = """
            select distinct ?subclass ?class ?property where {
            ?instance ?property <%s> .
            ?property <http://www.w3.org/2000/01/rdf-schema#domain> ?class .
            ?subclass <http://www.w3.org/2000/01/rdf-schema#subClassOf> ?class.
            {
                        select distinct ?class ?property where {
                            ?instance ?property <%s> .
                            ?property <http://www.w3.org/2000/01/rdf-schema#domain> ?class
                            FILTER(?instance = <%s>)
                        }
            }
            FILTER(?instance = <%s>)
            }
            """% (property_instance_uri, property_instance_uri, class_instance_uri, class_instance_uri)
    result = execute_sparql_query(query)

    return result

def get_all_properties_by_class(class_uri):
    query = """
            select distinct ?property where{
            {
                ?property rdfs:domain ?class . 
                <%s> rdfs:subClassOf+ ?class.
                } UNION {
                ?property rdfs:domain <%s>.
                }
            }
            """% (class_uri, class_uri)
    result = execute_sparql_query(query)

    return result

def get_all_property_relations_by_instance(instance_uri):
    """ Given dbr:Colombo --> capital, city, birthPlace
    """
    query = """
            select distinct ?property STR(?label) where {
                ?obj ?property <%s> .
                ?property rdfs:label ?label.
                FILTER ( LANG(?label) = "en" )
            }
            """% (instance_uri)
    result = execute_sparql_query(query)
    return result

def get_all_instance_properties(instance_uri):
    """ Given dbr:Colombo --> country, area, province
    """
    query = """
            select distinct ?property STR(?label) where {
                <%s> ?property ?obj .
                ?property rdfs:label ?label.
                FILTER ( LANG(?label) = "en" )
            }
            """% (instance_uri)
    result = execute_sparql_query(query)
    return result

def get_parents(class_uri):
    query = """
            SELECT DISTINCT ?c WHERE {
                %s rdfs:subClassOf* ?c .
            } 
            """% (class_uri)
    result = execute_sparql_query(query)
    return result

'''

get all props by instance

select distinct ?property where {
    ?obj ?property dbr:Sri_Lanka
}

get all properties of a class

select distinct ?property where{
{
  ?property rdfs:domain ?class . 
  dbo:Country rdfs:subClassOf+ ?class.
} UNION {
  ?property rdfs:domain dbo:Country.
}}

get all properties of a resource
select distinct ?property ?label ?o {
  { dbr:Colombo ?property ?o }
  union
  { ?s ?property dbr:Colombo }

  optional { 
    ?property rdfs:label ?label .
    filter langMatches(lang(?label), 'en')
  }
}


select distinct ?property ?o {
  dbr:Colombo ?property dbr:Sri_Lanka

  { dbr:Colombo ?property ?o }
  union
  { ?s ?property dbr:Colombo }

 
}

'''
