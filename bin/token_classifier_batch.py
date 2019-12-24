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
    parser.add_argument('--data', help="Serialized json string")
    parser.add_argument('--out_dir', help="output folder")
    args = parser.parse_args()

    return(args)

def request(sentences):
    r = requests.post(url = "http://localhost:4998/queries", json={'sentences':sentences})
    return json.loads(r.text)

if __name__ == "__main__":
    args = get_args()
    #if sentence classifier output was provided as an argumenet
    #jsons = eval(re.sub(r"\[QUOTE\]", r"'", args.data).replace("\'",""))
    # args.data=re.sub(r"\[QUOTE\]", r"'", args.data).replace("\'","").strip().strip()
    # args.data=re.sub(r"^\[.*\{","[{",args.data)
    # args.data=re.sub(r"\}\n?.*\n?\{","},{",args.data) 
    # jsons=eval(re.sub(r"\}\n?.*\n?\]","}]",args.data))
    
    #if sentence classifier output was provided as files name
    files=args.data.strip("[ ]").split(",") 
    jsons = []
    for filename in files:
        filename=filename.strip("' \n")
        if filename=="":continue ##
        jsons.append(read_from_json(filename))
    if len(jsons)!=0:
        rtext = request(str([data["sentences"] for data in jsons]))
        all_tokens = rtext["tokens"]
        all_token_labels = rtext["output"]
        for i,data in enumerate(jsons):
            data["tokens"] = all_tokens[i]
            data["token_labels"] = all_token_labels[i]
            write_to_json(data, data["id"], extension="json", out_dir=args.out_dir)
            #print('"' + change_extension(data["id"], ex=".json") + '"')
            #print(data["id"].replace(".html",".json.json"))
  
