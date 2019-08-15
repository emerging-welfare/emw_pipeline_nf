path_to_repo=$1
export PYTHONPATH="$path_to_repo/bin"
screen -dm python3 $path_to_repo/bin/classifier/classifier_batch_flask.py
screen -dm python3 $path_to_repo/bin/sent_classifier/classifier_flask.py
screen -dm python3 $path_to_repo/bin/token_classifier/classifier_batch_flask.py
sleep 60
./nextflow run emw_pipeline.nf
