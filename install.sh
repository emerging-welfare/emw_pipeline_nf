#Nextflow installation
export NXF_VER=19.10.0
wget -qO- https://get.nextflow.io | bash
mv nextflow ./bin
nextflow

#python requirements
#pip2 install -r requirements2.txt && 
pip3 install -r requirements.txt

#Extract & Doc Preprocess Dependencies
#git clone https://github.com/OsmanMutlu/python-boilerpipe.git && cd python-boilerpipe && python2 setup.py install && cd .. && rm -rf python-boilerpipe

#BERT
cd .. && git clone https://github.com/OsmanMutlu/pytorch-pretrained-BERT.git && cd pytorch-pretrained-BERT && pip3 install .  && cd ..
mkdir ~/.pytorch_pretrained_bert && cd ~/.pytorch_pretrained_bert && wget https://s3.amazonaws.com/models.huggingface.co/bert/bert-base-uncased.tar.gz && wget https://s3.amazonaws.com/models.huggingface.co/bert/bert-base-uncased-vocab.txt && wget "https://www.dropbox.com/s/4eu8ib47vusqupk/doc_model.pt?dl=1" && mv doc_model.pt\?dl=1 doc_model.pt && wget "https://www.dropbox.com/s/a0ut89hnzehekpl/sent_model.pt?dl=1" && mv sent_model.pt\?dl=1 sent_model.pt && wget "https://www.dropbox.com/s/s23zklmhvwjsy8f/svm_model.pkl?dl=1" && mv svm_model.pkl\?dl=1 svm_model.pkl && wget "https://www.dropbox.com/s/q8jmj10ozrnhct4/token_model.pt?dl=1" && mv token_model.pt\?dl=1 token_model.pt

# Tokenizer
python3 -c "import nltk;nltk.download('popular', halt_on_error=False)"

#is_violent 
mkdir bin/violent_classifier && cd bin/violent_classifier && wget https://www.dropbox.com/s/9zp0pgkadk0st8m/violent_model.pickle?dl=1 && mv violent_model.pickle?dl=1 violent_model.pickle

#Trigger Semantic Categorization
cd ~/.pytorch_pretrained_bert &&  wget "https://www.dropbox.com/s/ylayuknupfj1cra/sem_cats_128.pt?dl=1" && mv sem_cats_128.pt\?dl=1 sem_cats_128.pt

#Participant Semantic Categorization
cd ~/.pytorch_pretrained_bert &&  wget "https://www.dropbox.com/s/frgv24lftlp3lwk/part_sem_cats_128.pt?dl=1" && mv part_sem_cats_128.pt\?dl=1 part_sem_cats_128.pt


#Organizer Semantic Categorization
 cd ~/.pytorch_pretrained_bert &&  wget "https://www.dropbox.com/s/qft9b81fnkp5tsk/org_sem_cats_128.pt?dl=1" && mv org_sem_cats_128.pt\?dl=1 org_sem_cats_128.pt 