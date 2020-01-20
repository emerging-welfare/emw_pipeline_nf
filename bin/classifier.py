#Abdurrahman Beyaz. abdurrahmanbeyaza@gmail.com
"""
This class is an individual version of classifier_batch
"""
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
    parser = argparse.ArgumentParser(prog='classifier.py',
                                     description='Document FLASK SVM Classififer Application ')
    parser.add_argument('--data', help="Serialized json string")
    parser.add_argument('--out_dir', help="output folder")
    args = parser.parse_args()

    return(args)

def request(id,text):
    r = requests.post(url = "http://localhost:5000/queries", data = {'identifier':id,'text':text},json={"Content-Type":"application/json"})
    return json.loads(r.text)

if __name__ == "__main__":
    args = get_args()
    data = load_from_json(args.data)

    rtext = request(id=data["id"], text=data["text"])
    data["doc_label"] = int(rtext["output"])
    data["length"] = len(data["text"])

    if data["doc_label"] == 0:
        write_to_json(data, data["id"], extension="json", out_dir=args.out_dir)
    else:
        data["sentences"] = rtext["event_sentences"]

    print(dump_to_json(data, add_label=True))
