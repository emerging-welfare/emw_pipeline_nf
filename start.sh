git pull origin master
export PYTHONPATH=/emw_pipeline_nf/bin
nohup python3 /emw_pipeline_nf/bin/classifier/classifier_flask.py 2> /dev/null &
nohup python3 /emw_pipeline_nf/bin/sent_classifier/classifier_flask.py 2> /dev/null &
nohup python3 /emw_pipeline_nf/bin/token_classifier/classifier_flask.py 2> /dev/null &
sleep 60
nextflow run emw_pipeline.nf
