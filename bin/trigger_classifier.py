#!/usr/bin/env python3
import argparse
import json
import requests
from utils import dump_to_json
from utils import load_from_json

def get_args():
    '''
    This function parses and return arguments passed in
    '''
    parser = argparse.ArgumentParser(prog='trigger_classifier.py',
                                     description='Trigger FLASK BERT Classififer Application ')
    parser.add_argument('--data', help="Serialized json string")
    args = parser.parse_args()

    return(args)

def request(id,sentences):
    r = requests.post(url = "http://localhost:4998/queries", json={'identifier':id,'sentences':sentences})
    return json.loads(r.text)

# If token classification is in one step, do this in the flask part. If not, do this in last process.
def postprocess(data):
    all_labels = []
    all_tokens = []
    sent_count = 0
    trigger_labels = data["trigger_labels"]
    for i, token in enumerate(data["tokens"]):
        if token == "SAMPLE_START":
            labels = []
            tokens = []
        elif token == "[SEP]":
            all_tokens.append(tokens)
            if data["sent_labels"][sent_count] == 0: # If sentence's label is 0, ignore all predicted tokens and reset them to 'O' tag.
                labels = ["O"] * len(labels)

            all_labels.append(labels)
            sent_count += 1
            labels = []
            tokens = []
        elif token == "":
            all_tokens.append(tokens)
            if data["sent_labels"][sent_count] == 0: # If sentence's label is 0, ignore all predicted tokens and reset them to 'O' tag.
                labels = ["O"] * len(labels)

            all_labels.append(labels)
            labels = []
            tokens = []
        else:
            tokens.append(token)
            labels.append(trigger_labels[i])

    data["trigger_labels"] = all_labels
    data["tokens"] = all_tokens
    return data

if __name__ == "__main__":
    args = get_args()
    data = load_from_json(args.data)

    rtext = request(data["id"], data["sentences"])
    data["tokens"] = rtext["tokens"]
    data["trigger_labels"] = rtext["output"]

    data = postprocess(data) # Check the note at the definition of this method
    print(dump_to_json(data))
