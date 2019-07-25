# You need glove.6B.100d.txt in data/word_vectors folder
export PYTHONPATH=$PYTHONPATH:/scratch/users/omutlu/emw_pipeline_nf/bin
nohup python3 /scratch/users/omutlu/emw_pipeline_nf/bin/classifier/classifier_flask.py 2> /dev/null &
nohup python3 /scratch/users/omutlu/emw_pipeline_nf/bin/sent_classifier/classifier_flask.py 2> /dev/null &
nohup python3 /scratch/users/omutlu/emw_pipeline_nf/bin/trigger_classifier/classifier_flask.py 2> /dev/null &
sleep 60
./nextflow run emw_pipeline.nf
