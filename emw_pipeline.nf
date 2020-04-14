#!/usr/bin/env nextflow

println("input path is set to $params.input")
println("outdir path is set to $params.outdir")
println("source lang is set to $params.source_lang")
println("source is set to $params.source")
println("document batchsize is set to $params.doc_batchsize")
println("token batchisize is set to $params.token_batchsize")
println("perfix is set to $params.prefix" )
println("classifier is first is  $params.classifier_first")

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
    output:
        stdout(out_json) into classifier_out
    script:
    if (params.cascaded)
    """
    python3 $params.prefix/bin/classifier_batch.py --input_files '$in_json' --out_dir $params.outdir --cascaded
    """
    else
    """
    python3 $params.prefix/bin/classifier_batch.py --input_files '$in_json' --out_dir $params.outdir
    """
}

}
else {

process first_classifier {
    // errorStrategy { try { if (in_json == null) { return 'ignore' }; for (String s in in_json) {s = s.replaceAll("\\[QUOTE\\]", "'"); data = jsonSlurper.parseText(s); new File(params.outdir + data["id"] + "json.preproc").write(s, "UTF-8") } } catch(Exception ex) { println("Could not output json!") }; return 'ignore' }
    // errorStrategy 'ignore'
    // beforeScript 'echo "Before doc $(date)" >> $HOME/runtimes.txt'
    // afterScript  'echo "After doc $(date)" >> $HOME/runtimes.txt'
    input:
	file(in_json) from html_channel.collate(params.doc_batchsize)
    output:
        stdout(out_json) into classifier_out
    script:
    if (params.cascaded)
    """
    python3 $params.prefix/bin/classifier_batch.py --input_files "$in_json" --out_dir $params.outdir --first --cascaded
    """
    else
    """
    python3 $params.prefix/bin/classifier_batch.py --input_files "$in_json" --out_dir $params.outdir --first
    """
        
}

}


process sent_classifier {
//    errorStrategy { try { if (in_json == null || in_json == "N") { return 'ignore' }; in_json = Eval.me(in_json).flatten(); for (String s in in_json) {s = s.replaceAll("\\[QUOTE\\]", "'"); data = jsonSlurper.parseText(s); new File(params.outdir + data["id"] + "json.doc").write(s, "UTF-8") } } catch(Exception ex) { println("Could not output json!") }; return 'ignore' }
//    errorStrategy 'ignore'
    // beforeScript 'echo "Before sent $(date)" >> $HOME/runtimes.txt'
    // afterScript  'echo "After sent $(date)" >> $HOME/runtimes.txt'
    input:
        val(in_json) from classifier_out.flatMap { n -> Eval.me(n) }
    output:
        stdout(out_json) into sent_out
    script:
    if (params.cascaded)
        """
	    python3 $params.prefix/bin/sent_classifier.py --data '$in_json'  --out_dir $params.outdir --cascaded
	    """
    else
        """
	    python3 $params.prefix/bin/sent_classifier.py --data '$in_json'  --out_dir $params.outdir
	    """
}

process token_classifier {
//    errorStrategy { try { if (in_json == null) { return 'ignore' }; for (String s in in_json) {s = s.replaceAll("\\[QUOTE\\]", "'"); data = jsonSlurper.parseText(s); new File(params.outdir + data["id"] + "json.sent").write(s, "UTF-8") } } catch(Exception ex) { println("Could not output json!") }; return 'ignore' }
    // errorStrategy 'ignore' 
    // beforeScript 'echo "Before tok $(date)" >> $HOME/runtimes.txt'
    // afterScript  'echo "After tok $(date)" >> $HOME/runtimes.txt'
  input:
        val(in_json) from sent_out.collate(params.token_batchsize)
    script:
    if (params.cascaded)
    """
    python3 $params.prefix/bin/token_classifier_batch.py --data '$in_json' --out_dir $params.outdir --cascaded
    """
    else
    """
    python3 $params.prefix/bin/token_classifier_batch.py --data '$in_json' --out_dir $params.outdir
    """
}

