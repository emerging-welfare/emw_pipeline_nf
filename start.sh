# ******** PREPERATION ********
echo "Reading config...." >&2
source nextflow.conf

export PYTHONPATH="$prefix/bin"

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
    "input":"'"$input$files_start_with"'",
    "files_start_with":"'"$files_start_with"'",
    "outdir":"'"$output"'",
    "source_lang":"'"$source_lang"'",
    "source":"'"$source"'",
    "doc_batchsize":'$doc_batchsize',
    "token_batchsize":'$token_batchsize',
    "prefix":"'"$prefix"'",
    "extractor_script_path":"'"$extractor_script_path"'",
    "cascaded":'$cascaded',
    "classifier_first":'$classifier_first',
    "sent_batchsize":'$sent_batchsize',
    "RUN_DOC":'$RUN_DOC',
    "RUN_SENT":'$RUN_SENT',
    "RUN_TOK":'$RUN_TOK',
    "RUN_POST":'$RUN_POST'
}' > params.json

cat params.json
sleep 1

# TODO : think about resume
# TODO : sleep after screens or think of something else
# TODO : add "all" to gpu_number variables
# TODO : Where to delete work and .nextflow ?
# TODO : sent level task paralellism
# TODO : In current version, all sentences go through semantic stuff. Should only the positive sentences go through them? If yes, how?
# TODO : we give list of filenames to classifier_batch and token_classifier_batch, but they handle it differently. Why is this the case?
# TODO : give screens names
# TODO : In post, change integer labels to actual ones using label lists.
# TODO : Maybe we can group sentences by "filename" when passing through a channel.

doc_finished=false
sent_finished=false
tok_finished=false

# TODO : Find a better regex, do it in one sed
# TODO : ignoring filenames with "'" character. How do we fix this?
# If RUN_DOC is true, this file will be empt
rm "$output"positive_filenames.txt # clear out previous run's file if there is any
echo "filename" >> "$output"positive_filenames.txt
find $input -type f -name "*.json" | grep -v "'" | xargs grep '"doc_label": 1' | sed -r "s/^([^\{]+)\{.*$/\1/g" | sed -r "s/^.*\/([^\/]+):$/\1/g" >> "$output"positive_filenames.txt

# ******** RUNNING PIPELINE ********
if [ "$RUN_DOC" = true ] ; then
    echo "******** DOCUMENT LEVEL ********"
    screen -dm python $prefix/bin/classifier/classifier_batch_flask.py --gpu_number $gpu_classifier --batch_size $doc_batchsize
    screen -dm python $prefix/bin/violent_classifier/classifier_flask.py
    sleep 30
    nextflow doc_level.nf -params-file params.json && killall screen &&  doc_finished=true ;
    if [ "$doc_finished" = false ] ; then
	echo "Error occured during Document level. Aborting pipeline!"
	exit 1
    fi
    rm "$output"positive_filenames.txt
    echo "filename" >> "$output"positive_filenames.txt
    find $output -type f -name "*.json" | grep -v "'" | xargs grep '"doc_label": 1' | sed -r "s/^([^\{]+)\{.*$/\1/g" | sed -r "s/^.*\/([^\/]+):$/\1/g" >> "$output"positive_filenames.txt
fi

if [ "$RUN_SENT" = true ] ; then
    echo "******** SENTENCE LEVEL ********"
    screen -dm python  $prefix/bin/sent_classifier/classifier_flask.py --gpu_number_protest $gpu_number_protest --gpu_number_tsc $gpu_number_tsc --gpu_number_psc $gpu_number_psc --gpu_number_osc $gpu_number_osc
    sleep 90
    nextflow sent_level.nf -params-file params.json && killall screen &&  sent_finished=true ;
    if [ "$sent_finished" = false ] ; then
	echo "Error occured during Sentence level. Aborting pipeline!"
	exit 2
    fi
fi

if [ "$RUN_TOK" = true ] ; then
    echo "******** TOKEN LEVEL ********"
    screen -dm python $prefix/bin/token_classifier/classifier_batch_flask.py --gpu_number $gpu_token
    sleep 30
    nextflow tok_level.nf -params-file params.json && killall screen &&  tok_finished=true ;
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
    # TODO : Make sure to check if this add newlines between jsons. Also handle filenames containing "'".
    find jsons -type f | grep -v "'" | xargs cat >> output_combined_jsons.json
fi

#find jsons -type f | grep -v "'" | xargs cat >> $out_name_output_file.jsons.json && find work -mindepth 1 -type d | xargs -I {} rm -rf {}

find work -mindepth 1 -type d | xargs -I {} rm -rf {} && rm -r work
rm -rf .nextflow*
