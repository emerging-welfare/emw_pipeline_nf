import argparse
import json
import requests
from utils import load_from_json
import os
import math
from shutil import copyfile

def get_args():
    '''
    This function parses and return arguments passed in
    '''
    parser = argparse.ArgumentParser(prog='sent_classifier.py',
                                     description='Sentence FLASK BERT Classififer Application ')
    parser.add_argument('--out_dir', help="Output folder")
    parser.add_argument('--input_dir', help="Input folder")
    parser.add_argument('--data', help="Input JSON data")
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
    jsons=eval(args.data)

    rtext = request([" ".join([str(tok) for tok in d["sent_tokens"]]) for d in jsons])
    sent_labels = rtext["output_protest"] # [int(v) for v in rtext["output_protest"]]
    trigger_semantic_labels = rtext["trigger_sem"]
    participant_semantic_labels = rtext["part_sem"]
    organizer_semantic_labels = rtext["org_sem"]

    # TODO : When writing, since other sentences that belong to this document can be in some other batch, and we have 8 cpus and batches run concurrently, there might be some overlap??? -> Solved this for now, but need to test with bigger data.
    # TODO : for task parallelism part just return predictions, and then do this part in another process where all the things are gathered, so that we only write to file once.
    uniq_filenames = list(set([d["filename"] for d in jsons]))
    for filename in uniq_filenames:
        curr_jsons = [(i,d) for i,d in enumerate(jsons) if d["filename"] == filename]

        if not os.path.exists(args.out_dir + filename):
            copyfile(args.input_dir + filename, args.out_dir + filename)

        # TODO : This will blow if the original length is bigger than new length. (Maybe newly predicted labels are all smaller in length)
        # To solve this, we use integers only
        with open(args.out_dir + filename, "r+", encoding="utf-8") as f:
            json_data = json.loads(f.read())
            f.seek(0,0)
            for i,d in curr_jsons:
                json_data["sent_labels"][d["sent_num"]] = str(sent_labels[i])
                json_data["trigger_semantic"][d["sent_num"]] = str(trigger_semantic_labels[i])
                json_data["participant_semantic"][d["sent_num"]] = str(participant_semantic_labels[i])
                json_data["organizer_semantic"][d["sent_num"]] = str(organizer_semantic_labels[i])

            f.write(json.dumps(json_data) + "\n")

            # fd = os.open(args.input_dir + filename, os.O_RDWR)
            # try:
            #     json_data = json.loads(os.read(fd, 100000000).decode("utf-8"))
            #     for i,d in curr_jsons:
            #         json_data["sent_labels"][d["sent_num"]] = sent_labels[i]
            #         # json_data["trigger_semantic"][d["sent_num"]] = trigger_semantic_labels[i]
            #         # json_data["participant_semantic"][d["sent_num"]] = participant_semantic_labels[i]
            #         # json_data["organizer_semantic"][d["sent_num"]] = organizer_semantic_labels[i]

            #     out_text = json.dumps(json_data) + "\n"
            #     os.write(fd, out_text.encode("utf-8"))
            # except:
            #     pass

            # os.set_blocking(fd, False)
            # os.close(fd)
