# # exit when any command fails
# set -e
# trap 'last_command=$current_command; current_command=$BASH_COMMAND' DEBUG
# trap 'echo "\"${last_command}\" command failed with exit code $?."' EXIT

# USER INPUT
# If folder -> This is the directory where all the jsons from pipeline output resides.
# If file -> This is the post-processed positive_docs.json
input_file_or_folder=$1
out_folder=$2 # The output folder
# a tsv file with columns "url","date" (YYYY/MM/DD) and "place".
dates_and_places_file=${3:-""} # If not given, default is ""

# OPTIONS
out_filename="database.json" # Output json file
target_country="argentina" # "india", "south_africa", brazil", "argentina"
# sentence_cascade=false # If true: Negative sentences' token labels are negative
place_folder="/home/omutlu/geocoding_dictionaries/$target_country/"
# place_folder="~/geocoding_dictionaries/india/"
internal="true" # If the database is for internal use only
debug="true" # If you want to debug/evaluate the database output
check_extracted_first="true" # When doing geocoding, whether to check for places in extracted places first, rather than html places
dist_has_locality="true"
batch_name="lanacion_2022-04-30"

if [[ -d $input_file_or_folder ]]; then # If folder
    echo "Merging jsons files together"
    # !!!This method does not work if there is no newline after the first json line!!!
    find $input_file_or_folder -type f -name "*.json" -print0 |
        xargs -0 grep 'doc_label": 1' |
        sed -r "s/^[^\{]*//g" > $out_folder/positive_docs.json

    echo "Merging finished"

    echo "Post-processing pipeline output"
    if [[ -f $dates_and_places_file ]]; then
	python pipeline_to_json.py -i $out_folder/positive_docs.json -o $out_folder/processed_positive_docs.json -d $dates_and_places_file
    else
	python pipeline_to_json.py -i $out_folder/positive_docs.json -o $out_folder/processed_positive_docs.json
    fi

    echo "Post-processing finished. Post-processed file's name : processed_positive_docs.json (Keep this! Might be used later)"
    # mv $out_folder/positive_docs2.json $out_folder/positive_docs.json
    input_file_or_folder="$out_folder/processed_positive_docs.json" # NOTE : You can use this file later to feed into this script.
fi

echo "Constructing the event database"
# delete old run's info files if any (others already overwrite existing files)
if [[ -f $out_folder/nothing_found.json ]]; then
    rm $out_folder/nothing_found.json $out_folder/only_state_found.json $out_folder/geopy_outs.txt
fi

python construct_event_database.py \
    --input_file $input_file_or_folder \
    --out_folder $out_folder \
    --out_filename $out_filename \
    --place_folder $place_folder \
    --internal $internal \
    --debug $debug \
    --target_country $target_country \
    --dist_has_locality $dist_has_locality \
    --batch_name $batch_name \
    --check_extracted_first $check_extracted_first > $out_folder/geocoding.log

echo -e "\n\nRun Options: \n  --debug=$debug\n  --internal=$internal\n  --check_extracted_first=$check_extracted_first\n  --target_country=$target_country\n  --dist_has_locality=$dist_has_locality" >> $out_folder/geocoding.log

echo "Script Finished!"
