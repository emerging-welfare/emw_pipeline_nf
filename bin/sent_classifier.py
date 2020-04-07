import argparse
import json
import requests
from utils import load_from_json
import os
import math
from shutil import copyfile

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
    jsons=eval(args.data)

    rtext = request([" ".join([str(tok) for tok in d["sent_tokens"]]) for d in jsons])
    sent_labels = rtext["output_protest"]
    trigger_semantic_labels = rtext["trigger_sem"]
    participant_semantic_labels = rtext["part_sem"]
    organizer_semantic_labels = rtext["org_sem"]

    out_text = "[SPLIT]".join([data["filename"] + ":" + str(data["sent_num"]) + ":" + str(sent_labels[i]) + ":" + str(trigger_semantic_labels[i]) + ":" + str(participant_semantic_labels[i]) + ":" + str(organizer_semantic_labels[i]) for i,data in enumerate(jsons)])
    print(out_text)
