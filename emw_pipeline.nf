#!/usr/bin/env nextflow
//import groovy.json.JsonSlurper

params.input_dir = "$baseDir/data"
params.input = "$params.input_dir/*html"
params.outdir = "$params.input_dir/../jsons"
params.source_lang = "English"
params.source = 4

html_channel = Channel.fromPath(params.input)
println(params.input)
// Source 1 times
// Source 2 newind
// Source 3 ind
// Source 4 thehin
// Source 5 scm
// Source 6 people

process extract {
    input:
        file(filename) from html_channel
    output:
//        set val(out_json) file(filename) into extract_out
        stdout(out_json) into extract_out
    script:
	if ( params.source == 1 )
        """
	    python3 /new_pipeline/bin/extract/justext_gettext.py --input_file "$params.input_dir/$filename" --source_lang $params.source_lang
	"""
	else if ( params.source == 2 )
        """
	    python2 /new_pipeline/bin/extract/goose_gettext.py --input_file "$params.input_dir/$filename"
	"""
	else if ( params.source == 3 )
        """
	    python2 /new_pipeline/bin/extract/goose_gettext.py --input_file "$params.input_dir/$filename"
	"""
	else if ( params.source == 4 )
        """
	    python2 /new_pipeline/bin/extract/boilerpipe_gettext.py --input_file "$params.input_dir/$filename"
	"""
	else if ( params.source == 5 )
        """
	    python2 /new_pipeline/bin/extract/boilerpipe_gettext.py --input_file "$params.input_dir/$filename" --no_byte
	"""
	else if ( params.source == 6 )
        """
	    python2 /new_pipeline/bin/extract/boilerpipe_gettext.py --input_file "$params.input_dir/$filename"
	"""
	else
	    error "No source as : ${params.source}"
}

process DTC {
    input:
//        set val(in_json) file(filename) from extract_out
        val(in_json) from extract_out
    output:
        stdout(out_json) into DTC_out
    script:
	if ( params.source == 5 )
        """
        python3 /new_pipeline/bin/PublishDateGraper_DTC-nextflow.py --input_dir $params.input_dir --data '$in_json' --no_byte
        """
	else
	"""
	python3 /new_pipeline/bin/PublishDateGraper_DTC-nextflow.py --input_dir $params.input_dir --data '$in_json'
	"""
}
// python3 bin/PublishDateGraper_DTC-nextflow.py --input_file $filename --data in_json

process doc_preprocess {
    input:
        val(in_json) from DTC_out
    output:
        stdout(out_json) into preprocess_out
    script:
	"""
	python3 /new_pipeline/bin/doc_preprocess.py --input_dir $params.input_dir --data '$in_json' --source $params.source
	"""
}

process classifier {
    input:
        val(in_json) from preprocess_out
    output:
        stdout(out_json) into classifier_out
    script:
        """
        python3 /new_pipeline/bin/classifier.py --data '$in_json'
        """
}

process placeTagger {
    input:
        val(in_json) from classifier_out
    output:
        stdout(out_json) into place_out
    when:
        """if [`echo $in_json | rev | cut -d "," -f 1` = 1 ];then echo "True";fi"""
    script:
        """
        python3 /new_pipeline/bin/placeTagger.py --data '$in_json'
        """
}

process temporalTagger {
    input:
        val(in_json) from place_out
    script:
        """
        python3 /new_pipeline/bin/temporalTagger.py --data '$in_json'
        """
}
