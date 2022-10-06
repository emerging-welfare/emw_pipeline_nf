#!/usr/bin/env python3
import os
import numpy
from pathlib import Path
# import pickle
# from sklearn.linear_model import SGDClassifier
# from sklearn.base import BaseEstimator, TransformerMixin
import torch
from transformers import AutoModel, AutoTokenizer

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

def model_predict(encoder, classifier, texts, max_length):
    encoded_input = tokenizer(texts, padding="max_length", truncation=True,
                              max_length=max_length, return_tensors="pt")
    input_ids = encoded_input["input_ids"].to(device)
    input_mask = encoded_input["attention_mask"].to(device)

    embeddings = encoder(input_ids, attention_mask=input_mask)[1]
    out = classifier(embeddings)

    all_preds = torch.sigmoid(out).detach().cpu().numpy().flatten()
    all_preds = [idx_to_label[int(x >= 0.5)] for x in all_preds]

    return all_preds

class queryList(Resource):
    def post(self):
        args = flask.request.get_json(force=True)

        all_preds = model_predict(encoder, classifier, args["texts"], max_seq_length)

        out = {}
        out["violent_output"] = all_preds

        # rural_pred = rural_model.predict(args["text"])[0]
        # if rural_pred == 1:
        #     out["urbanrural"] = "rural"
        # else:
        #     out["urbanrural"] = "urban"

        return out

HOME = os.getenv("HOME")

# Load violent model
idx_to_label = ["non-violent", "violent"]
max_seq_length = 512
device_ids = [0,1,2,3,4,5,6,7]
device = torch.device("cuda:0")
pretrained_transformers_model = "xlm-roberta-base"
tokenizer = AutoTokenizer.from_pretrained(pretrained_transformers_model)
encoder = AutoModel.from_pretrained(pretrained_transformers_model)
classifier = torch.nn.Linear(encoder.config.hidden_size, 1)

classifier.load_state_dict(torch.load(HOME+"/.pytorch_pretrained_bert/multilingual_violent_classifier.pt"))
classifier.to(device)
encoder.load_state_dict(torch.load(HOME+"/.pytorch_pretrained_bert/multilingual_violent_encoder.pt"))
encoder.to(device)
if torch.cuda.device_count() > 1 and device.type == "cuda":
    encoder = torch.nn.DataParallel(encoder, device_ids=device_ids)

encoder.eval()
classifier.eval()


# Load rural model
# global rural_model
# with open(HOME+"/.pytorch_pretrained_bert/rural_model.pickle", 'rb') as f:
#     rural_model = pickle.load(f)

api.add_resource(queryList, '/queries')
app.run(host='0.0.0.0', port=4996, debug=False)
