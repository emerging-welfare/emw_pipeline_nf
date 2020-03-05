#!/usr/bin/env python3
import os
import numpy
from pathlib import Path
import pickle
from nltk.corpus import stopwords as sw
from nltk.corpus import wordnet as wn
from nltk import wordpunct_tokenize
from nltk import WordNetLemmatizer
from nltk import sent_tokenize
from sklearn.linear_model import SGDClassifier
from nltk import pos_tag
from sklearn.base import BaseEstimator, TransformerMixin

# Import the framework
from flask import Flask, g
from flask_restful import Resource, Api, reqparse
# Create an instance of Flask
app = Flask(__name__)

# Create the API
api = Api(app)

@app.route("/")
def index():
    # Open the README file
    #with open(os.path.dirname(app.root_path) + '/README.md', 'r') as markdown_file:
    # Read the content of the file
    #content = str("\n ".join(main(file)))

    # Convert to HTML
    #if classifer is not None :
    # return markdown.markdown("classifier is loaded")
    return "<html><body><p>classifier is loaded</p></body></html>"
    #else :
    #    return "<html><body><p>classifier is not loaded</p></body></html>"
        # return markdown.markdown("classifier is not loaded"

class NLTKPreprocessor(BaseEstimator, TransformerMixin):
    #it loads a variety of corpora and models for use in tokenization.
    #By default the set of english stopwords from NLTK is used, and the WordNetLemmatizer
    #looks up data from the WordNet lexicon. Note that this takes a noticeable amount of time, 
    #and should only be done on instantiation of the transformer.

    def __init__(self, stopwords=None, punct=None,
                         lower=True, strip=True):
        self.lower      = lower
        self.strip      = strip
        self.stopwords  = stopwords or set(sw.words('english'))
        self.punct      = punct or set(string.punctuation)
        self.lemmatizer = WordNetLemmatizer()

    def fit(self, X, y=None):
        return self

    def inverse_transform(self, X):
        return [" ".join(doc) for doc in X]

    def transform(self, X):
        return [list(self.tokenize(doc)) for doc in X]
            
        #The tokenize method breaks raw strings into sentences,
        #then breaks those sentences into words and punctuation,
        #and applies a part of speech tag. The token is then normalized:
        #made lower case, then stripped of whitespace and other types of punctuation that may be appended.
        #If the token is a stopword or if every character is punctuation, the token is ignored.
        #If it is not ignored, the part of speech is used to lemmatize the token, which is then yielded
    def tokenize(self, document):
        # Break the document into sentences
        for sent in sent_tokenize(document):
            # Break the sentence into part of speech tagged tokens
            for token, tag in pos_tag(wordpunct_tokenize(sent)):
                   # Apply preprocessing to the token
                    token = token.lower() if self.lower else token
                    token = token.strip() if self.strip else token
                    token = token.strip('_') if self.strip else token

                    token = token.strip('*') if self.strip else token

                    # If stopword, ignore token and continue
                    if token in self.stopwords:
                            continue
                    # If punctuation, ignore token and continue
                    if all(char in self.punct for char in token):
                            continue

                        # Lemmatize the token and yield
                    lemma = self.lemmatize(token, tag)
                    yield lemma

    def lemmatize(self, token, tag):
        tag = {'N': wn.NOUN,'V': wn.VERB,'R': wn.ADV,'J': wn.ADJ}.get(tag[0], wn.NOUN)
        return self.lemmatizer.lemmatize(token, tag)

class queryList(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('text', required=False, type=str, action='append', default=[])
        #parser.add_argument('output', required=False)
        args = parser.parse_args()

        #args["is_violent"] = str(model.predict(args["text"])[0])
        return str(model.predict(args["text"])[0])
        #return args, 201

def identity(arg):
    """
    Simple identity function works as a passthrough.
    """
    return arg


global model
HOME=os.getenv("HOME")
with open(HOME+"/.pytorch_pretrained_bert/violent_model.pickle", 'rb') as f:
        model = pickle.load(f)

api.add_resource(queryList, '/queries')
app.run(host='0.0.0.0', port=4996, debug=True)


