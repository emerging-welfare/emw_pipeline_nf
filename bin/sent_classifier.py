import argparse
import json
import requests
from utils import dump_to_json
#from utils import load_from_json
from utils import read_from_json
from utils import change_extension
from utils import write_to_json
def get_args():
    '''
    This function parses and return arguments passed in
    '''
    parser = argparse.ArgumentParser(prog='sent_classifier.py',
                                     description='Sentence FLASK BERT Classififer Application ')
    parser.add_argument('--data', help="Serialized json string")
    parser.add_argument('--out_dir', help="output folder")
    args = parser.parse_args()

    return(args)

def request(sentences):
    r = requests.post(url = "http://localhost:4999/queries", json={'sentences':sentences})
    return json.loads(r.text)

def request_violent(id,text):
    r = requests.post(url = "http://localhost:4996/queries", json={'identifier':id,'text':text})
    return json.loads(r.text)


if __name__ == "__main__":
    args = get_args()
#    data = load_from_json(args.data)
    data=read_from_json(args.data)
    if "sentences" not in data.keys():
        data["sentences"]=[]
        data["sent_labels"]=[]
    else:
        rtext = request(data["sentences"])
        data["sent_labels"] = [int(i) for i in rtext["output"]]
    is_violent=request_violent(data["id"],data["text"])
    data["is_violent"]= is_violent if is_violent else "0"
    if 1 in data["sent_labels"]:
        print(dump_to_json(data))
    else:
        write_to_json(data, data["id"], extension="json", out_dir=args.out_dir)
