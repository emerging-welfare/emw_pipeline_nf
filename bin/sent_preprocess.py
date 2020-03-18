import argparse
import json
import os
from utils import dump_to_json
from utils import read_from_json
from pytorch_pretrained_bert.tokenization import BertTokenizer

def get_args():
    '''
    This function parses and return arguments passed in
    '''
    parser = argparse.ArgumentParser(prog='sent_preprocess.py',
                                     description='Sentence Preprocess')
    parser.add_argument('--input_file', help="Input file")
    parser.add_argument('--out_dir', help="output folder")
    args = parser.parse_args()

    return(args)


def convert_text_to_features(text, max_seq_length, tokenizer):
    tokens = tokenizer.tokenize(text)
    if len(tokens) > max_seq_length - 2:
        tokens = tokens[0:(max_seq_length - 2)]

    tokens = ["[CLS]"] + tokens + ["[SEP]"]
    input_ids = tokenizer.convert_tokens_to_ids(tokens)
    return input_ids

if __name__ == "__main__":
    args = get_args()
    # filename = eval(args.input_file)
    json_data=read_from_json(args.input_file)
    # if json_data=="":continue

    max_seq_length = 128
    HOME=os.getenv("HOME")
    bert_vocab = HOME+ "/.pytorch_pretrained_bert/bert-base-uncased-vocab.txt"
    tokenizer = BertTokenizer.from_pretrained(bert_vocab)

    # TODO : check for empty json data or no keys
    sent_tokens = []
    for sent in json_data["sentences"]:
        sent_tokens.append(convert_text_to_features(sent, max_seq_length, tokenizer))

    print("[SPLIT]".join([dump_to_json({"filename":args.input_file, "sent_num":i, "sent_tokens":sent_tokens[i]}) for i in range(len(sent_tokens))]))
