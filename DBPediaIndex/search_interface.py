from urllib2 import *
import simplejson
import pprint

def search_entity(keyword):

    if(keyword is not None):

        query = 'http://localhost:8983/solr/dbpedia/select?q=all_data:{}&wt=json'.format(keyword)
        connection = urlopen(query)
        
        response = simplejson.load(connection)
        return response

if __name__ == "__main__":
    
    response = search_entity("island")
    for document in response['response']['docs']:
            pprint.pprint(document) 



