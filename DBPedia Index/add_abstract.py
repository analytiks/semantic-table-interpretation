
import pandas as pd 
from SPARQLWrapper import SPARQLWrapper, JSON
import glob
import urllib
import cache

import traceback

def execute_sparql_query(query):

	#first try the cache
	result = cache.get(query)
	if result is not None:
		return result

	sparql = SPARQLWrapper("http://dbpedia.org/sparql")
	sparql.addDefaultGraph("http://dbpedia.org")
	sparql.setReturnFormat(JSON)
	sparql.setQuery(query)

	result = sparql.query().convert()["results"]["bindings"]
	cache.put(query, result)
	return result


def build_query(uri):

	query = "SELECT * WHERE {<%s> <http://dbpedia.org/ontology/abstract> ?abstract}" % uri
	return query


def read_lines():

	path_list = glob.glob('/home/lahiru/fyp/DBPediaIndex/subset/out/*.csv')
	
	for file_path in path_list:
		new_file_name = "1-"+file_path.split("/")[-1]
		with open(new_file_name, 'w') as f1:
				f1.write('uri,name,abstract\n')

		with open(file_path, 'r') as ff:
			next(ff)
			for line in ff:
				temp_vals = line.split(",")
				uri = temp_vals[0]
				name = temp_vals[1]
				if(uri[0]=='"'):
					uri = uri[1:]
				if(uri[-2]=='"'):
					uri = uri[:-2]
				print uri
				new_line = uri + "," + name + ","
				uri = urllib.unquote(uri).decode('utf8')
				query = build_query(uri)
				abstracts = []
				try:
					abstracts = execute_sparql_query(query)
				except Exception as e:
					print "query error!"
					traceback.print_exc()
				else:
					try:
						content = ""
						for a in abstracts:
								val = urllib.unquote(a['abstract']['value']).encode('utf8')
								content = content + val
						new_line = new_line + content

					except Exception as e:
						print e
				with open(new_file_name, 'a') as f2:
					f2.write(new_line)
					f2.write('\n')


if __name__ == "__main__":
	read_lines()