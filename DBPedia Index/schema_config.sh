#!/usr/bin/env bash

curl -X POST -H 'Content-type:application/json' --data-binary '{
  "add-field":{
     "name":"url",
     "indexed":false,
     "type":"string",
     "stored":true }
}' http://localhost:8983/solr/dbpedia/schema


curl -X POST -H 'Content-type:application/json' --data-binary '{
  "add-field":{
     "name":"name",
     "indexed":false,
     "type":"string",
     "stored":true }
}' http://localhost:8983/solr/dbpedia/schema


curl -X POST -H 'Content-type:application/json' --data-binary '{
  "add-field":{
     "name":"abstract",
     "indexed":false,
     "type":"string",
     "stored":true }
}' http://localhost:8983/solr/dbpedia/schema


curl -X POST -H 'Content-type:application/json' --data-binary '{
  "add-field":{
     "name":"all_data",
     "indexed":true,
     "type":"text_general",
     "stored":false,
     "multiValued":true }
}' http://localhost:8983/solr/dbpedia/schema


curl -X POST -H 'Content-type:application/json' --data-binary '{
  "add-copy-field":{
     "source":"name",
     "dest":"all_data"}
}' http://localhost:8983/solr/dbpedia/schema


curl -X POST -H 'Content-type:application/json' --data-binary '{
  "add-copy-field":{
     "source":"abstract",
     "dest":"all_data"}
}' http://localhost:8983/solr/dbpedia/schema
