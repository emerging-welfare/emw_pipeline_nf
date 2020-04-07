#!/usr/bin/env nextflow

import groovy.json.JsonSlurper

// println("input path is set to $params.input")
// println("outdir path is set to $params.outdir")
// println("source lang is set to $params.source_lang")
// println("source is set to $params.source")
// println("document batchsize is set to $params.doc_batchsize")
// println("token batchisize is set to $params.token_batchsize")
// println("perfix is set to $params.prefix" )
// println("classifier is first is  $params.classifier_first")

// If we didn't run doc level, then input dir must contain sentences in it. If we did run doc level then outdir contains the stuff we need.
input_dir = params.input_dir
if (params.RUN_DOC) {
   input_dir = params.outdir // params.input_dir = params.outdir doesn't work for some reason
}

if (params.cascaded) {
    json_channel = Channel.fromPath(params.outdir + "positive_filenames.txt")
                          .splitCsv(header:true)
			  .map{ row-> file(input_dir + row.filename) }
}
else {
    json_channel = Channel.fromPath(input_dir + params.files_start_with)
}


process sent_preprocess {
//    errorStrategy { try { if (in_json == null || in_json == "N") { return 'ignore' }; in_json = Eval.me(in_json).flatten(); for (String s in in_json) {s = s.replaceAll("\\[QUOTE\\]", "'"); data = jsonSlurper.parseText(s); new File(params.outdir + data["id"] + "json.doc").write(s, "UTF-8") } } catch(Exception ex) { println("Could not output json!") }; return 'ignore' }
//    errorStrategy 'ignore'
    input:
	file(in_json) from json_channel
    output:
        stdout(out_json) into preprocess_out
    script:
    """
    	python3 $params.prefix/bin/sent_preprocess.py --input_file '$in_json'  --out_dir $params.outdir
    """
}

preprocess_out = preprocess_out.flatMap { it.split("\\[SPLIT\\]") }.collate( params.sent_batchsize )

// This sent_classifier can be where task parallelism happens
process sent_classifier {
//    errorStrategy { try { if (in_json == null || in_json == "N") { return 'ignore' }; in_json = Eval.me(in_json).flatten(); for (String s in in_json) {s = s.replaceAll("\\[QUOTE\\]", "'"); data = jsonSlurper.parseText(s); new File(params.outdir + data["id"] + "json.doc").write(s, "UTF-8") } } catch(Exception ex) { println("Could not output json!") }; return 'ignore' }
//    errorStrategy 'ignore'
    input:
	val(in_json) from preprocess_out
    output:
        stdout(out_json) into sent_out
    script:
        """
	python3 $params.prefix/bin/sent_classifier.py --data '$in_json' --out_dir $params.outdir --input_dir $input_dir
	"""
}

sent_out = sent_out.flatMap { it.split("\\[SPLIT\\]") }.groupBy{ it.split(":")[0] }.flatMap{ it.values() }
// sent_out = sent_out.flatMap { it.split("\\[SPLIT\\]") }.map{ it.split(",") }.groupTuple(by: 0)

process sent_output {
    input:
	val(in_json) from sent_out
    script:
        """
	python3 $params.prefix/bin/sent_output.py --data '$in_json' --out_dir $params.outdir --input_dir $input_dir
	"""
}
