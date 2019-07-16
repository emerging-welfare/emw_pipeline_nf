# This is how it you would run these extraction and doc preprocessing scripts in bash
# You can easily convert these to nextflow instructions

### !!! Requirements are: For python3 -> "justext", "lxml", "fuzzywuzzy" , For python2 -> "boilerpipe", "goose" !!! ###
### !!! Need to add the path to bin folder to your PYTHONPATH env variable !!! ###

# These are given by you!!!
HTML_DIR="/asd/htmls"
OUTPUT_DIR="/asd/jsons/"
SOURCE_LANG="English"
SOURCE="timesofindia"

for filename in $HTML_DIR/http*; do
    if [[ $filename == *"timesofindia"* ]]; then
	python3 extract/justext_gettext.py --input_file $filename --out_dir $OUTPUT_DIR --source_lang $SOURCE_LANG
	python3 doc_preprocess/preprocess_timesofindia.py --input_file $filename --out_dir $OUTPUT_DIR
    elif [[ $filename == *"newindianexpress"* ]]; then
	python2 extract/goose_gettext.py --input_file $filename --out_dir $OUTPUT_DIR
	python3 doc_preprocess/preprocess_newindianexpress.py --input_file $filename --out_dir $OUTPUT_DIR
    elif [[ $filename == *"indianexpress"* ]]; then
	python2 extract/goose_gettext.py --input_file $filename --out_dir $OUTPUT_DIR
	python3 doc_preprocess/preprocess_indianexpress.py --input_file $filename --out_dir $OUTPUT_DIR
    elif [[ $filename == *"thehindu"* ]]; then
	python2 extract/boilerpipe_gettext.py --input_file $filename --out_dir $OUTPUT_DIR
	python3 doc_preprocess/preprocess_thehindu.py --input_file $filename --out_dir $OUTPUT_DIR
    elif [[ $filename == *"scmp"* ]]; then
	python2 extract/boilerpipe_gettext.py --input_file $filename --out_dir $OUTPUT_DIR --no_byte
	python3 doc_preprocess/preprocess_scmp.py --input_file $filename --out_dir $OUTPUT_DIR
    elif [[ $filename == *"people"* ]]; then
	python2 extract/boilerpipe_gettext.py --input_file $filename --out_dir $OUTPUT_DIR
	python3 doc_preprocess/preprocess_people.py --input_file $filename --out_dir $OUTPUT_DIR
    else
	echo "Something wrong!!!"
	echo "$filename"
done
