#!/usr/bin/env nextflow

// If we did run multi_task then outdir contains the stuff we need.
input_dir = params.input_dir
filename_wildcard = params.filename_wildcard
if (params.do_text_extraction || params.RUN_MULTI_TASK || params.RUN_SENT) {
   input_dir = params.outdir // params.input_dir = params.outdir doesn't work for some reason
   filename_wildcard = "*.json"
}

if (params.doc_cascaded) {
    json_channel = Channel.fromPath(params.outdir + "positive_filenames.txt")
                          .splitCsv(header:false, sep: '\t').flatMap { it }
}
else {
    json_channel = Channel.fromPath(input_dir + filename_wildcard, relative: true)
}

process violent_classifier {
    // errorStrategy { try { if (in_json == null) { return 'ignore' }; for (String s in in_json) {s = s.replaceAll("\\[QUOTE\\]", "'"); data = jsonSlurper.parseText(s); new File(params.outdir + data["id"] + "json.preproc").write(s, "UTF-8") } } catch(Exception ex) { println("Could not output json!") }; return 'ignore' }
    // errorStrategy 'ignore'
    input:
	val(in_json) from json_channel.collate(params.doc_batchsize)
    script:
    """
    python3 $params.prefix/bin/violent_classifier.py --input_files "$in_json" --out_dir $params.outdir --input_dir $input_dir
    """
}
