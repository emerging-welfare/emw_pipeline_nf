#Nextflow installation
echo "Installing Nextflow"
export NXF_VER=19.10.0
wget -qO- https://get.nextflow.io | bash
mv nextflow ./bin
nextflow
echo "Nextflow installed"

#python requirements
#pip2 install -r requirements2.txt && 
echo "Installing python requirements"
pip install -r requirements.txt
echo "python requirements are installed"
#Extract & Doc Preprocess Dependencies
#git clone https://github.com/OsmanMutlu/python-boilerpipe.git && cd python-boilerpipe && python2 setup.py install && cd .. && rm -rf python-boilerpipe

#BERT
echo "Installing BERT models and OsmanMutlu/pytorch-pretrained-BERT"
cd .. && git clone https://github.com/OsmanMutlu/pytorch-pretrained-BERT.git && cd pytorch-pretrained-BERT && pip3 install .  && cd ..
mkdir ~/.pytorch_pretrained_bert && cd ~/.pytorch_pretrained_bert && wget https://s3.amazonaws.com/models.huggingface.co/bert/bert-base-uncased.tar.gz && wget https://s3.amazonaws.com/models.huggingface.co/bert/bert-base-uncased-vocab.txt && wget "https://www.dropbox.com/s/4eu8ib47vusqupk/doc_model.pt?dl=1" && mv doc_model.pt\?dl=1 doc_model.pt && wget "https://www.dropbox.com/s/a0ut89hnzehekpl/sent_model.pt?dl=1" && mv sent_model.pt\?dl=1 sent_model.pt && wget "https://www.dropbox.com/s/s23zklmhvwjsy8f/svm_model.pkl?dl=1" && mv svm_model.pkl\?dl=1 svm_model.pkl && wget "https://www.dropbox.com/s/q8jmj10ozrnhct4/token_model.pt?dl=1" && mv token_model.pt\?dl=1 token_model.pt
echo "BERT models and OsmanMutlu/pytorch-pretrained-BERT are installed"
# Tokenizer
echo "Installing nltk corpous"
python3 -c "import nltk;nltk.download('popular', halt_on_error=False)"
echo "nltk corpous are installed"

echo "Installing Violent Classifier" 

cd ~/.pytorch_pretrained_bert && wget https://www.dropbox.com/s/74arnky6sr2705a/violent_model.pickle?dl=0 && mv violent_model.pickle?dl=1 violent_model.pickle

echo "Violent Classifier is installed"



#Trigger Semantic Categorization

echo "Installing Trigger Semantic Categorization"

cd ~/.pytorch_pretrained_bert &&  wget "https://www.dropbox.com/s/avd7g4vzcbz4o63/sem_cats_128.pt?dl=0" && mv sem_cats_128.pt\?dl=1 sem_cats_128.pt

echo "Trigger Semantic Categorization is installed"



#Participant Semantic Categorization

echo "Installing Participant Semantic Categorization"

cd ~/.pytorch_pretrained_bert &&  wget "https://www.dropbox.com/s/13s8p431aj5p2y9/part_sem_cats_128.pt?dl=0" && mv part_sem_cats_128.pt\?dl=1 part_sem_cats_128.pt

echo "Participant Semantic Categorization is installed"



#Organizer Semantic Categorization

echo "Installing Organizer Semantic Categorization"

cd ~/.pytorch_pretrained_bert &&  wget "https://www.dropbox.com/s/z01n8agtcbmmeyr/org_sem_cats_128.pt?dl=0" && mv org_sem_cats_128.pt\?dl=1 org_sem_cats_128.pt 

echo "Installing Organizer Semantic Categorization is installed"


# Flair Place Tagger
cd ~/.pytorch_pretrained_bert && mkdir models && cd models && wget "https://s3.eu-central-1.amazonaws.com/alan-nlp/resources/models-v0.4/NER-conll03-english/en-ner-conll03-v0.4.pt"
 
echo "All necessary components are installed"
cd ..
