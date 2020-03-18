#!/usr/bin/env nextflow

// println("input path is set to $params.input")
// println("outdir path is set to $params.outdir")
// println("source lang is set to $params.source_lang")
// println("source is set to $params.source")
// println("document batchsize is set to $params.doc_batchsize")
// println("token batchisize is set to $params.token_batchsize")
// println("perfix is set to $params.prefix" )
// println("classifier is first is  $params.classifier_first")

html_channel = Channel.fromPath(params.input)
println(params.input)

if (!params.classifier_first) {

process extract {
   //errorStrategy 'ignore'
   input:
       file(filename) from html_channel
   output:
       stdout(out_json) into extract_out
    when:
        !params.classifier_first

   script:
	def asd = ".json"
	def file = new File(params.outdir + filename + ".json")
	if ( file.exists() )
	"""
	    echo '"$filename$asd"'
	"""
	else
       """
	    python3 $params.extractor_script_path --input_file "$params.input_dir/$filename" --out_dir $params.outdir
	"""
}


process classifier {
    // errorStrategy { try { if (in_json == null) { return 'ignore' }; for (String s in in_json) {s = s.replaceAll("\\[QUOTE\\]", "'"); data = jsonSlurper.parseText(s); new File(params.outdir + data["id"] + "json.preproc").write(s, "UTF-8") } } catch(Exception ex) { println("Could not output json!") }; return 'ignore' }
    // errorStrategy 'ignore'
    input:
	val(in_json) from extract_out.collate(params.doc_batchsize)
    script:
    """
    python3 $params.prefix/bin/classifier_batch.py --input_files "$in_json" --out_dir $params.outdir --first
    """
}

}
else {

process first_classifier {
    // errorStrategy { try { if (in_json == null) { return 'ignore' }; for (String s in in_json) {s = s.replaceAll("\\[QUOTE\\]", "'"); data = jsonSlurper.parseText(s); new File(params.outdir + data["id"] + "json.preproc").write(s, "UTF-8") } } catch(Exception ex) { println("Could not output json!") }; return 'ignore' }
    // errorStrategy 'ignore'
    input:
	file(in_json) from html_channel.collate(params.doc_batchsize)
    script:
    """
    python3 $params.prefix/bin/classifier_batch.py --input_files "$in_json" --out_dir $params.outdir --first
    """
}

}
