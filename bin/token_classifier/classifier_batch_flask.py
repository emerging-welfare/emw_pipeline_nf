import os
import numpy
from pathlib import Path
import torch
from nltk import word_tokenize
import argparse

# TODO : Should use a fork of flair that contains only the parts we need.
import flair

import pytorch_pretrained_bert as fork_bert

# Import the framework
from flask import Flask, g
from flask_restful import Resource, Api, reqparse
# Create an instance of Flask
app = Flask(__name__)
import json
# Create the API
api = Api(app)

PYTORCH_PRETRAINED_BERT_CACHE = Path(os.getenv('PYTORCH_PRETRAINED_BERT_CACHE',
                                               Path.home() / '.pytorch_pretrained_bert'))

@app.route("/")
def index():
    # Open the README file
    #with open(os.path.dirname(app.root_path) + '/README.md', 'r') as markdown_file:
    # Read the content of the file
    #content = str("\n ".join(main(file)))

    # Convert to HTML
    if classifer is not None :
        # return markdown.markdown("classifier is loaded")
        return "<html><body><p>classifier is loaded</p></body></html>"
    else :
        return "<html><body><p>classifier is not loaded</p></body></html>"
        # return markdown.markdown("classifier is not loaded")

def prepare_input(lines, tokenization_fix=False):
    # examples = []
    words = []
    for (i, line) in enumerate(lines):
        line = line.strip()
        if line == "SAMPLE_START":
            words.append("[CLS]")
        elif line in ["[SEP]", "\x91", "\x92", "\x97"]:
            continue
        else:
            words.append(line)

    # NOTE : As you see the things we mask with input_mask are just "[PAD]" tokens, the rest of the tokens are used in throughout BERT,
    # with the sole exception that some of them ([CLS], [SEP] and extra subword tokens) do not get evaluated at the end.
    # This is where labeling mask comes into play.
    tokens = []
    labeling_mask = []
    for (j, word) in enumerate(words):
        if word == "[CLS]":
            tokens.append("[CLS]")
            labeling_mask.append(0)
            continue

        tokenized = tokenizer.tokenize(word)

        if not tokenization_fix: # in this case labeling_mask = input_mask - CLS and SEP token
            labeling_mask.append(1)
            if len(tokenized) > 0:
                tokens.append(tokenized[0])
            else:
                tokens.append("[UNK]")

        else:
            # If we want to keep all wordpieces
            labeling_mask.append(1)
            if len(tokenized) == 1:
                tokens.extend(tokenized)
            elif len(tokenized) > 1:
                tokens.extend(tokenized)
                labeling_mask.extend([0]*(len(tokenized) - 1))
            else:
                tokens.append("[UNK]")

    if len(tokens) > max_seq_length - 1:
        tokens = tokens[0:(max_seq_length - 1)]
        labeling_mask = labeling_mask[0:(max_seq_length - 1)]

    tokens.append("[SEP]") # For BERT
    labeling_mask.append(0)
    tokens = tokenizer.convert_tokens_to_ids(tokens)

    segment_ids = [0] * len(tokens)
    input_mask = [1] * len(tokens)

    while len(tokens) < max_seq_length:
        tokens.append(0)
        segment_ids.append(0)
        input_mask.append(0)
        labeling_mask.append(0)

    return tokens, input_mask, segment_ids, labeling_mask

def get_args():
    '''
    This function parses and return arguments passed in
    '''
    parser = argparse.ArgumentParser(prog='classifier_flask.py',
                                     description='Flask Server for Token  Classification')
    parser.add_argument('--gpu_number', help="Insert the gpu count/number , if more than gpu will be allocated please use the following format 0,1,2,5, where 0,1,2,5 gpus will be allocated.\n or just type the number of required gpu, i.e 2 ",default='2')
    parser.add_argument('--gpu_number_place', help="Insert the gpu count/number. This model only does not work with multiple gpus.",default='7')
    args = parser.parse_args()

    return(args)


def predict(all_tokens, tokenization_fix=True): # For token models before 2020-02-21 use tokenization_fix=False
    all_input_ids = list()
    all_input_mask = list()
    all_segment_ids = list()
    all_labeling_mask = list()
    for tokens in all_tokens:
        input_ids, input_mask, segment_ids, labeling_mask = prepare_input(tokens, tokenization_fix=tokenization_fix)

        input_ids = torch.tensor(input_ids, dtype=torch.long).unsqueeze(0)
        input_mask = torch.tensor(input_mask, dtype=torch.long).unsqueeze(0)
        segment_ids = torch.tensor(segment_ids, dtype=torch.long).unsqueeze(0)

        all_input_ids.append(input_ids)
        all_input_mask.append(input_mask)
        all_segment_ids.append(segment_ids)
        all_labeling_mask.append(labeling_mask)

    all_input_ids = torch.cat(all_input_ids, dim=0).to(device)
    all_input_mask = torch.cat(all_input_mask, dim=0).to(device)
    all_segment_ids = torch.cat(all_segment_ids, dim=0).to(device)
    all_labeling_mask = numpy.array(all_labeling_mask)

    logits = model(all_input_ids, all_segment_ids, all_input_mask)
    logits = logits.detach().cpu().numpy()
    temp_labels = numpy.argmax(logits, axis=-1)

    all_labels = []
    for i in range(len(all_tokens)):
        tokens = all_tokens[i]
        labels = temp_labels[i,:]
        labeling_mask = all_labeling_mask[i,:]
        labels = labels[labeling_mask != 0] # remove CLS, all extra subwords, SEP and PAD tokens

        new_labels = []
        j = 0
        for line in tokens:
            line = line.strip()
            if line == "SAMPLE_START":
                new_labels.append("O")
            elif line in ["[SEP]", "\x91", "\x92", "\x97"]:
                new_labels.append("O")
            else:
                if j < len(labels): # since we have this many labels predicted
                    new_labels.append(label_map[labels[j]])
                    j += 1

                # NOTE : if we cut sequences longer than max_seq_length, since we don't have predictions for the tokens
                # after 510, we have to assign them "O" label.
                # TODO : Implement chunking to mitigate this problem. Divide document to smaller, preferably overlapping chunks,
                # use some voting mechanism to combine predicted token labels for the whole sequence.
                else:
                    new_labels.append("O")

        all_labels.append(new_labels)

    return all_labels

