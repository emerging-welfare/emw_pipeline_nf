#!/usr/bin/env nextflow

input_dir = params.input_dir
filename_wildcard = params.filename_wildcard
if (params.do_text_extraction) { // If we did text extraction then outdir contains the stuff we need.
   input_dir = params.outdir
   filename_wildcard = "*.json"
}

input_channel = Channel.fromPath(input_dir + filename_wildcard, relative: true)
println(input_dir + filename_wildcard)

process multi_task_classifier {
//    errorStrategy { try { if (in_json == null) { return 'ignore' }; for (String s in in_json) {s = s.replaceAll("\\[QUOTE\\]", "'"); data = jsonSlurper.parseText(s); new File(params.outdir + data["id"] + "json.sent").write(s, "UTF-8") } } catch(Exception ex) { println("Could not output json!") }; return 'ignore' }
    // errorStrategy 'ignore'
    input:
	val(in_json) from input_channel.collate(params.multi_task_batchsize)
    script:
	if (params.doc_cascaded) {
	"""
	python3 $params.prefix/bin/multi_task_classifier_batch.py --input_files '$in_json' --input_dir $input_dir --out_dir $params.outdir --language $params.source_lang --doc_cascaded
	"""
	}
	else {
	"""
	python3 $params.prefix/bin/multi_task_classifier_batch.py --input_files '$in_json' --input_dir $input_dir --out_dir $params.outdir --language $params.source_lang
	"""
	}
}
