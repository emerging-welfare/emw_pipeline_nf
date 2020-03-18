# ******** PREPERATION ********
export path_to_repo="$HOME/emw_pipeline_nf"
export PYTHONPATH="$path_to_repo/bin"

echo "Reading config...." >&2
source nextflow.conf

 # Check if directory exists in bash and if not create it
[ ! -d "$output" ] && mkdir -p "$output"

echo "document classifier gpus = $gpu_classifier
    Sentence classifier gpus= $gpu_number_protest
    Sentence trigger se gpu= $gpu_number_tsc
    Sentence participant sem gpu= $gpu_number_psc
    Sentence organizer sem gpu= $gpu_number_osc
    Token classifier gpus= $gpu_token
    "

echo "input folder is =$input" >&2
echo "output folder is=$output">&2


echo "the config file is generated "
echo '{
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
    "sent_batchsize":'$sent_batchsize',
    "RUN_DOC":'$RUN_DOC',
    "RUN_SENT":'$RUN_SENT',
    "RUN_TOK":'$RUN_TOK',
    "RUN_POST":'$RUN_POST'
}' > params.json

cat params.json
sleep 1


# echo "starting the flask models"
# screen -dm python $path_to_repo/bin/classifier/classifier_batch_flask.py --gpu_number $gpu_classifier --batch_size $doc_batchsize
# screen -dm python  $path_to_repo/bin/sent_classifier/classifier_flask.py --gpu_number_protest $gpu_number_protest --gpu_number_tsc $gpu_number_tsc --gpu_number_psc $gpu_number_psc --gpu_number_osc $gpu_number_osc
# screen -dm python $path_to_repo/bin/token_classifier/classifier_batch_flask.py --gpu_number $gpu_token
# screen -dm python $path_to_repo/bin/violent_classifier/classifier_flask.py
# sleep 60


# TODO : think about resume
# TODO : sleep after screens or think of something else
# TODO : add "all" to gpu_number variables
# TODO : violent classifier
# TODO : Where to delete work and .nextflow ?
# TODO : sent level task paralellism
# TODO : Test tok level

doc_finished=false
sent_finished=false
tok_finished=false

# TODO : Find a better regex, do it in one sed
# If RUN_DOC is true, this file will be empt
echo "filename" >> "$output"positive_filenames.txt
find $input -type f -name "*.json" | grep -v "'" | xargs grep '"doc_label": 1' | sed -r "s/^([^\{]+)\{.*$/\1/g" | sed -r "s/^.*\/([^\/]+):$/\1/g" >> "$output"positive_filenames.txt

# ******** RUNNING PIPELINE ********
if [ "$RUN_DOC" = true ] ; then
    echo "******** DOCUMENT LEVEL ********"
    screen -dm python $path_to_repo/bin/classifier/classifier_batch_flask.py --gpu_number $gpu_classifier --batch_size $doc_batchsize
    sleep 30
    nextflow doc_level.nf -params-file params.json -resume && killall screen &&  doc_finished=true ;
    if [ "$doc_finished" = false ] ; then
	echo "Error occured during Document level. Aborting pipeline!"
	exit 1
    fi
    rm positive_filenames.txt
    echo "filename" >> "$output"positive_filenames.txt
    find $output -type f -name "*.json" | grep -v "'" | xargs grep '"doc_label": 1' | sed -r "s/^([^\{]+)\{.*$/\1/g" | sed -r "s/^.*\/([^\/]+):$/\1/g" >> "$output"positive_filenames.txt
fi

if [ "$RUN_SENT" = true ] ; then
    echo "******** SENTENCE LEVEL ********"
    screen -dm python  $path_to_repo/bin/sent_classifier/classifier_flask.py --gpu_number_protest $gpu_number_protest --gpu_number_tsc $gpu_number_tsc --gpu_number_psc $gpu_number_psc --gpu_number_osc $gpu_number_osc
    nextflow sent_level.nf -params-file params.json -resume && killall screen &&  sent_finished=true ;
    if [ "$sent_finished" = false ] ; then
	echo "Error occured during Sentence level. Aborting pipeline!"
	exit 2
    fi
fi

if [ "$RUN_TOK" = true ] ; then
    echo "******** TOKEN LEVEL ********"
    screen -dm python $path_to_repo/bin/token_classifier/classifier_batch_flask.py --gpu_number $gpu_token
    nextflow tok_level.nf -params-file params.json -resume && killall screen &&  tok_finished=true ;
    if [ "$tok_finished" = false ] ; then
	echo "Error occured during Token level. Aborting pipeline!"
	exit 3
    fi
fi

echo "******** ALL LEVELS COMPLETED ********"

if [ "$RUN_POST" = true ] ; then
    echo "******** RUNNING POSTPROCESSING ********"
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
    # TODO : Make sure to check if this add newlines between jsons. Also handle filenames containing "'".
    find jsons -type f | grep -v "'" | xargs cat >> output_combined_jsons.json
fi

#find jsons -type f | grep -v "'" | xargs cat >> $out_name_output_file.jsons.json && find work -mindepth 1 -type d | xargs -I {} rm -rf {}

find work -mindepth 1 -type d | xargs -I {} rm -rf {} && rm -r work
rm -rf .nextflow*
