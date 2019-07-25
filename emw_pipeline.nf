#!/usr/bin/env nextflow

params.input_dir = "$baseDir/data"
params.input = "$params.input_dir/http*"
params.outdir = "$params.input_dir/../jsons/"
params.source_lang = "English"
params.source = 4
params.prefix = "/scratch/users/omutlu/emw_pipeline_nf"

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
        stdout(out_json) into extract_out
    script:
	if ( params.source == 1 )
        """
	    python3 $params.prefix/bin/extract/justext_gettext.py --input_file "$params.input_dir/$filename" --source_lang $params.source_lang
	"""
	else if ( params.source == 2 )
        """
	    python2 $params.prefix/bin/extract/goose_gettext.py --input_file "$params.input_dir/$filename"
	"""
	else if ( params.source == 3 )
        """
	    python2 $params.prefix/bin/extract/goose_gettext.py --input_file "$params.input_dir/$filename"
	"""
	else if ( params.source == 4 )
        """
	    python2 $params.prefix/bin/extract/boilerpipe_gettext.py --input_file "$params.input_dir/$filename"
	"""
	else if ( params.source == 5 )
        """
	    python2 $params.prefix/bin/extract/boilerpipe_gettext.py --input_file "$params.input_dir/$filename" --no_byte
	"""
	else if ( params.source == 6 )
        """
	    python2 $params.prefix/bin/extract/boilerpipe_gettext.py --input_file "$params.input_dir/$filename"
	"""
	else
	    error "No source as : ${params.source}"
}

process doc_preprocess {
    input:
        val(in_json) from extract_out
    output:
        stdout(out_json) into preprocess_out
    script:
	"""
	python3 $params.prefix/bin/doc_preprocess.py --input_dir $params.input_dir --data '$in_json' --source $params.source
	"""
}

process classifier {
    input:
        val(in_json) from preprocess_out
    output:
        stdout(out_json) into classifier_out
    script:
        """
        python3 $params.prefix/bin/classifier.py --data '$in_json' --out_dir $params.outdir
        """
}

process sent_classifier {
    input:
        val(in_json) from classifier_out
    output:
        stdout(out_json) into sent_out
    when:
        in_json.substring(in_json.length()-2,in_json.length()-1) == "1"
    script:
        in_json = in_json.substring(0,in_json.length()-3)
        """
	python3 $params.prefix/bin/sent_classifier.py --data '$in_json'
	"""
}

process trigger_classifier {
    input:
        val(in_json) from sent_out
    output:
        stdout(out_json) into trigger_out
    script:
    """
    python3 $params.prefix/bin/trigger_classifier.py --data '$in_json'
    """
}

process neuroner {
    input:
        val(in_json) from trigger_out
    script:
    """
    python3 $params.prefix/bin/neuroner.py --data '$in_json' --out_dir $params.outdir
    """
}