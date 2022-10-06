echo "Starting time"
date

# ******** PREPERATION ********
echo "Reading config...." >&2
source nextflow.conf

export PYTHONPATH="$prefix/bin"

 # Check if directory exists in bash and if not create it
[ ! -d "$output" ] && mkdir -p "$output"

echo "
    Sentence trigger sem gpu= $gpu_number_tsc
    Sentence participant sem gpu= $gpu_number_psc
    Sentence organizer sem gpu= $gpu_number_osc
    Multi task classifier gpus= $gpu_multi_task
    "

echo "input folder is =$input" >&2
echo "output folder is=$output">&2


echo "the config file is generated "
echo '{
    "input_dir":"'"$input"'",
    "outdir":"'"$output"'",
    "prefix":"'"$prefix"'",
    "filename_wildcard":"'"$filename_wildcard"'",
    "doc_cascaded":'$doc_cascaded',
    "sent_cascaded":'$sent_cascaded',
    "source_lang":"'"$source_lang"'",
    "do_text_extraction": '$do_text_extraction',
    "extractor_script_path":"'"$extractor_script_path"'",
    "multi_task_batchsize":'$multi_task_batchsize',
    "doc_batchsize":'$doc_batchsize',
    "sent_batchsize":'$sent_batchsize',
    "RUN_MULTI_TASK":'$RUN_MULTI_TASK',
    "RUN_SENT":'$RUN_SENT',
    "RUN_DOC":'$RUN_DOC'
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

extraction_finished=false
multi_task_finished=false
doc_finished=false
sent_finished=false

# ******** RUNNING PIPELINE ********
# # TODO: Text extraction may not work atm. Revise it!
# if [ "$do_text_extraction" = true ] ; then
#     echo "******** TEXT EXTRACTION ********"
#     nextflow text_exraction.nf -params-file params.json && extraction_finished=true ;
#     if [ "$extraction_finished" = false ] ; then
# 	echo "Error occured during text extraction. Aborting pipeline!"
# 	exit 3
#     fi
# fi

process_folder=$input
if [ "$RUN_MULTI_TASK" = true ] ; then
    process_folder=$output
    echo "******** MULTI TASK ********"
    if ! screen -ls | grep -q multi_task; then
	screen -S multi_task -dm python $prefix/bin/multi_task_classifier/multi_task_classifier_batch_flask.py --gpu_number $gpu_multi_task
	sleep 30
    fi
    nextflow multi_task.nf -params-file params.json && killall screen &&  multi_task_finished=true ;
    if [ "$multi_task_finished" = false ] ; then
	echo "Error occured during Multi Task. Aborting pipeline!"
	exit 3
    fi
fi


rm "$process_folder"positive_filenames.txt # clean out previous run's file if there is any
# TODO : Find a better regex, do it in one sed
# TODO : Filenames with "'" char can be written in positive_filenames.txt. When reading this in sent_level.nf and tok_level.nf, does this cause problems?
find $process_folder -type f -name "*.json" -print0 | xargs -0 grep '"doc_label": 1' | sed -r "s/^([^\{]+)\{.*$/\1/g" | sed -r "s/^.*\/([^\/]+):$/\1/g" >> "$process_folder"positive_filenames.txt
# find $process_folder -type f -name "*.json" | grep -v "'" | xargs grep '"doc_label": 1' | sed -r "s/^([^\{]+)\{.*$/\1/g" | sed -r "s/^.*\/([^\/]+):$/\1/g" >> "$process_folder"positive_filenames.txt


# Run sentence level and flair
if [ "$RUN_SENT" = true ] ; then
    echo "******** SENTENCE LEVEL ********"
    if ! screen -ls | grep -q sent; then
	screen -S sent -dm python  $prefix/bin/sent_classifier/classifier_flask.py --gpu_number_tsc $gpu_number_tsc --gpu_number_psc $gpu_number_psc --gpu_number_osc $gpu_number_osc --language $source_lang
	sleep 90
    fi
    nextflow sent_level.nf -params-file params.json && killall screen &&  sent_finished=true ;
    if [ "$sent_finished" = false ] ; then
	echo "Error occured during Sentence level. Aborting pipeline!"
	exit 2
    fi
fi

if [ "$RUN_DOC" = true ] ; then
    echo "******** DOCUMENT LEVEL ********"
    if ! screen -ls | grep -q violent; then
	screen -S violent -dm python $prefix/bin/violent_classifier/classifier_flask.py
	sleep 30
    fi
    nextflow doc_level.nf -params-file params.json && killall screen &&  doc_finished=true ;
    if [ "$doc_finished" = false ] ; then
	echo "Error occured during Document level. Aborting pipeline!"
	exit 1
    fi
fi

echo "******** ALL LEVELS COMPLETED ********"

echo "Ending time"
date
