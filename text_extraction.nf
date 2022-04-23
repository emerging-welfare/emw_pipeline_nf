#!/usr/bin/env nextflow

input_channel = Channel.fromPath(params.input_dir + params.filename_wildcard)
println(params.input_dir + params.filename_wildcard)

process extract {
    //errorStrategy 'ignore'
    input:
	file(filename) from input_channel
    script:
	"""
	    python3 $params.extractor_script_path --input_file "$params.input_dir/$filename" --out_dir $params.outdir
	"""
}
