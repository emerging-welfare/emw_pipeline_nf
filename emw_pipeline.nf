#!/usr/bin/env nextflow
//import groovy.json.JsonSlurper

params.input_dir = "$baseDir/data"
params.input = "$params.input_dir/*html"
params.outdir = "$baseDir/jsons/"
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
    errorStrategy 'ignore'
    input:
        file(filename) from html_channel
    output:
        stdout(out_json) into extract_out
    script:
	if ( params.source == 1 )
        """
	    python3 /emw_pipeline_nf/bin/extract/justext_gettext.py --input_file "$params.input_dir/$filename" --source_lang $params.source_lang
	"""
	else if ( params.source == 2 )
        """
	    python2 /emw_pipeline_nf/bin/extract/goose_gettext.py --input_file "$params.input_dir/$filename"
	"""
	else if ( params.source == 3 )
        """
	    python2 /emw_pipeline_nf/bin/extract/goose_gettext.py --input_file "$params.input_dir/$filename"
	"""
	else if ( params.source == 4 )
        """
	    python2 /emw_pipeline_nf/bin/extract/boilerpipe_gettext.py --input_file "$params.input_dir/$filename"
	"""
	else if ( params.source == 5 )
        """
	    python2 /emw_pipeline_nf/bin/extract/boilerpipe_gettext.py --input_file "$params.input_dir/$filename" --no_byte
	"""
	else if ( params.source == 6 )
        """
	    python2 /emw_pipeline_nf/bin/extract/boilerpipe_gettext.py --input_file "$params.input_dir/$filename"
	"""
	else
	    error "No source as : ${params.source}"
}

process doc_preprocess {
    errorStrategy { try { in_json = in_json.replaceAll("\\[QUOTE\\]", "'"); if (in_json == null) { return 'ignore' } ;data = jsonSlurper.parseText(in_json); new File("jsons/" + data["id"].replaceAll("\\.[^\\.]+$", ".") + "json.extract").write(in_json, "UTF-8") } catch(Exception ex) { println("Could not output json!") }; return 'ignore' }
    input:
        val(in_json) from extract_out
    output:
        stdout(out_json) into preprocess_out
    script:
	"""
	python3 /emw_pipeline_nf/bin/doc_preprocess.py --input_dir $params.input_dir --data '$in_json' --source $params.source
	"""
}

process classifier {
    errorStrategy { try { in_json = in_json.replaceAll("\\[QUOTE\\]", "'"); if (in_json == null) { return 'ignore' } ;data = jsonSlurper.parseText(in_json); new File("jsons/" + data["id"].replaceAll("\\.[^\\.]+$", ".") + "json.preprocess").write(in_json, "UTF-8") } catch(Exception ex) { println("Could not output json!") }; return 'ignore' }
    input:
        val(in_json) from preprocess_out
    output:
        stdout(out_json) into classifier_out
    script:
        """
        python3 /emw_pipeline_nf/bin/classifier.py --data '$in_json' --out_dir $params.outdir
        """
}

process DCT {
    errorStrategy { try { in_json = in_json.replaceAll("\\[QUOTE\\]", "'"); if (in_json == null) { return 'ignore' } ;data = jsonSlurper.parseText(in_json); new File("jsons/" + data["id"].replaceAll("\\.[^\\.]+$", ".") + "json.doc").write(in_json, "UTF-8") } catch(Exception ex) { println("Could not output json!") }; return 'ignore' }
    input:
        val(in_json) from classifier_out
    output:
        stdout(out_json) into DCT_out
    when:
        in_json.substring(in_json.length()-2,in_json.length()-1) == "1"
    script:
        in_json = in_json.substring(0,in_json.length()-3)
	if ( params.source == 5 )
        """
        python3 /emw_pipeline_nf/bin/PublishDateGraper_DTC-nextflow.py --input_dir $params.input_dir --data '$in_json' --no_byte
        """
	else
	"""
	python3 /emw_pipeline_nf/bin/PublishDateGraper_DTC-nextflow.py --input_dir $params.input_dir --data '$in_json'
	"""
}

process sent_classifier {
    errorStrategy { try { in_json = in_json.replaceAll("\\[QUOTE\\]", "'"); if (in_json == null) { return 'ignore' } ;data = jsonSlurper.parseText(in_json); new File("jsons/" + data["id"].replaceAll("\\.[^\\.]+$", ".") + "json.DCT").write(in_json, "UTF-8") } catch(Exception ex) { println("Could not output json!") }; return 'ignore' }
    input:
        val(in_json) from DCT_out
    output:
        stdout(out_json) into sent_out
    script:
    """
    python3 /emw_pipeline_nf/bin/sent_classifier.py --data '$in_json'
    """
}

process token_classifier {
    errorStrategy { try { in_json = in_json.replaceAll("\\[QUOTE\\]", "'"); if (in_json == null) { return 'ignore' } ;data = jsonSlurper.parseText(in_json); new File("jsons/" + data["id"].replaceAll("\\.[^\\.]+$", ".") + "json.sent").write(in_json, "UTF-8") } catch(Exception ex) { println("Could not output json!") }; return 'ignore' }
    input:
        val(in_json) from sent_out
    script:
    """
    python3 /emw_pipeline_nf/bin/token_classifier.py --data '$in_json' --out_dir $params.outdir
    """
}