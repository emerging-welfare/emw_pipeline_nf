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
    parser.add_argument('--do_coreference', help="Output folder", action="store_true",default=False)
    parser.add_argument('--out_dir', help="output folder")
    args = parser.parse_args()

    return(args)

def request(sentences, cascaded, all_pos_idxs, doc_ids):
    try:
        r = requests.post(url = "http://localhost:4998/queries", json={'sentences':sentences, 'cascaded':cascaded, 'all_pos_idxs':all_pos_idxs}, timeout=600) # 10 min timeout
        return json.loads(r.text)
    except requests.exceptions.Timeout as e:
        print("Timeout : %s" %doc_ids)
        data = {}
        data["tokens"] = ["Timeout" for s in sentences]
        data["output"] = ["Timeout" for s in sentences]
        data["flair_output"] = ["Timeout" for s in sentences]
        return data
    except:
        print("Error : %s" %doc_ids)
        data = {}
        data["tokens"] = ["Error" for s in sentences]
        data["output"] = ["Error" for s in sentences]
        data["flair_output"] = ["Error" for s in sentences]
        return data

def request_coreference(sentences, pos_sent_nums):
    r = requests.post(url = "http://localhost:4995/queries", json={'sentences':sentences,'sentence_no':pos_sent_nums})
    return json.loads(r.text)

if __name__ == "__main__":
    args = get_args()
    files=args.input_files.strip("[ ]").split(", ")
    jsons = []
    for filename in files:
        curr_json = read_from_json(filename)
        if curr_json.get("sent_labels", "") != "": # Some of the documents are not processed in sentence level (They have too many sentences)
            jsons.append(curr_json)

    if len(jsons)!=0: # TODO : why is this here?

        # Coreference
        if args.do_coreference:
            all_event_clusters = []
            for data in jsons:
                pos_sent_nums = [i for i,v in enumerate(data["sent_labels"]) if int(v) == 1]
                if len(pos_sent_nums) > 1: # If we have 0 or 1 pos sentence, we don't need to do coreference.
                    pos_sentences = [data["sentences"][idx] for idx in pos_sent_nums]
                    rtext_cor = request_coreference(pos_sentences, pos_sent_nums)
                    all_event_clusters.append(rtext_cor["event_clusters"])
                else:
                    all_event_clusters.append([])

        # if args.do_coreference:
        #     empties = []
        #     all_pos_sent_nums = []
        #     all_pos_sentences = []
        #     for i,data in enumerate(jsons):
        #         pos_sent_nums = [i for i,v in enumerate(data["sent_labels"]) if int(v) == 1]
        #         if len(pos_sent_nums) > 1: # If we have 0 or 1 pos sentence, we don't need to do coreference.
        #             all_pos_sent_nums.append(pos_sent_nums)
        #             pos_sentences = [data["sentences"][idx] for idx in pos_sent_nums]
        #             all_pos_sentences.append(pos_sentences)
        #         else:
        #             empties.append(i)

        #     if len(all_pos_sentences) > 0:
        #         rtext_cor = request_coreference(all_pos_sentences, all_pos_sent_nums)
        #         all_event_clusters = rtext_cor["event_clusters"]

        rtext = request(str([data["sentences"] for data in jsons]), args.cascaded, str([[i for i,sent_label in enumerate(data["sent_labels"]) if sent_label == 1] for data in jsons]), ", ".join([data["id"] for data in jsons]))
        all_tokens = rtext["tokens"]
        all_token_labels = rtext["output"]
        all_flair_outputs = rtext["flair_output"]
        # j = 0
        for i,data in enumerate(jsons):
            data["tokens"] = all_tokens[i]
            data["token_labels"] = all_token_labels[i]
            data["flair_output"] = all_flair_outputs[i]
            if args.do_coreference and all_event_clusters[i]:
                data["event_clusters"] = all_event_clusters[i]

            # if args.do_coreference and i not in empties:
            #     data["event_clusters"] = all_event_clusters[j]
            #     j += 1

            write_to_json(data, data["id"], extension="json", out_dir=args.out_dir)
