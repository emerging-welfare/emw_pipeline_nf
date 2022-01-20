import os
from nltk import sent_tokenize, word_tokenize
import numpy
import torch
from transformers import AutoTokenizer, XLMRobertaModel
import sys
import argparse
import flair
# Import the framework
from flask import Flask, g
from flask_restful import Resource, Api, reqparse
# Create an instance of Flask
app = Flask(__name__)

# Create the API
api = Api(app)

HOME=os.getenv("HOME")
# TODO: or just copy-paste ScopeIt model implementation
sys.path.append(HOME + "/ScopeIt/src/")
from model import ScopeIt

def prepare_tokens(texts, max_length=128):
    """returns input_ids, attention_mask, token_type_ids for set of data ready in BERT format"""
    global tokenizer

    t = tokenizer(texts, is_split_into_words=True, padding="max_length",
                  truncation=True, max_length=max_length, return_tensors="pt")

    if no_token_type:
        return t["input_ids"], t["attention_mask"]
    else:
        return t["input_ids"], t["attention_mask"], t["token_type_ids"]

# def model_predict2(embeddings, all_mock_token_labels, org_lengths, max_num_sents=50, max_length=128):
#     # These mock_token_labels must be in the json data before preprocess_data.py is applied. They can be all "O" labels with length the same as tokens before that script is applied.
#     all_token_preds = []
#     all_sent_preds = []
#     all_doc_preds = []
#     with torch.no_grad():
#         embeddings = embeddings.to(model_device)
#         token_out, sent_out, doc_out = model(embeddings)

#         token_out = token_out.view(BATCHSIZE, max_num_sents, max_length, -1)
#         token_preds = token_out.detach().cpu().numpy() # [BatchSize, Sentences, Seq_len, TokenLabels]
#         token_preds = numpy.argmax(token_preds, axis=3) # [BatchSize, Sentences, Seq_len]

#     doc_preds = torch.sigmoid(doc_out).detach().cpu().numpy()
#     sent_preds = torch.sigmoid(sent_out).detach().cpu().numpy()
#     for doc_num in range(BATCHSIZE):
#         all_sent_preds.append([int(x[0] >= 0.5) for x in sent_preds[doc_num].tolist()])
#         all_doc_preds.append(int(doc_preds[doc_num][0] >= 0.5))

#         doc_token_preds = []
#         curr_org_lengths = org_lengths[doc_num]
#         for sent_num in range(len(curr_org_lengths)): # For each sentence
#             curr_token_preds = token_preds[doc_num, sent_num, :]
#             tok_labs = all_mock_token_labels[doc_num, sent_num, :]
#             tok_preds = curr_token_preds[tok_labs != -1].tolist() # get rid of extra subwords, CLS, SEP, PAD

#             sent_org_length = curr_org_lengths[sent_num]
#             tok_preds.extend([14] * (sent_org_length - len(tok_preds))) # 14 is for "O" label
#             doc_token_preds.append(tok_preds)

#         all_token_preds.append(doc_token_preds)

#     return all_token_preds, all_sent_preds, all_doc_preds

# NOTE: Parallelize all of the model
# def predict2(inputs, max_length=128, max_num_sents=50):
#     org_sentence_lengths = []
#     tokenized_inputs = []
#     org_lengths = []
#     for text in inputs:
#         curr_sentences = sent_tokenize(text)
#         org_sentence_lengths.append(len(curr_sentences))
#         all_tokens = []
#         curr_org_lengths = []
#         for sent in curr_sentences:
#             curr_tokens = word_tokenize(sent)
#             all_tokens.append(curr_tokens)
#             curr_org_lengths.append(len(curr_tokens))

#         tokenized_inputs.append(all_tokens)
#         org_lengths.append(curr_org_lengths)

#     to_be_processed = []
#     for doc in tokenized_inputs:
#         if len(doc) > max_num_sents: # truncate sentences
#             doc = doc[:max_num_sents]
#         else: # pad sentences
#             # TODO: Decide if this would effect the second GRU output!!!
#             doc.extend([["<pad>"]] * (max_num_sents-len(doc)))

#         for sent in doc:
#             to_be_processed.append(sent)

#     # get input
#     to_be_processed = tokenize_and_align_labels(to_be_processed, max_length=max_length)
#     input_ids = to_be_processed["input_ids"]
#     input_masks = to_be_processed["attention_mask"]
#     mock_labels = torch.LongTensor(to_be_processed["mock_labels"]).view(BATCHSIZE, max_num_sents, max_length).numpy()
#     if not no_token_type:
#         token_type_ids = to_be_processed["token_type_ids"].to(bert_device)

