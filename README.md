# EMW pipeline using Nextflow & Docker 
[Docker image's components](https://github.com/alabrashJr/emw_pipeline_docker)

## Prerequisite

* Java 7 or 8 
* Docker engine 1.10.x (or higher) 
* miniconda3 

## Installation 

Install Nextflow with miniconda by using the following command: 

```
conda create --name <env-name> python==3.6.4 --yes
conda activate <env-name>
conda install -c bioconda nextflow==18.10.1 --yes
nextflow
```
    
Finally, clone this repository with the following command: 

```
docker pull alabrashjr/emw_pipeline:v1.2
git clone https://github.com/alabrashJr/emw_pipeline_nf.git
pip install -r requirements.txt
python bootstrap.py
```

Try to specify a different input parameter, for example: 

## Parameters (is not tested yet)

* input 
```
python bootstrap.py --input this/and/that
```
or matching the pattern specified are grouped in pairs having 
the same prefix.
```
python bootstrap.py --input 'data/*_{1,2}.html'
```

to get all html files, 

```
python bootstrap.py --input 'data/*.html'
```
* resume 

The `-resume` option skips the execution of any step that has been processed in a previous 
execution. 

i.e
```
python bootstrap.py -resume --input 'data/*_{1,2}.html'
```


* output 

This step shows how produce the pipeline output to a folder of your choice by using the 
`publishDir` directive. 

Run the example by using the following command: 


```
nextflow run rna-ex6.nf -resume --input 'data/*_{1,2}.html' --outdir results_output
```

You will find the outputs produced by the pipeline in the `results_output` folder.


Flowchart, 
-----------
                                     HTML Pages
                                        |
                                        |
                                        |
                                        |
                                       / \
                        Clean & Parser      DCTFinder
                             |
                             |
                             |
                             |
                         classifier                          
                             |
                             |
                             |          N O 
                         if protest ----------
                             |
                             |Y
                             |E
                             |S
                            /  \
                  placeTragger  TemproalTragger