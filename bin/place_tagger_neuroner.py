import argparse
import json
import requests
from utils import write_to_json
from utils import dump_to_json
from utils import load_from_json

def get_args():
    '''
    This function parses and return arguments passed in
    '''
    parser = argparse.ArgumentParser(prog='placeTaggerN.py',
                                     description='Extract place names from a text using FLASK neuroner Application ')
    parser.add_argument('--data', help="Serialized json string")
    parser.add_argument('--out_dir', help="output folder")
    args = parser.parse_args()

    return(args)

def request(id,text):
    r = requests.post(url = "http://localhost:4997/queries", data = {'text':text},json={"Content-Type":"application/json"})
    return json.loads(r.text)

if __name__ == "__main__":
    args = get_args()
    data = load_from_json(args.data)
    rtext = request(text=data["text"])
    data["places"]=[x for x in rtext if x["type"]=="place"]

    # write_to_json(data, data["id"], extension="json", out_dir=args.out_dir)

    # print(dump_to_json(data, add_label=True))
