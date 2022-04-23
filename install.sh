# TODO: Update this! At least the download links for models!

# exit when any command fails
set -e
# keep track of the last executed command
trap 'last_command=$current_command; current_command=$BASH_COMMAND' DEBUG
# echo an error message before exiting
trap 'echo "\"${last_command}\" command filed with exit code $?."' EXIT

#Nextflow installation
echo "Installing Nextflow"
export NXF_VER=19.10.0
wget -qO- https://get.nextflow.io | bash
mv nextflow ./bin/
nextflow
echo "Nextflow installed"

#python requirements
#pip2 install -r requirements2.txt &&
echo "Installing python requirements"
pip install -r requirements.txt
echo "python requirements are installed"
#Extract & Doc Preprocess Dependencies
#git clone https://github.com/OsmanMutlu/python-boilerpipe.git && cd python-boilerpipe && python2 setup.py install && cd .. && rm -rf python-boilerpipe

# Tokenizer
echo "Installing nltk corpous"
python3 -c "import nltk;nltk.download('popular', halt_on_error=False)"
echo "nltk corpus are installed"

#BERT
echo "Installing OsmanMutlu/pytorch-pretrained-BERT"
cd .. && git clone https://github.com/OsmanMutlu/pytorch-pretrained-BERT.git && cd pytorch-pretrained-BERT && pip install .  && cd ..
echo "Finished installing OsmanMutlu/pytorch-pretrained-BERT"

echo "All necessary components are installed"


read -p "Do you wish download all the models? (Necessary if you don't already have them!) [Yy/Nn] : " -n 1 -r
echo    # (optional) move to a new line
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    exit 1
fi

echo "Downloading all BERT models"
mkdir ~/.pytorch_pretrained_bert && cd ~/.pytorch_pretrained_bert && wget https://s3.amazonaws.com/models.huggingface.co/bert/bert-base-uncased.tar.gz && wget https://s3.amazonaws.com/models.huggingface.co/bert/bert-base-uncased-vocab.txt
wget "https://www.dropbox.com/s/8lla2208h0hll37/doc_model.pt?dl=1" && mv doc_model.pt\?dl=1 ~/.pytorch_pretrained_bert/doc_model.pt
wget "https://www.dropbox.com/s/fxcgzl0bg7cgblf/sent_model.pt?dl=1" && mv sent_model.pt\?dl=1 ~/.pytorch_pretrained_bert/sent_model.pt
wget "https://www.dropbox.com/s/dnphbaecsvj4ubp/token_model.pt?dl=1" && mv token_model.pt\?dl=1 ~/.pytorch_pretrained_bert/token_model.pt
echo "BERT models and OsmanMutlu/pytorch-pretrained-BERT are installed"

#is_violent
echo "Installing Violent Classifier"
wget https://www.dropbox.com/s/74arnky6sr2705a/violent_model.pickle?dl=1 && mv violent_model.pickle?dl=1 ~/.pytorch_pretrained_bert/violent_model.pickle
echo "Violent Classifier is installed"

echo "Installing Urban-rural Classifier"
wget https://www.dropbox.com/s/bphcts6vnzpokks/ruralurbanclassifier?dl=1 && mv ruralurbanclassifier?dl=1 ~/.pytorch_pretrained_bert/rural_model.pickle
echo "Urban-rural Classifier is installed"


#Trigger Semantic Categorization
echo "Installing Trigger Semantic Categorization"
wget "https://www.dropbox.com/s/avd7g4vzcbz4o63/sem_cats_128.pt?dl=1" && mv sem_cats_128.pt\?dl=1 ~/.pytorch_pretrained_bert/sem_cats_128.pt
echo "Trigger Semantic Categorization is installed"

#Participant Semantic Categorization
echo "Installing Participant Semantic Categorization"
wget "https://www.dropbox.com/s/13s8p431aj5p2y9/part_sem_cats_128.pt?dl=1" && mv part_sem_cats_128.pt\?dl=1 ~/.pytorch_pretrained_bert/part_sem_cats_128.pt
echo "Participant Semantic Categorization is installed"

#Organizer Semantic Categorization
echo "Installing Organizer Semantic Categorization"
wget "https://www.dropbox.com/s/z01n8agtcbmmeyr/org_sem_cats_128.pt?dl=1" && mv org_sem_cats_128.pt\?dl=1 ~/.pytorch_pretrained_bert/org_sem_cats_128.pt
echo "Installing Organizer Semantic Categorization is installed"

# Flair Place Tagger
mkdir ~/.pytorch_pretrained_bert/models && wget "https://s3.eu-central-1.amazonaws.com/alan-nlp/resources/models-v0.4/NER-conll03-english/en-ner-conll03-v0.4.pt" && mv en-ner-conll03-v0.4.pt ~/.pytorch_pretrained_bert/en-ner-conll03-v0.4.pt

echo "All models are downloaded"
