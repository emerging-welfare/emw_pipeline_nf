#!/usr/bin/env python3
import json
import os,argparse
from sutime import SUTime
import requests
from utils import write_to_json
from utils import load_from_json

def get_args():
    '''
    This function parses and return arguments passed in
    '''
    parser = argparse.ArgumentParser(prog='temporalTagger.py',description='SUTime is a library for recognizing and normalizing time expressions. That is, it will convert next wednesday at 3pm to something like 2016-02-17T15:00 (depending on the assumed current reference time). ')
    parser.add_argument('--data', help="insert a vaild input ")
    args = parser.parse_args()
    return(args)

def request(id,eventSenteces):
    r = requests.post(url = "http://localhost:4999/tts", data = {'identifier':id,'eventSenteces':eventSenteces},json={"Content-Type":"application/json"})
    return json.loads(r.text)

if __name__ == '__main__':
    args = get_args()
    data = load_from_json(args.data)

    rtext = request(data["id"], data["event_sentences"])
    data["temporal_tags"] = rtext["temporaltaggers"]
    write_to_json(data, data["id"], extension="json")
