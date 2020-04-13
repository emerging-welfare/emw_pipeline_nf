echo "Starting time"
date

echo "Reading config...." >&2
source nextflow.conf

export PYTHONPATH="$prefix/bin" 

[ ! -d "$output" ] && mkdir -p "$output" # Check if directory exists in bash and if not create it

echo "document classifier gpus = $gpu_classifier
    Sentence classifier gpus= $gpu_number_protest
    Sentence trigger se gpu= $gpu_number_tsc
    Sentence participant sem gpu= $gpu_number_psc
    Sentence organizer sem gpu= $gpu_number_osc
    Token classifier gpus= $gpu_token 
    Place classifier gpus= $gpu_number_place 
    "
screen_number="$(screen -ls | wc -l )" # getting the screen running number  

if ! screen -ls | grep -q doc; then
    screen -S doc -dm python $prefix/bin/classifier/classifier_batch_flask.py --gpu_number $gpu_classifier --batch_size $doc_batchsize
fi

if ! screen -ls | grep -q sent; then
    screen -S sent -dm python  $prefix/bin/sent_classifier/classifier_flask.py --gpu_number_protest $gpu_number_protest --gpu_number_tsc $gpu_number_tsc --gpu_number_psc $gpu_number_psc --gpu_number_osc $gpu_number_osc
fi

if ! screen -ls | grep -q tok; then
    screen -S tok -dm python $prefix/bin/token_classifier/classifier_batch_flask.py --gpu_number $gpu_token --gpu_number_place "$gpu_number_place"
fi

if ! screen -ls | grep -q violent; then
    screen -S violent -dm python $prefix/bin/violent_classifier/classifier_flask.py
fi

sleep 60 # TODO : If all screens were here already there is no need for this

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

pipeline_signal=false

if $pipeline_signal; then 
echo "generating detailed output of the pipeline\n\n"

    if [ "$filter_unprotested_doc" = true ] ; then
        if [ "$filter_unprotested_sentence" = true ] ; then
            python $prefix/bin/output_to_csv.py --output_type $out_output_type /
            --input_folder $output /
            --o $out_name_output_file/
            --filter_unprotested_doc /
            --filter_unprotested_sentence  --date_key $out_date_key
        else
            python $prefix/bin/output_to_csv.py --output_type $out_output_type /
            --input_folder $output /
            --o $out_name_output_file/
            --filter_unprotested_doc  --date_key $out_date_key 
        fi
    else
        python $prefix/bin/output_to_csv.py --output_type $out_output_type --input_folder $output  --o $out_name_output_file  --date_key  $out_date_key
    fi
    find jsons -type f | grep -v "'" | xargs cat >> output.jsons.json && find work -mindepth 1 -type d | xargs -I {} rm -rf {}
    #find jsons -type f | grep -v "'" | xargs cat >> $out_name_output_file.jsons.json && find work -mindepth 1 -type d | xargs -I {} rm -rf {}
    rm -rf .nextflow*

fi

echo "Ending time"
date
