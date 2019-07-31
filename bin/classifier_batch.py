import argparse
import json
import requests
import re
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

def request(texts):
    r = requests.post(url = "http://localhost:5000/queries", data = {'texts':texts},json={"Content-Type":"application/json"})
    return json.loads(r.text)

if __name__ == "__main__":
    args = get_args()

    json_data = re.findall(r"\{[^\}]+?\}", args.data)
    jsons = []
    for data in json_data:
        data = load_from_json(data)
        jsons.append(data)

    rtext = request([data["text"] for data in jsons])
    event_sentences = rtext["event_sentences"]
    output_data = []
    for i,data in enumerate(jsons):
        out = int(rtext["outputs"][i])
        data["doc_label"] = out
        data["length"] = len(data["text"])
        if out == 0:
            write_to_json(data, data["id"], extension="json", out_dir=args.out_dir)
        if out == 1:
            data["sentences"] = event_sentences.pop()
            output_data.append(dump_to_json(data))

    if len(output_data) == 0:
        print("N")
    else:
        print(str(output_data))
