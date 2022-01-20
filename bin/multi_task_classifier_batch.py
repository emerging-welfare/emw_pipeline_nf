import argparse
import json
import requests
import re
from utils import write_to_json
from utils import dump_to_json
from utils import read_from_json
from utils import change_extension
import os.path

def get_args():
    '''
    This function parses and return arguments passed in
    '''
    parser = argparse.ArgumentParser(prog='classifier.py',
                                     description='Document FLASK SVM Classififer Application ')
    parser.add_argument('--input_files', help="Input file")
    parser.add_argument('--out_dir', help="output folder")
    parser.add_argument('--cascaded', help="enable cascaded version" ,action="store_true",default=False)
    parser.add_argument('--do_coreference', help="enable coreference" ,action="store_true",default=False)
    parser.add_argument('--max_num_sents', help="how many sentences are processed at once", default="200")
    parser.add_argument('--max_length', help="max length of sentences", default="128")
    args = parser.parse_args()

    return(args)

def request(texts, cascaded, max_length, max_num_sents):
    try:
        r = requests.post(url = "http://localhost:4994/queries",
                          json={'texts':texts,
                                'max_length':max_length,
                                'max_num_sents':max_num_sents,
                                'cascaded':cascaded},
                          timeout=600) # 10 min timeout
        return json.loads(r.text)
    except requests.exceptions.Timeout as e:
        print("Timeout")
        data = {}
        data["doc_preds"] = ["Timeout" for _ in texts]
        data["all_tokens"] = [["Timeout" for _ in sents] for sents in texts]
        data["token_preds"] = [["Timeout" for _ in sents] for sents in texts]
        data["sent_preds"] = [["Timeout" for _ in sents] for sents in texts]
        data["flair_output"] = [["Timeout" for _ in sents] for sents in texts]
        return data
    except:
        print("Error")
        data = {}
        data["doc_preds"] = ["Error" for _ in texts]
        data["all_tokens"] = [["Error" for _ in sents] for sents in texts]
        data["token_preds"] = [["Error" for _ in sents] for sents in texts]
        data["sent_preds"] = [["Error" for _ in sents] for sents in texts]
        data["flair_output"] = [["Error" for _ in sents] for sents in texts]
        return data

def request_coreference(sentences, pos_sent_nums):
    r = requests.post(url = "http://localhost:4995/queries", json={'sentences':sentences,'sentence_no':pos_sent_nums})
    return json.loads(r.text)

if __name__ == "__main__":
    args = get_args()
    files=args.input_files.strip("[ ]").split(", ")
    jsons = []
    for filename in files:
        if os.path.exists(filename):
            curr_json = read_from_json(filename)
            jsons.append(curr_json)

    if len(jsons) != 0:
        rtext = request([data["sentences"] for data in jsons], args.cascaded, args.max_length, args.max_num_sents)
        all_tokens = rtext["all_tokens"]
        token_preds = rtext["token_preds"]
        sent_preds = rtext["sent_preds"]
        doc_preds = rtext["doc_preds"]
        flair_output = rtext["flair_output"]

        output_data = []
        for i,data in enumerate(jsons):
            tokens = all_tokens[i]
            curr_token_preds = token_preds[i]
            curr_sent_preds = [int(pred) for pred in sent_preds[i]]
            curr_doc_pred = int(doc_preds[i])
            curr_flair_output = flair_output[i]

            data["doc_label"] = curr_doc_pred
            data["tokens"] = tokens
            data["token_labels"] = curr_token_preds
            data["sent_labels"] = curr_sent_preds

            # Coreference
            if args.do_coreference:
                event_clusters = []
                pos_sent_nums = [i for i,v in enumerate(data["sent_labels"]) if int(v) == 1]
                if len(pos_sent_nums) > 1: # If we have 0 or 1 pos sentence, we don't need to do coreference.
                    pos_sentences = [data["sentences"][idx]for idx in pos_sent_nums]
                    rtext_cor = request_coreference(pos_sentences, pos_sent_nums)
                    event_clusters = rtext_cor["event_clusters"]

                data["event_clusters"] = event_clusters

            write_to_json(data, data["id"], extension="json", out_dir=args.out_dir)
