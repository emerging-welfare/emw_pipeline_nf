export path_to_repo="$HOME/emw_pipeline_nf"
export PYTHONPATH="$path_to_repo/bin"
screen -dm $HOME/anaconda3/envs/py36/bin/python  $path_to_repo/bin/classifier/classifier_batch_flask.py
screen -dm $HOME/anaconda3/envs/py36/bin/python  $path_to_repo/bin/sent_classifier/classifier_flask.py
screen -dm $HOME/anaconda3/envs/py36/bin/python  $path_to_repo/bin/token_classifier/classifier_batch_flask.py
screen -dm $HOME/anaconda3/envs/py36/bin/python  $path_to_repo/bin/violent_classifier/classifier_flask.py
#sleep 60
#./nextflow run emw_pipeline.nf
