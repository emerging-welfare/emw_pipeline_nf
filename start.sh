export path_to_repo="$HOME/emw_pipeline_nf"
export PYTHONPATH="$path_to_repo/bin"

echo "Reading config...." >&2
source nextflow.conf

[ ! -d "$output" ] && mkdir -p "$output" # Check if directory exists in bash and if not create it

echo "document classifier gpus = $gpu_classifier
    Sentence classifier gpus=$gpu_sentences
    Token classifier gpus=$gpu_token "
screen_number="$(screen -ls | wc -l )" # getting the screen running number  

#TODO, more specific control
if (( $screen_number == 7 )) ; then
    echo "flasks are already is running"
else
    echo "starting the flask models"
    killall screen # 
    screen -dm $HOME/anaconda3/envs/py36/bin/python  $path_to_repo/bin/classifier/classifier_batch_flask.py --gpu_number $gpu_classifier
    screen -dm $HOME/anaconda3/envs/py36/bin/python  $path_to_repo/bin/sent_classifier/classifier_flask.py --gpu_number $gpu_sentences
    screen -dm $HOME/anaconda3/envs/py36/bin/python  $path_to_repo/bin/token_classifier/classifier_batch_flask.py --gpu_number $gpu_token
    screen -dm $HOME/anaconda3/envs/py36/bin/python  $path_to_repo/bin/violent_classifier/classifier_flask.py
    sleep 60
fi


if [ "$all_components" = true ] ; then
    echo 'git checkout all_components!'
    # git checkout all_components
else
    echo 'git checkout hpc'
    # git checkout hpc 
fi

echo "input folder is =$input" >&2
echo "output folder is=$output">&2
#screen -dm $HOME/anaconda3/envs/py36/bin/python  $path_to_repo/bin/classifier/classifier_batch_flask.py --gpu_number 0-6
#screen -dm $HOME/anaconda3/envs/py36/bin/python  $path_to_repo/bin/sent_classifier/classifier_flask.py --gpu_number 6
#screen -dm $HOME/anaconda3/envs/py36/bin/python  $path_to_repo/bin/token_classifier/classifier_batch_flask.py --gpu_number 7
#screen -dm $HOME/anaconda3/envs/py36/bin/python  $path_to_repo/bin/violent_classifier/classifier_flask.py
#sleep 60
#nextflow run emw_pipeline.nf -resume  && find jsons -type f | grep -v "'" | xargs cat >> scmp.jsons.json && find work -mindepth 1 -type d | xargs -I {} rm -rf {}

echo "the config file is generated " 
echo ' {
      "input_dir":"'"$input"'",
      "input":"'"$input/$files_start_with"'",
      "outdir":"'"$output"'",
      "source_lang":"'"$source_lang"'",
      "source":"'"$source"'",
      "doc_batchsize":'$doc_batchsize',
      "token_batchsize":'$token_batchsize',
      "prefix":"'"$prefix"'"
   }' > params.json

cat params.json
echo "running the pipeline"

if [ "$resume" = true ] ; then 
        echo "nextflow emw_pipeline.nf -params-file params.json -resume "
        nextflow emw_pipeline.nf -params-file params.json -resume && find jsons -type f | grep -v "'" | xargs cat >> scmp.jsons.json && find work -mindepth 1 -type d | xargs -I {} rm -rf {}
else
      echo "nextflow emw_pipeline.nf -params-file params.json "
      nextflow emw_pipeline.nf -params-file params.json && find jsons -type f | grep -v "'" | xargs cat >> scmp.jsons.json && find work -mindepth 1 -type d | xargs -I {} rm -rf {}
fi


# nextflow emw_pipeline.nf -params-file params.json