import argparse
import json
import requests
import re
from utils import write_to_json
from utils import dump_to_json

def get_args():
    '''
    This function parses and return arguments passed in
    '''
    parser = argparse.ArgumentParser(prog='classifier.py',
                                     description='Document FLASK SVM Classififer Application ')
    parser.add_argument('--input_files', help="Input file")
    parser.add_argument('--out_dir', help="output folder")
    args = parser.parse_args()

    return(args)

def request(texts):
    r = requests.post(url = "http://localhost:5000/queries", data = {'texts':texts},json={"Content-Type":"application/json"})
    return json.loads(r.text)

if __name__ == "__main__":
    args = get_args()
    # jsons = eval(re.sub(r"\[QUOTE\]", r"'", args.data))

    files = eval(args.input_files)

    jsons = []
    for filename in files:
        with open(args.out_dir + filename, "r", encoding="utf-8") as f:
            jsons.append(json.loads(f.read()))

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

    if len(output_data) > 0:
        print(str(output_data))