#     input_ids = input_ids.to(bert_device)
#     input_masks = input_masks.to(bert_device)
#     with torch.no_grad():
#         if no_token_type:
#             embeddings = bert(input_ids, attention_mask=input_masks)[0]
#         else:
#             embeddings = bert(input_ids, attention_mask=input_masks,
#                               token_type_ids=token_type_ids)[0]

#     all_token_preds, all_sent_preds, all_doc_preds = model_predict(embeddings.view(BATCHSIZE, max_num_sents, max_length, -1),
#                                                                       mock_labels,
#                                                                       org_lengths,
#                                                                       max_num_sents=max_num_sents,
#                                                                       max_length=max_length)


#     return tokenized_inputs, all_token_preds, all_sent_preds, all_doc_preds

def get_chunks(tokenized_inputs, max_num_sents):
    chunk = []
    curr_sent_num = 0
    num_docs = 0
    for doc in tokenized_inputs:
        if curr_sent_num+len(doc) >= max_num_sents:
            if len(chunk) != 0:
                yield num_docs, chunk
                num_docs = 0
                chunk = []
            else:
                # we truncate by max_num_sents when tokenizing,
                # so this will trigger for those but there will be no actual truncation
                yield 1, doc[:max_num_sents]
                continue
            curr_sent_num = 0

        curr_sent_num += len(doc)
        chunk.extend(doc)
        num_docs += 1

    if len(chunk) != 0:
        yield num_docs, chunk

def model_predict(doc_embeddings, doc_mock_token_labels, doc_org_lengths):
    all_token_preds = []
    with torch.no_grad():
        doc_embeddings = doc_embeddings.unsqueeze(0).to(model_device)
        token_out, sent_out, doc_out = model(doc_embeddings)
        sent_out = sent_out.squeeze(0)

        token_preds = token_out.detach().cpu().numpy()
        token_preds = numpy.argmax(token_preds, axis=2) # [Sentences, Seq_len]

    doc_pred = torch.sigmoid(doc_out).detach().cpu().numpy()
    doc_pred = int(doc_pred.tolist()[0][0] >= 0.5)
    sent_preds = torch.sigmoid(sent_out).detach().cpu().numpy()
    sent_preds = [int(x[0] >= 0.5) for x in sent_preds.tolist()]

    for sent_num in range(len(doc_org_lengths)): # For each sentence
        curr_token_preds = token_preds[sent_num, :]
        tok_labs = doc_mock_token_labels[sent_num, :]
        tok_preds = curr_token_preds[tok_labs != -1].tolist() # get rid of extra subwords, CLS, SEP, PAD

        sent_org_length = doc_org_lengths[sent_num]
        tok_preds.extend([14] * (sent_org_length - len(tok_preds))) # 14 is for "O" label
        all_token_preds.append(tok_preds)

    return all_token_preds, sent_preds, doc_pred

# NOTE: Parallelize BERT part not the ScopeIt part
# So just string all sentences together, then pass them to BERT.
# After that divide them according to org_sentence_lengths again,
# and pass them to model.
def predict(inputs, max_length=128, max_num_sents=200):
    # tokenize
    org_sentence_lengths = []
    tokenized_inputs = []
    org_lengths = []
    for curr_sentences in inputs:
        # TODO: Think of the consequences of this
        if len(curr_sentences) > max_num_sents:
            curr_sentences = curr_sentences[:max_num_sents]

        org_sentence_lengths.append(len(curr_sentences))
        all_tokens = []
        curr_org_lengths = []
        for sent in curr_sentences:
            curr_tokens = word_tokenize(sent, language=args.language)
            if len(curr_tokens) != 0:
                all_tokens.append(curr_tokens)
                curr_org_lengths.append(len(curr_tokens))

        org_lengths.append(curr_org_lengths)
        tokenized_inputs.append(all_tokens)

    doc_count = 0
    all_token_preds = []
    all_sent_preds = []
    all_doc_preds = []
    for num_docs, chunk in get_chunks(tokenized_inputs, max_num_sents):
        # get input
        curr_org_sentence_lengths = org_sentence_lengths[doc_count:doc_count+num_docs]
        curr_org_lengths = org_lengths[doc_count:doc_count+num_docs]
        doc_count += num_docs

        chunk = tokenize_and_align_labels(chunk, max_length=max_length)
        input_ids = chunk["input_ids"]
        input_masks = chunk["attention_mask"]
        mock_labels = torch.LongTensor(chunk["mock_labels"]).numpy()
        if not no_token_type:
            token_type_ids = chunk["token_type_ids"].to(bert_device)

        input_ids = input_ids.to(bert_device)
        input_masks = input_masks.to(bert_device)
        with torch.no_grad():
            if no_token_type:
                embeddings = bert(input_ids, attention_mask=input_masks)[0]
            else:
                embeddings = bert(input_ids, attention_mask=input_masks,
                                  token_type_ids=token_type_ids)[0]

        # predict
        curr_sent_num = 0
        for doc_num in range(num_docs):
            org_sent_length = curr_org_sentence_lengths[doc_num]
            lower = curr_sent_num
            curr_sent_num += org_sent_length

            curr_docs_embeddings = embeddings[lower:curr_sent_num, :, :]
            curr_docs_mock_labels = mock_labels[lower:curr_sent_num, :]
            token_preds, sent_preds, doc_pred = model_predict(curr_docs_embeddings,
                                                               curr_docs_mock_labels,
                                                               curr_org_lengths[doc_num])

            all_token_preds.append(token_preds)
            all_sent_preds.append(sent_preds)
            all_doc_preds.append(doc_pred)

    return tokenized_inputs, all_token_preds, all_sent_preds, all_doc_preds

