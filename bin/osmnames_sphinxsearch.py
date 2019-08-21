#!/usr/bin/env python3
import argparse
import json
import requests
from utils import write_to_json
from utils import load_from_json
from operator import itemgetter
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

def request(place_name):
    r = requests.get(url = "http://localhost:80/q/{0}.js".format(place_name))
    return r.json()["results"][0]

if __name__ == "__main__":
    args = get_args()
    data = load_from_json(args.data)
    token_labels = data["token_labels"]
    tokens=data["tokens"]
    places_token_in=[x for x,y in enumerate(token_labels) if "B-place"== y]
    geocoded_cities=[(x,request(x)) for x in itemgetter(*places_token_in)(tokens)]
    data["geocoded_cities"] = geocoded_cities

    write_to_json(data, data["id"], extension="json", out_dir=args.out_dir)
