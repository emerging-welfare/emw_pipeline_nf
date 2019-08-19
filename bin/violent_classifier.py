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
    parser = argparse.ArgumentParser(prog='violent_classifier.py',
                                     description='Violent FLASK Classififer Application ')
    parser.add_argument('--data', help="Serialized json string")
    parser.add_argument('--out_dir', help="Output folder")
    args = parser.parse_args()

    return(args)

def request(text):
    r = requests.post(url = "http://localhost:4996/queries", json={'text':text})
    return json.loads(r.text)

if __name__ == "__main__":
    args = get_args()
    data = load_from_json(args.data)

    rtext = request(data["text"])
    data["is_violent"] = rtext["is_violent"]

    write_to_json(data, data["id"], extension="json", out_dir=args.out_dir)
