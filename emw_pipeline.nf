#!/usr/bin/env nextflow
import groovy.json.JsonSlurper

params.input = "$baseDir/data/http*"
params.outdir = "$baseDir/results"
params.source_lang = "English"
params.source = 4

html_channel = Channel.fromPath(params.input)

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
        set val(out_json) file(filename) into extract_out
    script:
	if ( params.source == 1 )
        """
	    python3 bin/extract/justext_gettext.py --input_file $filename --source_lang $params.source_lang
	"""
	else if ( params.source == 2 )
        """
	    python2 bin/extract/goose_gettext.py --input_file $filename
	"""
	else if ( params.source == 3 )
        """
	    python2 bin/extract/goose_gettext.py --input_file $filename
	"""
	else if ( params.source == 4 )
        """
	    python2 bin/extract/boilerpipe_gettext.py --input_file $filename
	"""
	else if ( params.source == 5 )
        """
	    python2 bin/extract/boilerpipe_gettext.py --input_file $filename --no_byte
	"""
	else if ( params.source == 6 )
        """
	    python2 bin/extract/boilerpipe_gettext.py --input_file $filename
	"""
	else
	    error "No source as : ${params.source}"
}

process DTC {
    input:
        set val(in_json) file(filename) from extract_out
    output:
        set val(out_json) file(filename) into DTC_out
    script:
        """
        python3 bin/PublishDateGraper_DTC-nextflow.py --input_file $filename --data in_json
        """
}

process doc_preprocess {
    input:
        set val(in_json) file(filename) from DTC_out
    output:
        val(out_json) into preprocess_out
    script:
        """
	python3 bin/doc_preprocess.py --input_file $filename --data $in_json --source $params.source
	"""
}

process classifier {
    input:
        val(in_json) from preprocess_out
    output:
        set val(out_json) val(label) into classifier_out
    script:
        """
        python3 bin/classifier.py --data $in_json
        """
}

process placeTagger {
    input:
        set val(in_json) val(label) from classifier_out
    output:
        val(out_json) into place_out
    when:
        label == 1
    script:
        """
        python3 bin/placeTagger.py --data $in_json
        """
}

process temporalTagger {
    input:
        val(in_json) from place_out
    script:
        """
        python3 bin/temporalTagger.py --data $in_json
        """
}
