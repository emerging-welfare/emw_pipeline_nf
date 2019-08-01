import argparse
import json
import requests
import re
from utils import dump_to_json
from utils import load_from_json

def get_args():
    '''
    This function parses and return arguments passed in
    '''
    parser = argparse.ArgumentParser(prog='trigger_classifier.py',
                                     description='Trigger FLASK BERT Classififer Application ')
    parser.add_argument('--data', help="Serialized json string")
    parser.add_argument('--out_dir', help="output folder")
    args = parser.parse_args()

    return(args)

def request(sentences):
    r = requests.post(url = "http://localhost:4998/queries", json={'sentences':sentences})
    return json.loads(r.text)

if __name__ == "__main__":
    args = get_args()

    json_data = re.findall(r'\{"[^\}]+?\]\}', args.data)
    jsons = []
    for data in json_data:
        data = load_from_json(data)
        jsons.append(data)

    rtext = request(str([data["sentences"] for data in jsons]))

    all_tokens = rtext["tokens"]
    all_trigger_labels = rtext["output"]

    output_data = list()
    for i,data in enumerate(jsons):
        data["tokens"] = all_tokens[i]
        data["trigger_labels"] = all_trigger_labels[i]
        output_data.append(dump_to_json(data))

    print(str(output_data))
