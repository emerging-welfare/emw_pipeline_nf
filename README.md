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

# Pipeline Configuration. 

* when cascaded parameter is true

It will run the pipeline as illustrated in the flowchart below. Where no filtering will be applied hence, files will cross by all component in all level. 

Flowchart,


![cascaded](https://user-images.githubusercontent.com/9295206/73354823-b01ec680-42a7-11ea-98a1-d8f7f2c84e7b.png)

[gif version](https://media.giphy.com/media/lrtUmgopBzTYIB3tA8/giphy.gif)


* when cascaded parameter is false
It will run the pipeline as illustrated in the flowchart below. Where filtering will be applied and only postive sentences of a postive document will be passed.

 
![flowchart_hpc](https://user-images.githubusercontent.com/9295206/73265441-09262600-41e6-11ea-93d4-6b561c3020f3.png)


[gif version](https://media.giphy.com/media/gIOFwSETRmtKI29yIj/giphy.gif)


## Prerequisite
* Java 7 or 8
* Python3


## Installation
`install.sh` will install/download the following models in $HOME/.pytorch_pretrained_bert folder.

* Nextflow
* Python requirments libraries (requirement.txt)
* OsmanMutlu/pytorch-pretrained-BERT
* Document Models (Protest classifier (BERT) - Violent Classifier (SVM) ) 
* Sentence Model (Protest classifier (BERT) - Participant Semantic Categorization (BERT), Trigger Semantic Categorization (BERT), and Organizer Semantic Categorization (BERT)- Coreference Model (ALBERT))
* Token Model(Token Classifier)

```
conda create -n ENV_NAME python=3.6
conda activate ENV_NAME
cd emw_pipeline_nf
source install.sh
```

## Parameters
It can be modified in `nextflow.conf` file 
* `cascaded`

    true/false

    as it's explained in 'Pipeline Configuration' section.

* `classifier_first`

    true/false

    if false pipeline starts with extractor.

    if true the first component of the pipeline will be the classifier, hence the input files must be JSON formatted and contain the following variables,
    ```
    {
        "id":str,
        "length":int,
        "text":str,
        "time":str,
        "title":str
    }
    ```

* `gpu_classifier`
    
    GPU id or group of GPU ids that is/are assgined to document proteset classifier.

    A single number or series of number joined by comma ie 1,2,3

* `gpu_number_tsc`
    
    GPU id or group of GPU ids that is/are assgined to trigger semantic classifier.

    A single number or series of number joined by comma ie 1,2,3

* `gpu_number_psc`

    GPU id or group of GPU ids that is/are assgined to participant semantic classifier.

    A single number or series of number joined by comma ie 1,2,3

* `gpu_number_osc`

    GPU id or group of GPU ids that is/are assgined to organization semantic classifier.

    A single number or series of number joined by comma ie 1,2,3

* `gpu_number_protest`

    GPU id or group of GPU ids that is/are assgined to sentence protest classifier.

    A single number or series of number joined by comma ie 1,2,3

* `gpu_token`

    GPU id or group of GPU ids that is/are assgined to token classifier.

    A single number or series of number joined by comma ie 1,2,3

* `input`

    input folder Path 

    "\<PATH\>" .not ending with backslash

* `output`

    output folder path

    "\<PATH\>/jsons/"

* `resume`

    true/false

    nextflow's parameter https://www.nextflow.io/docs/latest/getstarted.html#modify-and-resume    

* `files_start_with`
    
    file names pattern

    ie "*" ,"\*json" ,"\http\*"

* `doc_batchsize`

    Document protest classifier batch size 

* `token_batchsize`

    token classifier batch size 

* `prefix`

    path to pipeline scripts

    ie "\<Path\>/emw_pipeline_nf" 

* `extractor_script_path`

    path to html to text script 

    ie $prefix"/bin/extract/peoples_chaina.py" # 

#### out_to_csv script's parameters 
* `out_output_type`

    type of output record file

    csv/json

* `out_name_output_file`

    name of outfile record file

* `out_date_key`

    the key of date inside the dataset

    ie "time","date"

* `filter_unprotested_sentence`

    true/false
    
    filter protest sentences in the record file.

    if true only sentences that are postive will be inculded.

    if false all the sentences will be included irrespective of their label

* `filter_unprotested_documents`
    
    true/false

    filter protest document in the record file.

    if true only sentences that are in postive document will be inculded.

    if false all the sentences will be include irrespective of their document label


## Run 
Set your parameters in `nextflow.conf` first. 
`start.sh` script will start the FLASK API of classifiers then will format the paramters that are in `nextflow.conf` to a JSON file and run nextflow. After nextflow is done reporting part will be started.

```
source start.sh
```