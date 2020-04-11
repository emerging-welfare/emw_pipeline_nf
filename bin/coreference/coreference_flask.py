from torch.utils.data import TensorDataset, DataLoader, RandomSampler, SequentialSampler
from itertools import combinations
from flask_restful import Resource, Api, reqparse
from flask import Flask, g
from transformers import *
from torch import nn
from pathlib import Path
import numpy as np
import argparse
import torch
import json

app = Flask(__name__)
api = Api(app)

@app.route("/")
def index():
    if model is not None :
        return "<html><body><p>classifier is loaded</p></body></html>"
    else :
        return "<html><body><p>classifier is not loaded</p></body></html>"


def prepare_pair(s1, s2, max_length=256):
    """returns input_ids, attention_mask, token_type_ids for set of data ready in BERT/ALBERT format"""
    global tokenizer

    t = tokenizer.encode_plus(s1, 
                        text_pair=s2,
                        pad_to_max_length=True,
                        add_special_tokens=True,
                        max_length=max_length,
                        return_tensors='pt')
    
    if "token_type_ids" not in t: t["token_type_ids"] = torch.tensor([[1, 1]])

    return t["input_ids"], t["attention_mask"], t["token_type_ids"]


def prepare_set(_set):
    input_ids, attention_masks, token_type_ids = zip(*list(map(lambda p: prepare_pair(p[0], p[1], max_length=max_length), zip(_set[0], _set[1]))))

    input_ids = torch.stack(input_ids).squeeze(1)
    attention_masks = torch.stack(attention_masks).squeeze(1)
    token_type_ids = torch.stack(token_type_ids).squeeze(1)

    return input_ids, attention_masks, token_type_ids


def predict(self, test_set, batch_size=32):
    test_inputs, test_masks, test_type_ids = prepare_set(test_set)
    test_data = TensorDataset(test_inputs, test_masks, test_type_ids)
    test_sampler = SequentialSampler(test_data)
    test_dataloader = DataLoader(test_data, sampler=test_sampler, batch_size=batch_size)

    self.eval()
    with torch.no_grad(): 
        preds = []
        for batch in test_dataloader:
            b_input_ids, b_input_mask, b_token_type_ids = tuple(t.to(device) for t in batch)
            output = self(b_input_ids, 
            attention_mask=b_input_mask,
            token_type_ids=b_token_type_ids)
            logits = output[0].detach().cpu()
            preds += list(torch.nn.functional.softmax(logits, dim=1)[:, 1].numpy())

    return preds


def get_args():
    """
    This function parses and return arguments passed in
    """
    parser = argparse.ArgumentParser(prog='coreference_flask.py',
                                     description='Flask Server for Coreference Resolution')
    parser.add_argument('--gpu_number', help="Insert the gpu count/number , if more than gpu will be allocated please use the following format 0,1,2,5, where 0,1,2,5 gpus will be allocated.\n or just type the number of required gpu, i.e 2 ",default='2')
    parser.add_argument('--gpu_number_place', help="Insert the gpu count/number. This model only does not work with multiple gpus.",default='7')
    args = parser.parse_args()

    return(args)


def cluster(sentences, sentence_no):
    # ranking pairs
    combs = list(combinations(zip(sentences, sentence_no), 2))
    s1 = [ s1[0] for s1, _ in combs ]
    s2 = [ s2[0] for _, s2 in combs ]
    ids = [ (s1[1], s2[1]) for s1, s2 in combs ]

    logits = model.predict((s1,s2), batch_size=batch_size)
    preds = [ float(s >= threshold) for s in logits ]
    pairs = { p : { "logit":l, "label": s, "score": l} for p, l, s in zip(ids, logits, preds)  }

    # rescoring
    for s1, s2 in ids:
        for s in sentence_no:
            if s1 == s or s2 == s:
                continue
            p_s1_s = next(p for p in ids if set(p) == set((s1, s)) )               
            p_s2_s = next(p for p in ids if set(p) == set((s2, s)) )
            if pairs[p_s1_s]["label"] == 1 and pairs[p_s2_s]["label"] == 1:    
                pairs[(s1, s2)]["score"] += reward
            elif pairs[p_s1_s]["label"] != pairs[p_s2_s]["label"]:
                pairs[(s1, s2)]["score"] -= penalty

    clusters = { n: 0 for n in sentence_no }
    filtered_pairs = { k : v  for k, v in pairs.items() if v["score"] >= clustering_threshold }
    sorted_pairs = sorted(filtered_pairs, key=lambda x: (filtered_pairs[x]["score"], x[0] - x[1]), reverse=True)

    # clustering
    group_no = 0
    for s1, s2 in sorted_pairs:
        if clusters[s1] == clusters[s2] == 0:
            group_no += 1
            clusters[s1] = clusters[s2] = group_no
        elif clusters[s1] == 0:
            clusters[s1] = clusters[s2]
        else:
            clusters[s2] = clusters[s1]

    for s in sentence_no:
        if clusters[s] == 0:
            group_no += 1
            clusters[s] = group_no

    cluster_grouped = {}
    for k, v in clusters.items():
        if v in cluster_grouped:
            cluster_grouped[v].append(k)
        else:
            cluster_grouped[v] = [k, ]

    return list(cluster_grouped.values()) 


class queryList(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('sentences', required=True)
        parser.add_argument('sentence_no', required=True)
        parser.add_argument('event_clusters', required=False)
        args = parser.parse_args()

        args["sentences"] = eval(args["sentences"])
        args["sentence_no"] = eval(args["sentence_no"])

        event_clusters = []
        for sents, sent_nos in zip(args["sentences"], args["sentence_no"]):
            event_clusters.append(cluster(sents, sent_nos))
        
        args["event_clusters"] = event_clusters

        return args, 201


model_path = str(Path.home() / '.pytorch_pretrained_bert/albert-large-v2-coreference')
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForSequenceClassification.from_pretrained(model_path)

args = get_args()
gpu_range = args.gpu_number.split(",")
max_length = 256

# Parameters of the clustering algorithm, 
# these parameters were tuned on the development set. 
threshold = 0.5
reward = penalty = 0.1
clustering_threshold = 0.5

if len(gpu_range) == 1:
    batch_size = 32
    device = torch.device("cuda:{0}".format(int(gpu_range[0])))
elif len(gpu_range) >= 2:
    device_ids = [int(x) for x in gpu_range]
    batch_size = 32 * len(device_ids)
    device = torch.device("cuda:{0}".format(int(device_ids[0])))
    model = torch.nn.DataParallel(model, device_ids=device_ids)

model.to(device)
model.predict = predict.__get__(model)
model.eval()

api.add_resource(queryList, '/queries')
app.run(host='0.0.0.0', port=4997)