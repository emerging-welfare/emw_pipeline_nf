#!/usr/bin/env nextflow

// println("input path is set to $params.input")
// println("outdir path is set to $params.outdir")
// println("source lang is set to $params.source_lang")
// println("source is set to $params.source")
// println("document batchsize is set to $params.doc_batchsize")
// println("token batchisize is set to $params.token_batchsize")
// println("perfix is set to $params.prefix" )
// println("classifier is first is  $params.classifier_first")

// If we didn't run doc level or sent_level, then input dir have sentences in it. If we did run doc level or sent_level then outdir contains the stuff we need.
input_dir = params.input_dir
if (params.RUN_DOC || params.RUN_SENT) {
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

process token_classifier {
//    errorStrategy { try { if (in_json == null) { return 'ignore' }; for (String s in in_json) {s = s.replaceAll("\\[QUOTE\\]", "'"); data = jsonSlurper.parseText(s); new File(params.outdir + data["id"] + "json.sent").write(s, "UTF-8") } } catch(Exception ex) { println("Could not output json!") }; return 'ignore' }
    // errorStrategy 'ignore'
  input:
        val(in_json) from json_channel.collate(params.token_batchsize)
    script:
    """
    python3 $params.prefix/bin/token_classifier_batch.py --input_files '$in_json' --out_dir $params.outdir
    """
}
