import argparse
import json
import requests
import re
from utils import write_to_json
from utils import dump_to_json
from utils import change_extension
from utils import read_from_json

def get_args():
    '''
    This function parses and return arguments passed in
    '''
    parser = argparse.ArgumentParser(prog='token_classifier_batch.py',
                                     description='Token FLASK BERT Classififer Application ')
    parser.add_argument('--input_files', help="Input files")
    parser.add_argument('--cascaded', help="enable cascaded version" ,action="store_true",default=False)
    parser.add_argument('--out_dir', help="output folder")
    args = parser.parse_args()

    return(args)

def request(sentences, cascaded, all_pos_idxs):
    r = requests.post(url = "http://localhost:4998/queries", json={'sentences':sentences, 'cascaded':cascaded, 'all_pos_idxs':all_pos_idxs})
    return json.loads(r.text)

if __name__ == "__main__":
    args = get_args()
    files=args.input_files.strip("[ ]").split(", ")
    jsons = []
    for filename in files:
        jsons.append(read_from_json(filename))

    if len(jsons)!=0: # TODO : why is this here?
        rtext = request(str([data["sentences"] for data in jsons]), args.cascaded, str([[i for i,sent_label in enumerate(data["sent_labels"]) if sent_label == 1] for data in jsons]))
        all_tokens = rtext["tokens"]
        all_token_labels = rtext["output"]
        all_flair_outputs = rtext["flair_output"]
        for i,data in enumerate(jsons):
            data["tokens"] = all_tokens[i]
            data["token_labels"] = all_token_labels[i]
            data["flair_output"] = all_flair_outputs[i]
            write_to_json(data, data["id"], extension="json", out_dir=args.out_dir)
            #print('"' + change_extension(data["id"], ex=".json") + '"')
            #print(data["id"].replace(".html",".json.json"))
