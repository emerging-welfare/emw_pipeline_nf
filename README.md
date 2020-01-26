This repo is a pipeline that takes an HTML/JSON formatted news articles and do several NLP tasks on them. 

An input file will cross by all/some the components of the pipeline. The output of each component will be written directly to a copy of the given file.
where the output of each component is as follows, 

* Document classifier -> 'doc_label'=0/1 
* Violent_classifer -> 'is_violent'=0/1
* Sentence_classifier will tokenize the sentences and get their labels for 4 different classifers-> 
    * 'sentences'=[]
    * 'sentence_labels'=[]
    * 'sentence_tokens'=[[]]
    * 'Trigger_Semantic_label'=[] 
    * 'participant_semantic'=[] 
    * 'organizer_semantic'=[] 

* Token_classifers -> 'token_labels'=[[]]

* report script (`bin/out_to_csv.py`) will create a detailed report on sentence base and merge coreferensed setnences using `[NS]` token.

[An example output](output_example.md) can be found at the end of the page. 

This Repo contains two branchs ,
# Pipeline Configuration. 

* when cascaded parameter is true

This option will run the pipeline as it illustrated in the flowchart. Where no filtering will be applied. where the file will cross by all component in all level. 

Flowchart,

![all_components](https://media.giphy.com/media/lrtUmgopBzTYIB3tA8/giphy.gif)


* when cascaded parameter is false
This option will run the pipeline as it illustrated in the flowchart. Where filtering will be applied and only postive sentences of a postive document will be passed.


![cascaded](https://media.giphy.com/media/gIOFwSETRmtKI29yIj/giphy.gif)


## Prerequisite
* Java 7 or 8
* Python3


## Installation
`install.sh` will install/download the following models in $HOME/.pytorch_pretrained_bert folder

* Nextflow
* Python requirments libraries (requirement.txt)
* OsmanMutlu/pytorch-pretrained-BERT
* Document Models (Protest classifier (BERT) - Violent Classifier (SVM) ) 
* Sentence Model (Protest classifier (BERT) - Participant Semantic Categorization (BERT), Trigger Semantic Categorization (BERT), and Organizer Semantic Categorization (BERT)- Coreference Model (ALBERT))
* Token Model(Token Classifier)
```
cd emw_pipeline_nf
source install.sh
```

## Parameters
It can be modified in `nextflow.conf` file 
* cascaded 

    true/false 

* classifier_first

    true/false
    if false pipeline starts with extractor if True the first component of the pipeline will be classifier

* gpu_classifier
    
    number of the group of the GPU/'s is/are assgined to document proteset classifier.

    A single number or series of number joined by comma ie 1,2,3

* gpu_number_tsc
    
    number of the group of the GPU/'s is/are assgined to trigger semantic classifier.

    A single number or series of number joined by comma ie 1,2,3

* gpu_number_psc

    number of the group of the GPU/'s is/are assgined to participant semantic classifier.

    A single number or series of number joined by comma ie 1,2,3

* gpu_number_osc

    number of the group of the GPU/'s is/are assgined to organization semantic classifier.

    A single number or series of number joined by comma ie 1,2,3

* gpu_number_protest

    number of the group of the GPU/'s is/are assgined to sentence protest classifier.

    A single number or series of number joined by comma ie 1,2,3
* gpu_token

    number of the group of the GPU/'s is/are assgined to token classifier.

    A single number or series of number joined by comma ie 1,2,3

* input

    input folder Path 

    "\<PATH\>" .not ending with backslash

* output

    output folder path

    "\<PATH\>/jsons/"

* resume
    nextflow's parameter https://www.nextflow.io/docs/latest/getstarted.html#modify-and-resume

    true/false

* files_start_with
    
    file name pattern
    ie "*" ,"\*json" ,"\http\*"


* doc_batchsize

    Document protest classifier batch size 

* token_batchsize

    token classifier batch size 

* prefix

    path to pipeline scripts

   ie "\<Path\>/emw_pipeline_nf" 

* extractor_script_path

    path to html to text script 

    ie $prefix"/bin/extract/peoples_chaina.py" # 

#out_to_csv script's parameters 
* out_output_type

    type of output record 

    csv/json

* out_name_output_file

    name of outfile record

* out_date_key

    the key of date in the dataset

    ie "time","date"

* filter_unprotested_sentence

    inclulde protest sentence in the record 

    true/false

* filter_unprotested_documents
    
    inclulde protest document in the record 

    true/false


## Run 
Set your parameters in `nextflow.conf` first. 
`start.sh` script will start the FLASK API of classifiers then will format the paramters that are in `nextflow.conf` to a JSON file and run nextflow. After nextflow is done reporting part will be started.

```
source start.sh
```