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

* [all_components](https://github.com/emerging-welfare/emw_pipeline_nf/tree/all_components)

To clone all_components branch
```
git checkout -b all_components  origin/all_components
git checkout all_components
```

This brach will run the pipeline as it illustrated in the flowchart. Where no filtering will be applied. where the file will cross by all component in all level. 

Flowchart,

![all_components](https://media.giphy.com/media/lrtUmgopBzTYIB3tA8/giphy.gif)


* [cascaded](https://github.com/emerging-welfare/emw_pipeline_nf/tree/cascaded)
This brach will run the pipeline as it illustrated in the flowchart. Where filtering will be applied and only postive sentences of a postive document will be passed.

To clone cascaded branch
```
git checkout -b cascaded  origin/cascaded
git checkout cascaded
```

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

## Run 
Set your parameters in `nextflow.conf` first. 
`start.sh` script will start the FLASK API of classifiers then will format the paramters that are in `nextflow.conf` to a JSON file and run nextflow. After nextflow is done reporting part will be started.

```
source start.sh
```