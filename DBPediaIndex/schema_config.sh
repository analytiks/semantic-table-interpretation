#!/usr/bin/env bash

################## Create new type for all_data id needed ###############
# curl -X POST -H 'Content-type:application/json' --data-binary '{
#   "add-field-type" : {
#      "name":"myNewTxtField",
#      "class":"solr.TextField",
#      "positionIncrementGap":"100",
#      "analyzer" : {
#         "charFilters":[{
#            "class":"solr.PatternReplaceCharFilterFactory",
#            "replacement":"$1$1",
#            "pattern":"([a-zA-Z])\\\\1+" }],
#         "tokenizer":{
#            "class":"solr.WhitespaceTokenizerFactory" },
#         "filters":[{
#            "class":"solr.WordDelimiterFilterFactory",
#            "preserveOriginal":"0" }
#            ]
#       }
#     }
#   }' http://localhost:8983/solr/gettingstarted/schema

curl -X POST -H 'Content-type:application/json' --data-binary '{
  "add-field":{
     "name":"uri",
     "indexed":true,
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
