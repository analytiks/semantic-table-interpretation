
============= Pre-processing Data ===================

Extract the t2D DBPedia subest here.

Remove any incomplete files in ./processed folder.

run "sudo docker-compose up" from root directory of the repo.

Run add_abstract.py from this directory


============= Creating Search Index ===================

Run Solr

Create a colection called "dbpedia"

run schma_config.sh to configure the schema.

Post the docuemnts in the processed folder.

