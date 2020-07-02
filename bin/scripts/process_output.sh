# exit when any command fails
set -e
trap 'last_command=$current_command; current_command=$BASH_COMMAND' DEBUG
trap 'echo "\"${last_command}\" command filed with exit code $?."' EXIT

# USER INPUT
# If folder -> This is the directory where all the jsons from pipeline output resides.
# If file -> This is the post-processed positive_docs.json
input_file_or_folder=$1
# a csv file with columns "url","date" (YYYY/MM/DD) and "place".
dates_and_places_file=${2:-""} # If not given, default is ""

# OPTIONS
out_filename="out_event_database.json" # Output json file
sentence_cascade=false # If true: Negative sentences' token labels are negative
place_folder="~/geonames/india/"

if [[ -d $input_file_or_folder ]]; then # If folder
    echo "Merging jsons files together"
    # !!!This method does not work if there is no newline after the first json line!!!
    # Merge all positive documents into a single json
    # if [[ -f $input_file_or_folder/positive_filenames.txt ]]; then
    # 	# +2 is to skip the header of positive_filenames.txt
    # 	tail -n +2 $input_file_or_folder/positive_filenames.txt |
    # 	    xargs -I{} cat $input_file_or_folder/{} > positive_docs.json
    # 	# filenames with ' are ignored by cat in previous line, so we add the next line
    # 	find $input_file_or_folder -type f -name "http*'*.json" -print0 |
    # 	    xargs -0 grep 'doc_label": 1' |
    # 	    sed -r "s/^[^\{]*//g" >> positive_docs.json
    # else
    # 	find $input_file_or_folder -type f -name "http*.json" -print0 |
    # 	    xargs -0 grep 'doc_label": 1' |
    # 	    sed -r "s/^[^\{]*//g" > positive_docs.json
    # fi
    find $input_file_or_folder -type f -name "http*.json" -print0 |
        xargs -0 grep 'doc_label": 1' |
        sed -r "s/^[^\{]*//g" > positive_docs.json

    echo "Merging finished"

    echo "Post-processing pipeline output"
    # Post-processing the pipeline output
    if [[ -f $dates_and_places_file ]]; then
	python pipeline_to_json.py -i positive_docs.json -o positive_docs2.json -d $dates_and_places_file
    else
	python pipeline_to_json.py -i positive_docs.json -o positive_docs2.json
    fi

    echo "Post-processing finished. Post-processed file's name : positive_docs.json (Keep this! Might be used later)"
    mv positive_docs2.json positive_docs.json
    input_file_or_folder="positive_docs.json" # NOTE : You can use this file later to feed into this script.
fi

# echo "Constructing the event database"
# python construct_event_database.py \
#        --input_file $input_file_or_folder \
#        --out_file $out_filename \
#        --place_folder $place_folder

echo "Script Finished!"