def get_chunks(sentences):
    tokenized_sentences = []
    for sentence in sentences:
        words = word_tokenize(sentence)
        tokenized_sentences.append(words)

    chunks, chunk = [], ['SAMPLE_START', ]
    for i, s in enumerate(tokenized_sentences):
        if (len(chunk) + 1 + len(s)) >= max_seq_length: # +1 for [SEP] token
            chunks.append(chunk)
            chunk = ['SAMPLE_START', ] + s
        else:
            if i == 0:
                chunk += s
            else:
                chunk += ['[SEP]', ] + s
    chunks.append(chunk)

    return chunks, tokenized_sentences


class queryList(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('sentences', required=True)
        parser.add_argument('tokens', required=False)
        parser.add_argument('output', required=False)
        parser.add_argument('flair_output', required=False)
        args = parser.parse_args()

        args["sentences"] = eval(args["sentences"])
        # args["sentences"] is a list of documents, which each are a list of sentences
        batchsize = len(args["sentences"])

        all_docs_tokenized = [] # list of list of list of tokens
        chunk_tokens, chunk_sizes = [], []
        for sentences in args["sentences"]:
            chunks, tokenized_sentences = get_chunks(sentences)
            all_docs_tokenized.append(tokenized_sentences)
            chunk_sizes.append(len(chunks))
            chunk_tokens += chunks

        chunk_output = []
        for i in range(0, len(chunk_tokens), batchsize):
            chunk_output += predict(chunk_tokens[i:i+batchsize])

        i = 0
        output = []
        tokens = []
        for s in chunk_sizes:
            output.append(sum(chunk_output[i:i+s], []))
            tokens.append(sum(chunk_tokens[i:i+s], []))
            i += s

        # Place Tagger
        # TODO : Too slow! Maybe move to GPU.
        place_output = []
        for tokenized_sentences in all_docs_tokenized:
            doc_sents = [flair.data.Sentence(" ".join(sent_tokens)) for sent_tokens in tokenized_sentences]
            doc_sents = place_tagger.predict(doc_sents) # Don't know if tagger actually does batching here!

            curr_place_tags = []
            for sent_id, sent in enumerate(doc_sents):
                for span in sent.get_spans("ner"):
                    if span.tag == "LOC":
                        # Ids are 1-indexed for some reason
                        idxs = sorted([tok.idx - 1 for tok in span.tokens])
                        curr_place_tags.append((sent_id, idxs[0], idxs[-1])) # tuple of sent_id, start_idx of span, end_idx of span

            place_output.append(curr_place_tags)

        args["tokens"] = tokens
        args["output"] = output
        args["flair_output"] = place_output

        return args, 201

max_seq_length = 512
HOME=os.getenv("HOME")
model_path = HOME +  "/.pytorch_pretrained_bert/token_model.pt"
bert_model = HOME +  "/.pytorch_pretrained_bert/bert-base-uncased.tar.gz"
bert_vocab = HOME +  "/.pytorch_pretrained_bert/bert-base-uncased-vocab.txt"
FLAIR_CACHE_ROOT = HOME +  "/.pytorch_pretrained_bert"

#device = torch.device("cuda:7")

tokenizer = fork_bert.tokenization.BertTokenizer.from_pretrained(bert_vocab)
label_list = ["B-etime", "B-fname", "B-organizer", "B-participant", "B-place", "B-target", "B-trigger", "I-etime", "I-fname", "I-organizer", "I-participant", "I-place", "I-target", "I-trigger", "O"]
label_map = {}
for (i, label) in enumerate(label_list):
    label_map[i] = label

model = fork_bert.modeling.BertForTokenClassification.from_pretrained(bert_model, PYTORCH_PRETRAINED_BERT_CACHE, num_labels=len(label_list))

if torch.cuda.is_available():
    model.load_state_dict(torch.load(model_path))
else:
    model.load_state_dict(torch.load(model_path, map_location='cpu'))

args=get_args()
gpu_range=args.gpu_number.split(",")
if len(gpu_range)==1:
    device=torch.device("cuda:{0}".format(int(gpu_range[0])))
elif len(gpu_range)>=2:
             device_ids= [int(x) for x in gpu_range]
             device=torch.device("cuda:{0}".format(int(device_ids[0])))
             model = torch.nn.DataParallel(model,device_ids=device_ids,output_device=device, dim=0)

model.to(device)
model.eval()

# Flair model for place names
if args.gpu_number_place == "cpu":
    flair.device = torch.device("cpu") # Default one is cuda:0
else:
    flair.device = torch.device("cuda:" + args.gpu_number_place)

flair.cache_root = FLAIR_CACHE_ROOT
place_tagger = flair.models.SequenceTagger.load("ner")
place_tagger.eval()

api.add_resource(queryList, '/queries')
app.run(host='0.0.0.0', port=4998)
