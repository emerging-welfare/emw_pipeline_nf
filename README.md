# EMW pipeline using Nextflow & Docker 

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
git clone https://github.com/alabrashJr/emw_pipeline_nf.git
python bootstrap.py
```

Try to specify a different input parameter, for example: 

```
python bootstrap.py --input this/and/that
```

read files by using a glob pattern:

```
python bootstrap.py --input 'data/ggal/reads/*_{1,2}.html'
```
It shows how read files matching the pattern specified are grouped in pairs having 
the same prefix.

to get all html files, 

```
python bootstrap.py --input 'data/here/reads/*.html'
```

The `-resume` option skips the execution of any step that has been processed in a previous 
execution. 

Try to execute it with more read files as shown below: 

```
python bootstrap.py -resume --reads 'data/here/reads/*_{1,2}.html'
```


### Step 6 - Define the pipeline output

This step shows how produce the pipeline output to a folder of your choice by using the 
`publishDir` directive. 

Run the example by using the following command: 


```
nextflow run rna-ex6.nf -resume --reads 'data/here/reads/*_{1,2}.html' --outdir my_transcripts
```

You will find the transcripts produced by the pipeline in the `my_transcripts` folder.


 

Nextflow allows you to use and manage all these scripts in consistent manner. Simply put them 
in a directory named `bin` in the pipeline project root. They will be automatically added 
to the pipeline execution `PATH`. 

For example, create a file named `quantify.sh` with the following content: 

```
#!/bin/bash 
set -e 
set -u

annot=${1}
bam_file=${2}
pair_id=${3}

cufflinks --no-update-check -q -G $annot ${bam_file}
mv transcripts.gtf transcript_${pair_id}.gtf
```

Save it, grant the execute permission and move it under the `bin` directory as shown below: 

```
chmod +x quantify.sh
mkdir -p bin 
mv quantify.sh bin
```

Then, open the `rna-ex7.nf` file and replace the `makeTranscript` process with 
the following code: 

```
process makeTranscript {
    tag "$pair_id"
    publishDir params.outdir, mode: 'copy'  
       
    input:
    file annot from annotation_file 
    set pair_id, file(bam_file) from bam
     
    output:
    set pair_id, file('transcript_*.gtf') into transcripts
 
    """
    quantify.sh $annot $bam_file $pair_id
    """
}

```

