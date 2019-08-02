export PYTHONPATH="/scratch/users/omutlu/emw_pipeline_nf/bin"
screen -dm python3 /scratch/users/omutlu/emw_pipeline_nf/bin/classifier/classifier_flask.py
screen -dm python3 /scratch/users/omutlu/emw_pipeline_nf/bin/sent_classifier/classifier_flask.py
screen -dm python3 /scratch/users/omutlu/emw_pipeline_nf/bin/token_classifier/classifier_batch_flask.py
sleep 60
./nextflow run emw_pipeline.nf
