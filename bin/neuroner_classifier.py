import argparse
import json
import requests
from utils import write_to_json
from utils import load_from_json

def get_args():
    '''
    This function parses and return arguments passed in
    '''
    parser = argparse.ArgumentParser(prog='neuroner_classifier.py',
                                     description='Extract information text using FLASK neuroner Application ')
    parser.add_argument('--data', help="Serialized json string")
    parser.add_argument('--out_dir', help="output folder")
    args = parser.parse_args()

    return(args)

def request(text):
    r = requests.post(url = "http://localhost:4996/queries", json = {'tokens':text})
    return json.loads(r.text)

if __name__ == "__main__":
    args = get_args()
    data = load_from_json(args.data)

    # text = "\n".join(data["tokens"])
    # rtext = request(text)

    rtext = request(data["tokens"])
    data["token_labels"] = rtext["output"]
    write_to_json(data, data["id"], extension="json", out_dir=args.out_dir)
