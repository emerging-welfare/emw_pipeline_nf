#!/usr/bin/env python3
import argparse
import json
import requests
from utils import write_to_json
from utils import load_from_json

def get_args():
    '''
    This function parses and return arguments passed in
    '''
    parser = argparse.ArgumentParser(prog='trigger_classifier.py',
                                     description='Trigger FLASK BERT Classififer Application ')
    parser.add_argument('--data', help="Serialized json string")
    parser.add_argument('--out_dir', help="Output folder")
    args = parser.parse_args()

    return(args)

def request(id,sentences):
    r = requests.post(url = "http://localhost:4998/queries", json={'identifier':id,'sentences':sentences})
    return json.loads(r.text)

if __name__ == "__main__":
    args = get_args()
    data = load_from_json(args.data)

    rtext = request(data["id"], data["sentences"])
    data["tokens"] = rtext["tokens"]
    data["trigger_labels"] = rtext["output"]

    write_to_json(data, data["id"], extension="json", out_dir=args.out_dir)
