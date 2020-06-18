# USER INPUT
input_folder=$1

# OPTIONS
show_statistics=false # Whether to show statistics of the output
out_extension="json" # csv, json, xlsx etc.


cd $input_folder

# Merge all positive documents into a single json
if [ -f positive_filenames.txt ]; then
    cat positive_filenames.txt | xargs cat >> positive_docs.json # filenames with ' are ignored by cat, so we add the next line
    find . -type f -name "*'*.json" -print0 | xargs -0 grep 'doc_label": 1' | sed -r "s/^[^:]*://g" >> positive_docs.json
else
    find . -type f -name "*.json" -print0 | xargs -0 grep 'doc_label": 1' | sed -r "s/^[^:]*://g" >> positive_docs.json
fi

# TODO : fill in the rest
