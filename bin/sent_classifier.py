import argparse
import json
import requests
from utils import load_from_json
import os
import math
from shutil import copyfile
import re

def get_args():
    '''
    This function parses and return arguments passed in
    '''
    parser = argparse.ArgumentParser(prog='sent_classifier.py',
                                     description='Sentence FLASK BERT Classififer Application ')
    parser.add_argument('--out_dir', help="Output folder")
    parser.add_argument('--input_dir', help="Input folder")
    parser.add_argument('--data', help="Input JSON data")
    args = parser.parse_args()

    return(args)

def request(sentences):
    r = requests.post(url = "http://localhost:4999/queries", json={'sentences':sentences})
    return json.loads(r.text)

def request_violent(id,text):
    r = requests.post(url = "http://localhost:4996/queries", json={'identifier':id,'text':text})
    return json.loads(r.text)


if __name__ == "__main__":
    args = get_args()
    # TODO: Not sure if this removes only empty outputs from previous step. Need to test!
    args.data = re.sub(",( ,){1,}", ",", args.data) # In case of empty outputs from previous step
    args.data = re.sub("^\[, ", "[", args.data) # Empty at the start
    args.data = re.sub(" ,\]$", "]", args.data) # Empty at the end
    # TODO: Is there a better way to handle this?

    jsons=eval(args.data)

    rtext = request([" ".join([str(tok) for tok in d["sent_tokens"]]) for d in jsons])
    trigger_semantic_labels = rtext["trigger_sem"]
    participant_semantic_labels = rtext["part_sem"]
    organizer_semantic_labels = rtext["org_sem"]

    # TODO: If there is any need for sentence level classification,
    # we can do it here with gpu.

    out_text = "[SPLIT]".join([data["filename"] + ":" + str(data["sent_num"]) + ":" + str(trigger_semantic_labels[i]) + ":" + str(participant_semantic_labels[i]) + ":" + str(organizer_semantic_labels[i]) for i,data in enumerate(jsons)])
    print(out_text)