# Tokenize all texts and align the labels with them.
def tokenize_and_align_labels(texts, max_length=128):
    tokenized_inputs = tokenizer(
        texts,
        padding="max_length",
        truncation=True,
        max_length=max_length,
        is_split_into_words=True,
        return_tensors="pt")

    labels = []
    for i, text in enumerate(texts):
        word_ids = tokenized_inputs.word_ids(batch_index=i)
        previous_word_idx = None
        label_ids = []
        for word_idx in word_ids:
            if word_idx is None:
                label_ids.append(-1)
            elif word_idx != previous_word_idx:
                label_ids.append(14)
            else:
                label_ids.append(-1)
            previous_word_idx = word_idx

        labels.append(label_ids)

    tokenized_inputs["mock_labels"] = labels
    return tokenized_inputs

def tag_places_flair(all_docs_tokenized, all_pos_idxs, cascaded=True):
    # Place Tagger
    place_output = []
    if cascaded:
        sent_lengths = [len(pos_idxs) for pos_idxs in all_pos_idxs]
        doc_sents = [flair.data.Sentence(" ".join(sent_tokens)) for tokenized_sentences,pos_idxs in zip(all_docs_tokenized, all_pos_idxs) for idx,sent_tokens in enumerate(tokenized_sentences) if idx in pos_idxs] # select only positive sentences
    else:
        sent_lengths = [len(tokenized_sentences) for tokenized_sentences in all_docs_tokenized]
        doc_sents = [flair.data.Sentence(" ".join(sent_tokens)) for tokenized_sentences in all_docs_tokenized for sent_tokens in tokenized_sentences]

    sent_offsets = [0] + [sum(sent_lengths[:idx+1]) for idx in range(len(sent_lengths))] # offsets according to doc lengths
    doc_sents = place_tagger.predict(doc_sents)

    curr_place_tags = []
    doc_idx = 0
    for sent_id, sent in enumerate(doc_sents):
        if sent_id == sent_offsets[doc_idx+1]:
            doc_idx += 1
            place_output.append(curr_place_tags)
            curr_place_tags = []
            if cascaded:
                while len(all_pos_idxs[doc_idx]) == 0: # In case there are no positive sentences for this doc
                    place_output.append([])
                    doc_idx += 1

        sent_id1 = sent_id - sent_offsets[doc_idx]
        for span in sent.get_spans("ner"):
            if span.tag == "LOC":
                # Ids are 1-indexed for some reason
                idxs = sorted([tok.idx - 1 for tok in span.tokens])
                if cascaded:
                    to_be_added = (all_pos_idxs[doc_idx][sent_id1], idxs[0], idxs[-1])
                else:
                    to_be_added = (sent_id1, idxs[0], idxs[-1])

                curr_place_tags.append(to_be_added) # tuple of sent_id, start_idx of span, end_idx of span

    place_output.append(curr_place_tags) # the last one is not caught with our if, so we add it here

    if cascaded:
        while len(place_output) != len(all_pos_idxs): # In case there are no positive sentences at the last documents
            place_output.append([])

    return place_output


