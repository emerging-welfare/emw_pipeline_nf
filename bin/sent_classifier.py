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
    parser = argparse.ArgumentParser(prog='sent_classifier.py',
                                     description='Sentence FLASK BERT Classififer Application ')
    parser.add_argument('--data', help="Serialized json string")
    args = parser.parse_args()

    return(args)

def request(id,sentences):
    r = requests.post(url = "http://localhost:4999/queries", json={'identifier':id,'sentences':sentences})
    return json.loads(r.text)

if __name__ == "__main__":
    args = get_args()
    data = load_from_json(args.data)

    # What to do when there is no positive sentence? This is more urgent in token level predictions where we filter out predicted tokens if they are not in a positive sentence.
    rtext = request(data["id"], data["sentences"])
    data["sent_labels"] = [int(i) for i in rtext["output"]]

    print(dump_to_json(data))
