#!/usr/bin/env python3
import os
import numpy
from pathlib import Path
import pickle
# from sklearn.linear_model import SGDClassifier
# from sklearn.base import BaseEstimator, TransformerMixin
import torch
from transformers import AutoModel, AutoTokenizer
import argparse

# Import the framework
import flask
from flask_restful import Resource, Api
# Create an instance of Flask
app = flask.Flask(__name__)

# Create the API
api = Api(app)

@app.route("/")
def index():
    return "<html><body><p>classifier is loaded</p></body></html>"

def get_args():
    '''
    This function parses and return arguments passed in
    '''
    parser = argparse.ArgumentParser(prog='classifier_flask.py',
                                     description='Flask Server for Document Classification')
    parser.add_argument('--gpu_number_violent', help="Insert the gpu number for violent classification",default='0,1,2,3,4,5,6,7')
    parser.add_argument('--language', help="Source language. Ex: english")

    args = parser.parse_args()
    return(args)

def model_predict(encoder, classifier, texts, max_length):
    encoded_input = tokenizer(texts, padding="max_length", truncation=True,
                              max_length=max_length, return_tensors="pt")
    input_ids = encoded_input["input_ids"].to(violent_device)
    input_mask = encoded_input["attention_mask"].to(violent_device)

    embeddings = encoder(input_ids, attention_mask=input_mask)[1]
    out = classifier(embeddings)

    all_preds = torch.sigmoid(out).detach().cpu().numpy().flatten()
    all_preds = [idx_to_label[int(x >= 0.5)] for x in all_preds]

    return all_preds

class queryList(Resource):
    def post(self):
        data = flask.request.get_json(force=True)

        all_preds = model_predict(encoder, classifier, data["texts"], max_seq_length)

        out = {}
        out["violent_output"] = all_preds

        if args.language == "english":
            rural_pred = rural_model.predict(data["texts"])[0]
            if rural_pred == 1:
                out["urbanrural"] = "rural"
            else:
                out["urbanrural"] = "urban"

        return out

HOME = os.getenv("HOME")
args=get_args()

# Load violent model
idx_to_label = ["non-violent", "violent"]
max_seq_length = 512
pretrained_transformers_model = "xlm-roberta-base"
tokenizer = AutoTokenizer.from_pretrained(pretrained_transformers_model)
encoder = AutoModel.from_pretrained(pretrained_transformers_model)
classifier = torch.nn.Linear(encoder.config.hidden_size, 1)

gpu_range = args.gpu_number_violent.split(",")
violent_device = torch.device("cuda:{}".format(int(gpu_range[0])))
classifier.load_state_dict(torch.load(HOME+"/.pytorch_pretrained_bert/multilingual_violent_classifier.pt"))
classifier.to(violent_device)
encoder.load_state_dict(torch.load(HOME+"/.pytorch_pretrained_bert/multilingual_violent_encoder.pt"))
encoder.to(violent_device)
if len(gpu_range) >= 2:
    device_ids = [int(x) for x in gpu_range]
    encoder = torch.nn.DataParallel(encoder, device_ids=device_ids)

encoder.eval()
classifier.eval()


# Load rural model
if args.language == "english":
    with open(HOME+"/.pytorch_pretrained_bert/rural_model.pickle", 'rb') as f:
        rural_model = pickle.load(f)

api.add_resource(queryList, '/queries')
app.run(host='0.0.0.0', port=4996, debug=False)
