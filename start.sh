export path_to_repo="$HOME/emw_pipeline_nf"
export PYTHONPATH="$path_to_repo/bin" 

echo "Reading config...." >&2
source nextflow.conf

[ ! -d "$output" ] && mkdir -p "$output" # Check if directory exists in bash and if not create it

echo "document classifier gpus = $gpu_classifier
    Sentence classifier gpus= $gpu_number_protest
    Sentence trigger se gpu= $gpu_number_tsc
    Sentence participant sem gpu= $gpu_number_psc
    Sentence organizer sem gpu= $gpu_number_osc
    Token classifier gpus= $gpu_token 
    "
screen_number="$(screen -ls | wc -l )" # getting the screen running number  

#TODO, more specific control
if (( $screen_number == 7 )) ; then
    echo "flasks are already is running"
else
    echo "starting the flask models"
#    killall screen # 
    screen -dm python $path_to_repo/bin/classifier/classifier_batch_flask.py --gpu_number $gpu_classifier --batch_size $doc_batchsize
    screen -dm python  $path_to_repo/bin/sent_classifier/classifier_flask.py --gpu_number_protest $gpu_number_protest --gpu_number_tsc $gpu_number_tsc --gpu_number_psc $gpu_number_psc --gpu_number_osc $gpu_number_osc
    screen -dm python $path_to_repo/bin/token_classifier/classifier_batch_flask.py --gpu_number $gpu_token
    screen -dm python $path_to_repo/bin/violent_classifier/classifier_flask.py
    sleep 60
fi

#TODO: add seqential version

echo "input folder is =$input" >&2
echo "output folder is=$output">&2


echo "the config file is generated " 
echo ' {
      "input_dir":"'"$input"'",
      "input":"'"$input/$files_start_with"'",
      "outdir":"'"$output"'",
      "source_lang":"'"$source_lang"'",
      "source":"'"$source"'",
      "doc_batchsize":'$doc_batchsize',
      "token_batchsize":'$token_batchsize',
      "prefix":"'"$prefix"'",
      "extractor_script_path":"'"$extractor_script_path"'",
      "cascaded":'$cascaded',
      "classifier_first":'$classifier_first' 
   }' > params.json

cat params.json
sleep 3

pipeline_signal=false

echo "running the pipeline"
if [ "$resume" = true ] ; then 
        echo "nextflow emw_pipeline.nf -params-file params.json -resume "
        nextflow emw_pipeline.nf -params-file params.json -resume && killall screen &&  pipeline_signal=true ;
else
      echo "nextflow emw_pipeline.nf -params-file params.json "
      nextflow emw_pipeline.nf -params-file params.json && killall screen &&  pipeline_signal=true ;
fi

if $pipeline_signal; then 
echo "generating detailed output of the pipeline\n\n"

    if [ "$filter_unprotested_doc" = true ] ; then
        if [ "$filter_unprotested_sentence" = true ] ; then
            python $path_to_repo/bin/output_to_csv.py --output_type $out_output_type /
            --input_folder $output /
            --o $out_name_output_file/
            --filter_unprotested_doc /
            --filter_unprotested_sentence  --date_key $out_date_key
        else
            python $path_to_repo/bin/output_to_csv.py --output_type $out_output_type /
            --input_folder $output /
            --o $out_name_output_file/
            --filter_unprotested_doc  --date_key $out_date_key 
        fi
    else
        python $path_to_repo/bin/output_to_csv.py --output_type $out_output_type --input_folder $output  --o $out_name_output_file  --date_key  $out_date_key
    fi
    find jsons -type f | grep -v "'" | xargs cat >> output.jsons.json && find work -mindepth 1 -type d | xargs -I {} rm -rf {}
    #find jsons -type f | grep -v "'" | xargs cat >> $out_name_output_file.jsons.json && find work -mindepth 1 -type d | xargs -I {} rm -rf {}
    rm -rf .nextflow*

fi
