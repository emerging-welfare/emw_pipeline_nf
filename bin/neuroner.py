import argparse
import json
import requests
from utils import write_to_json
from utils import load_from_json

def get_args():
    '''
    This function parses and return arguments passed in
    '''
    parser = argparse.ArgumentParser(prog='neuroner.py',
                                     description='Extract information text using FLASK neuroner Application ')
    parser.add_argument('--data', help="Serialized json string")
    parser.add_argument('--out_dir', help="output folder")
    args = parser.parse_args()

    return(args)

def postprocess(data):
    all_tokens = []
    # sent_count = 0
    all_trigger_labels = []
    all_token_labels = []
    for i, token in enumerate(data["tokens"]):
        if token == "SAMPLE_START":
            trigger_labels = []
            token_labels = []
            tokens = []
        elif token == "[SEP]":
            all_tokens.append(tokens)
            # if data["sent_labels"][sent_count] == 0: # If sentence's label is 0, ignore all predicted tokens and reset them to 'O' tag.
            #     trigger_labels = ["O"] * len(trigger_labels)
            #     token_labels = ["O"] * len(token_labels)

            all_trigger_labels.append(trigger_labels)
            all_token_labels.append(token_labels)
            sent_count += 1
            trigger_labels = []
            token_labels = []
            tokens = []
        elif token == "":
            all_tokens.append(tokens)
            # if data["sent_labels"][sent_count] == 0: # If sentence's label is 0, ignore all predicted tokens and reset them to 'O' tag.
            #     trigger_labels = ["O"] * len(trigger_labels)
            #     token_labels = ["O"] * len(token_labels)

            all_trigger_labels.append(trigger_labels)
            all_token_labels.append(token_labels)
            trigger_labels = []
            token_labels = []
            tokens = []
        else:
            tokens.append(token)
            if data["trigger_labels"][i] != "O":
                trigger_labels.append(data["trigger_labels"][i])
            elif data["token_labels"][i] != "O":
                token_labels.append(data["token_labels"][i])

    data["trigger_labels"] = all_trigger_labels
    data["token_labels"] = all_token_labels
    data["tokens"] = all_tokens
    return data

def request(text):
    r = requests.post(url = "http://localhost:4996/queries", json = {'tokens':text})
    return json.loads(r.text)

if __name__ == "__main__":
    args = get_args()
    data = load_from_json(args.data)

    # text = "\n".join(data["tokens"])
    # rtext = request(text)

    rtext = request(data["tokens"])
    data["token_labels"] = rtext["output"]
    data = postprocess(data)
    write_to_json(data, data["id"], extension="json", out_dir=args.out_dir)
