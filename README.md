# EMW pipeline using Nextflow & Docker

## Installation
```
git clone https://github.com/emerging-welfare/emw_pipeline_nf.git
cd emw_pipeline_nf
docker build --tag=<an_image_name> .
docker run --rm --name <an_container_name> -it <the_image_name> /bin/bash 
bash start.sh
```

The input will be all html files from data folder and the output will be written to jsons folder.

Flowchart,
-----------
                  
                         HTML Pages
                             |
                             |
                             |
                             |
                             
                        Clean & Parser      
                             |
                             |
                             |
                             |
                             
                      document_classifier
                             |
                             |
                             |
                             |
                                       N O
                         if protest ----------
                             |
                             |Y
                             |E
                             |S
                             |
                          DCTFinder
                             |
                             |
                             |
                             |
                       sentences_classifier
                             |
                             |
                             |
                             |
                       token_classifier
                             |
                             |
                             |
                             |
                           OUTPUT
                             
                             
          


