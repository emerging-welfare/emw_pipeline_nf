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
    parser.add_argument('--out_dir', help="output folder")
    parser.add_argument('--data', help="Serialized json string")
    parser.add_argument('--cascaded', help="enable cascaded version" ,action="store_true",default=False)
    args = parser.parse_args()

    return(args)

def request(sentences):
    r = requests.post(url = "http://localhost:4999/queries", json={'sentences':sentences})
    return json.loads(r.text)

def request_violent(id,text):
    r = requests.post(url = "http://localhost:4996/queries", json={'identifier':id,'text':text})
    return json.loads(r.text)

def request_coreference(sentences, pos_sent_nums):
    r = requests.post(url = "http://localhost:4995/queries", json={'sentences':sentences,'sentence_no':pos_sent_nums})
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
        data["sent_labels"] = [int(i) for i in rtext["output_protest"]]
        data["Trigger_Semantic_label"]=rtext["output_sem"]
        data["participant_semantic"]=rtext["partic_sem"]
        data["organizer_semantic"]=rtext["org_sem"]

        # Coreference
        pos_sent_nums = [i for i,v in enumerate(data["sent_labels"]) if v == 1]
        if len(pos_sent_nums) > 1: # If we have 0 or 1 pos sentence, we don't need to do coreference.
            pos_sentences = [data["sentences"][idx] for idx in pos_sent_nums]
            rtext_cor = request_coreference(pos_sentences, pos_sent_nums)
            data["event_clusters"] = rtext_cor["event_clusters"]

    is_violent=request_violent(data["id"],data["text"])
    data["is_violent"]= is_violent if is_violent else "0"
    write_to_json(data, data["id"], extension="json", out_dir=args.out_dir)
    if (1 in data["sent_labels"] and args.cascaded) or (not args.cascaded):
        print(args.out_dir+change_extension(data["id"],".json"))
