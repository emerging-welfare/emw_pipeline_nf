git pull origin master
nohup python3 /emw_pipeline_nf/bin/classifier/classifier_flask.py 2> /dev/null &
nohup python3 /emw_pipeline_nf/bin/sent_classifier/classifier_flask.py 2> /dev/null &
nohup python3 /emw_pipeline_nf/bin/trigger_classifier/classifier_flask.py 2> /dev/null &
nohup python3 /emw_pipeline_nf/bin/neuroner/neuroner_flask.py 2> /dev/null &
export PYTHONPATH=/emw_pipeline_nf/bin
nextflow run emw_pipeline.nf
