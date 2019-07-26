# You need glove.6B.100d.txt in data/word_vectors folder
screen -dm python3 /scratch/users/omutlu/emw_pipeline_nf/bin/neuroner/neuroner_flask.py
export PYTHONPATH=/scratch/users/omutlu/emw_pipeline_nf/bin:$PYTHONPATH
screen -dm python3 /scratch/users/omutlu/emw_pipeline_nf/bin/classifier/classifier_flask.py
screen -dm python3 /scratch/users/omutlu/emw_pipeline_nf/bin/sent_classifier/classifier_flask.py
screen -dm python3 /scratch/users/omutlu/emw_pipeline_nf/bin/trigger_classifier/classifier_flask.py
sleep 60
./nextflow run emw_pipeline.nf