class queryList(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('texts', required=False, type=str, action='append', default=[])
        parser.add_argument('max_length', required=True)
        parser.add_argument('max_num_sents', required=True)
        parser.add_argument('cascaded', type=bool, required=True)
        parser.add_argument('all_tokens', required=False)
        parser.add_argument('token_preds', required=False)
        parser.add_argument('sent_preds', required=False)
        parser.add_argument('doc_preds', required=False)
        parser.add_argument('flair_output', required=False)
        args = parser.parse_args()

        tokenized_inputs, all_token_preds, all_sent_preds, all_doc_preds = predict(args['texts'],
                                                                                   max_length=int(args["max_length"]),
                                                                                   max_num_sents=int(args["max_num_sents"]))

        # TODO: check here if document is positive or not
        all_pos_idxs = [[i for i,pred in enumerate(sent_preds) if pred == 1] for sent_preds in all_sent_preds]
        place_output = tag_places_flair(tokenized_inputs, all_pos_idxs, cascaded=args["cascaded"])

        args["all_tokens"] = tokenized_inputs
        args["token_preds"] = all_token_preds
        args["sent_preds"] = all_sent_preds
        args["doc_preds"] = all_doc_preds
        args["flair_output"] = place_output

        return args, 201

def get_args():
    '''
    This function parses and return arguments passed in
    '''
    parser = argparse.ArgumentParser(prog='classifier_batch_flask.py',
                                     description='Flask Server for Document Classification')
    parser.add_argument('--gpu_number', help="Insert the gpu count/number , if more than gpu will be allocated please use the following format 0,1,3,5, where 0,1,3,5 gpus will be allocated.\n or just type the number of required gpu, i.e 6 ",default="0,1")
    parser.add_argument('--gpu_number_place', help="Insert the gpu number for flair",default="7")
    #parser.add_argument('--batch_size', help="Document model batch size", type=int, default=10)
    parser.add_argument('--language', help="Language of the tokenizer", type=str, default="en")
    args = parser.parse_args()

    return(args)

@app.route("/")
def index():
    if classifer is not None :
        return "<html><body><p>classifier is loaded</p></body></html>"
    else :
        return "<html><body><p>classifier is not loaded</p></body></html>"

FLAIR_CACHE_ROOT = HOME +  "/.pytorch_pretrained_bert"

gru_hidden_size = 512
max_seq_length = 128
num_token_labels = 15
num_labels = 2

bert_model = "xlm-roberta-base"# HOME+"/.pytorch_pretrained_bert/bert-base-uncased.tar.gz"
no_token_type = True
model_path = HOME+"/.pytorch_pretrained_bert/multi_task_scopeit.pt"
bert_model_path = HOME+"/.pytorch_pretrained_bert/multi_task_bert.pt"

tokenizer = AutoTokenizer.from_pretrained(bert_model)
bert = XLMRobertaModel.from_pretrained(bert_model)
model = ScopeIt(bert.config.hidden_size, gru_hidden_size, num_layers=2, num_token_labels=num_token_labels)

args = get_args()
# BATCHSIZE = args.batch_size
if torch.cuda.is_available():
    model.load_state_dict(torch.load(model_path))
    gpu_range = args.gpu_number.split(",")
    if len(gpu_range) == 1:
        bert_device = torch.device("cuda:{0}".format(int(gpu_range[0])))
        model_device = bert_device
    elif len(gpu_range) >= 2:
        device_ids = [int(x) for x in gpu_range]
        model_device = torch.device("cuda:{0}".format(device_ids[0]))
        bert_device = torch.device("cuda:{0}".format(device_ids[1]))
        bert = torch.nn.DataParallel(bert,device_ids=device_ids[1:],output_device=bert_device,dim=0)
        bert.load_state_dict(torch.load(bert_model_path))
else:
    model.load_state_dict(torch.load(model_path, map_location='cpu'))
    bert_device = torch.device("cpu")
    model_device = torch.device("cpu")

bert.to(bert_device)
bert.eval()
model.to(model_device)
model.eval()

# Flair model for place names
if args.gpu_number_place == "cpu":
    flair.device = torch.device("cpu") # Default one is cuda:0
else:
    flair.device = torch.device("cuda:" + args.gpu_number_place)

flair.cache_root = FLAIR_CACHE_ROOT
#place_tagger = flair.models.SequenceTagger.load("ner")
place_tagger = flair.models.SequenceTagger.load(FLAIR_CACHE_ROOT + "/models/en-ner-conll03-v0.4.pt")
place_tagger.eval()

api.add_resource(queryList, '/queries')
app.run(host='0.0.0.0', port=4994, debug=True)
