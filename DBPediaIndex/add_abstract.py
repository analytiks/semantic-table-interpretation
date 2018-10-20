
from SPARQLWrapper import SPARQLWrapper, JSON
import glob
import urllib
import cache
import csv

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

	path_list = glob.glob('/home/lahiru/sti/DBPediaIndex/subset/*.csv')
	
	for file_path in path_list:
		new_file_name = "processed/	"+file_path.split("/")[-1]
		with open(new_file_name, 'w') as f1:
				f1.write('uri,name,abstract\n')
		with open(new_file_name, mode='a') as f2:
			writer = csv.writer(f2)

			with open(file_path, 'r') as ff:
				next(ff)
				reader = csv.reader(ff)
				for line in reader:
					temp_vals = line
					uri = temp_vals[0]
					name = temp_vals[1]
					if(uri[0]=='"'):
						uri = uri[1:]
					if(uri[-1]=='"'):
						uri = uri[:-1]
					if(uri[-2]=='"'):
						uri = uri[:-2]
					if(uri[-3]=='"'):
						uri = uri[:-3]
					print uri
					# new_line = uri + "," + name + ","
					new_line = []
					new_line.append(uri)
					new_line.append(name)
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
							# content = content + '"'
							new_line.append(content)
						except Exception as e:
							print e
					
					writer.writerow(new_line)
					


if __name__ == "__main__":
	read_lines()