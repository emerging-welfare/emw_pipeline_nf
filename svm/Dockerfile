FROM python:3.6.4
MAINTAINER Abdulrahman Alabrash <aalabrash18@ku.edu.tr>

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
#RUN  python -c "import nltk;nltk.download('stopwords');nltk.download('wordnet');nltk.download('averaged_perceptron_tagger');nltk.download('punkt');nltk.download('maxent_ne_chunker');nltk.download('words')"
RUN python -c "import nltk;nltk.download('popular', halt_on_error=False)"
COPY . .

CMD [ "python", "./run.py" ]
