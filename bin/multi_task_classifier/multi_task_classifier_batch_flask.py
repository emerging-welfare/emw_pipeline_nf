import os
import numpy
import torch
import argparse

from transformers import AutoTokenizer, XLMRobertaModel
import sys
sys.path.append("..")
from models import ScopeIt_with_coref
# import flair

# Import the framework
import flask
from flask_restful import Resource, Api

# Create an instance of Flask
app = flask.Flask(__name__)
# Create the API
api = Api(app)

HOME=os.getenv("HOME")

def get_chunks(tokenized_inputs, max_num_sents):
    # TODO: Test this somehow
    chunk = []
    curr_sent_num = 0
    num_docs = 0
    for doc in tokenized_inputs:
        if curr_sent_num+len(doc) >= max_num_sents and len(chunk) != 0:
            yield num_docs, chunk
            num_docs = 0
            chunk = []
            curr_sent_num = 0

        curr_sent_num += len(doc)
        chunk.extend(doc[:max_num_sents]) # doc[:max_num_sents] is actually doc[:min(len(doc), max_num_sents)]
        num_docs += 1

    if len(chunk) != 0:
        yield num_docs, chunk

def model_predict(doc_embeddings, doc_mock_token_labels, doc_org_lengths):
    all_token_preds = []
    with torch.no_grad():
        doc_embeddings = doc_embeddings.to(model_device)
        token_out, sent_out, doc_out, coref_out = model(doc_embeddings)

    token_preds = token_out.detach().cpu().numpy()
    token_preds = numpy.argmax(token_preds, axis=2) # [Sentences, Seq_len]

    sent_preds = torch.sigmoid(sent_out).detach().cpu().numpy()
    sent_preds = [int(x[0] >= 0.5) for x in sent_preds.tolist()]

    doc_pred = torch.sigmoid(doc_out).detach().cpu().numpy()
    doc_pred = int(doc_pred.tolist()[0] >= 0.5)

    coref_out = torch.sigmoid(coref_out).detach().cpu().numpy()

    # Length fix for token
    for sent_num in range(len(doc_org_lengths)): # For each sentence
        curr_token_preds = token_preds[sent_num, :]
        tok_labs = doc_mock_token_labels[sent_num, :]
        tok_preds = curr_token_preds[tok_labs != -1].tolist() # get rid of extra subwords, CLS, SEP, PAD
        tok_preds = [idx_to_label[pred] for pred in tok_preds]

        sent_org_length = doc_org_lengths[sent_num]
        tok_preds.extend(["O"] * (sent_org_length - len(tok_preds)))
        all_token_preds.append(tok_preds)

    return all_token_preds, sent_preds, doc_pred, coref_out

# NOTE: Parallelize the encoder part not the ScopeIt part
# So just string all sentences together, then pass them to the encoder.
# After that divide them according to org_sentence_lengths again,
# and pass them to model.
def predict(inputs, max_length=128, max_num_sents=6500):
    # tokenize
    org_sentence_lengths = []
    org_lengths = []
    for curr_doc_tokens in inputs:
        org_sentence_lengths.append(len(curr_doc_tokens))
        curr_org_lengths = [len(sent_tokens) for sent_tokens in curr_doc_tokens]
        org_lengths.append(curr_org_lengths)

    doc_count = 0
    all_token_preds = []
    all_sent_preds = []
    all_doc_preds = []
    all_coref_outs = []
    for num_docs, chunk in get_chunks(inputs, max_num_sents):
        # get input
        curr_org_sentence_lengths = org_sentence_lengths[doc_count:doc_count+num_docs]
        curr_org_lengths = org_lengths[doc_count:doc_count+num_docs]
        doc_count += num_docs

        chunk = tokenize_and_align_labels(chunk, max_length=max_length)
        input_ids = chunk["input_ids"]
        input_masks = chunk["attention_mask"]
        mock_labels = numpy.array(chunk["mock_labels"])
        if not no_token_type:
            token_type_ids = chunk["token_type_ids"].to(encoder_device)

        input_ids = input_ids.to(encoder_device)
        input_masks = input_masks.to(encoder_device)
        with torch.no_grad():
            if no_token_type:
                embeddings = encoder(input_ids, attention_mask=input_masks)[0]
            else:
                embeddings = encoder(input_ids, attention_mask=input_masks,
                                     token_type_ids=token_type_ids)[0]

        # TODO: if num_docs == 1, then we lost some sentences. Need to fill the sent_preds and
        # token preds with negative labels for those lost sentences and their tokens. -> Maybe we
        # don't care about too long documents(with more than 6500 sentences).

        # predict
        curr_sent_num = 0
        for doc_num in range(num_docs):
            org_sent_length = curr_org_sentence_lengths[doc_num]
            lower = curr_sent_num
            curr_sent_num += org_sent_length

            curr_docs_embeddings = embeddings[lower:curr_sent_num, :, :]
            curr_docs_mock_labels = mock_labels[lower:curr_sent_num, :]
            token_preds, sent_preds, doc_pred, coref_out = model_predict(curr_docs_embeddings,
                                                                         curr_docs_mock_labels,
                                                                         curr_org_lengths[doc_num])

            all_token_preds.append(token_preds)
            all_sent_preds.append(sent_preds)
            all_doc_preds.append(doc_pred)
            all_coref_outs.append(coref_out.tolist())

    return all_token_preds, all_sent_preds, all_doc_preds, all_coref_outs

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

# def tag_places_flair(all_docs_tokenized, all_pos_idxs, cascaded=True):
#     # Place Tagger
#     place_output = []
#     if cascaded:
#         sent_lengths = [len(pos_idxs) for pos_idxs in all_pos_idxs]
#         doc_sents = [flair.data.Sentence(" ".join(sent_tokens)) for tokenized_sentences,pos_idxs in zip(all_docs_tokenized, all_pos_idxs) for idx,sent_tokens in enumerate(tokenized_sentences) if idx in pos_idxs] # select only positive sentences
#     else:
#         sent_lengths = [len(tokenized_sentences) for tokenized_sentences in all_docs_tokenized]
#         doc_sents = [flair.data.Sentence(" ".join(sent_tokens)) for tokenized_sentences in all_docs_tokenized for sent_tokens in tokenized_sentences]

#     sent_offsets = [0] + [sum(sent_lengths[:idx+1]) for idx in range(len(sent_lengths))] # offsets according to doc lengths
#     doc_sents = place_tagger.predict(doc_sents)

#     curr_place_tags = []
#     doc_idx = 0
#     for sent_id, sent in enumerate(doc_sents):
#         if sent_id == sent_offsets[doc_idx+1]:
#             doc_idx += 1
#             place_output.append(curr_place_tags)
#             curr_place_tags = []
#             if cascaded:
#                 while len(all_pos_idxs[doc_idx]) == 0: # In case there are no positive sentences for this doc
#                     place_output.append([])
#                     doc_idx += 1

#         sent_id1 = sent_id - sent_offsets[doc_idx]
#         for span in sent.get_spans("ner"):
#             if span.tag == "LOC":
#                 # Ids are 1-indexed for some reason
#                 idxs = sorted([tok.idx - 1 for tok in span.tokens])
#                 if cascaded:
#                     to_be_added = (all_pos_idxs[doc_idx][sent_id1], idxs[0], idxs[-1])
#                 else:
#                     to_be_added = (sent_id1, idxs[0], idxs[-1])

#                 curr_place_tags.append(to_be_added) # tuple of sent_id, start_idx of span, end_idx of span

#     place_output.append(curr_place_tags) # the last one is not caught with our if, so we add it here

#     if cascaded:
#         while len(place_output) != len(all_pos_idxs): # In case there are no positive sentences at the last documents
#             place_output.append([])

#     return place_output


class queryList(Resource):
    def post(self):
        args = flask.request.get_json(force=True)
        all_token_preds, all_sent_preds, all_doc_preds, all_coref_outs = predict(args['tokens'],
                                                                                 max_length=max_seq_length,
                                                                                 max_num_sents=max_num_sents)

        # all_pos_idxs = [[i for i,pred in enumerate(sent_preds) if pred == 1] for sent_preds in all_sent_preds]
        # place_output = tag_places_flair(tokenized_inputs, all_pos_idxs, cascaded=args["cascaded"])

        out = {}
        out["token_preds"] = all_token_preds
        out["sent_preds"] = all_sent_preds
        out["doc_preds"] = all_doc_preds
        out["coref_outs"] = all_coref_outs

        return out, 201

def get_args():
    '''
    This function parses and return arguments passed in
    '''
    parser = argparse.ArgumentParser(prog='classifier_batch_flask.py',
                                     description='Flask Server for Document Classification')
    parser.add_argument('--gpu_number', help="Insert the gpu count/number , if more than gpu will be allocated please use the following format 0,1,3,5, where 0,1,3,5 gpus will be allocated.\n or just type the number of required gpu, i.e 6 ",default="0,1,2,3,4,5,6,7")
    args = parser.parse_args()

    return(args)

@app.route("/")
def index():
    if classifer is not None :
        return "<html><body><p>classifier is loaded</p></body></html>"
    else :
        return "<html><body><p>classifier is not loaded</p></body></html>"

# FLAIR_CACHE_ROOT = HOME +  "/.pytorch_pretrained_bert"

###### MODEL STUFF ######
label_list = ["B-etime", "B-fname", "B-organizer", "B-participant", "B-place", "B-target",
              "B-trigger", "I-etime", "I-fname", "I-organizer", "I-participant", "I-place",
              "I-target", "I-trigger", "O"]
idx_to_label = {}
for i, lab in enumerate(label_list):
    idx_to_label[i] = lab

gru_hidden_size = 512
max_seq_length = 128
max_num_sents = 6500
num_token_labels = len(label_list)
num_labels = 1

pretrained_transformers_model = "xlm-roberta-base"
no_token_type = True
model_path = HOME+"/.pytorch_pretrained_bert/multilingual_multi_task_scopeit_with_coref.pt"
encoder_model_path = HOME+"/.pytorch_pretrained_bert/multilingual_multi_task_encoder.pt"

tokenizer = AutoTokenizer.from_pretrained(pretrained_transformers_model)
encoder = XLMRobertaModel.from_pretrained(pretrained_transformers_model)
model = ScopeIt_with_coref(encoder.config.hidden_size, gru_hidden_size, num_layers=2,
                           num_token_labels=num_token_labels, use_two_mlps_for_coref=False)

args = get_args()

if torch.cuda.is_available():
    gpu_range = args.gpu_number.split(",")
    if len(gpu_range) == 1:
        encoder_device = torch.device("cuda:{0}".format(int(gpu_range[0])))
        model_device = encoder_device
    elif len(gpu_range) >= 2:
        device_ids = [int(x) for x in gpu_range]
        model_device = torch.device("cuda:{0}".format(device_ids[0]))
        encoder_device = torch.device("cuda:{0}".format(device_ids[1]))
        encoder.load_state_dict(torch.load(encoder_model_path, map_location=encoder_device))
        encoder = torch.nn.DataParallel(encoder,device_ids=device_ids[1:],output_device=encoder_device,dim=0)

    model.load_state_dict(torch.load(model_path, map_location=model_device))
else:
    model.load_state_dict(torch.load(model_path, map_location='cpu'))
    encoder_device = torch.device("cpu")
    model_device = torch.device("cpu")

encoder.to(encoder_device)
encoder.eval()
model.to(model_device)
model.eval()
######

api.add_resource(queryList, '/queries')
app.run(host='0.0.0.0', port=5000, debug=False)


# *************** TEST CODE ****************
# # TODO: Remove this test code
# # We can use this directly when testing nextflow parallelism. We do not need flask if we
# # don't use nextflow!
# import json
# from glob import glob
# from nltk import sent_tokenize, word_tokenize
# from itertools import combinations
# from time import time
# import re

# def clustering_algo(coref_out, pos_idxs, rescoring=True, ignore_lower_part=False):
#     """
#     Receives the output from the CorefHead with the positive sentence's indexes.
#     Converts this output, which is a matrix representing relations between positive sentences,
#     into actual clusters (lists of lists of sentence indexes).
#     Optionally, applies rescoring to relations.
#     """
#     reward = penalty = 0.1
#     clustering_threshold = 0.5

#     # NOTE : pos_idxs are always ordered, so each tuple in ids are always ordered, soo we only use the upper part of the score matrix when deciding labels.
#     ids = list(combinations(pos_idxs, 2))
#     pos_id_to_order = {}
#     for i, idx in enumerate(pos_idxs):
#         pos_id_to_order[idx] = i

#     pairs = {}
#     for v in ids:
#         pairs[v] = coref_out[pos_id_to_order[v[0]], pos_id_to_order[v[1]]]

#     coref_out = (coref_out >= 0.5).astype(int)

#     # rescoring
#     if rescoring:
#         for s1, s2 in ids:
#             for s in pos_idxs:
#                 if s1 == s or s2 == s:
#                     continue

#                 # When we train and use only the upper part of the matrix, we need to order these
#                 if ignore_lower_part:
#                     s1s = sorted([s1,s])
#                     s2s = sorted([s2,s])
#                     s1_s_label = coref_out[pos_id_to_order[s1s[0]],pos_id_to_order[s1s[1]]]
#                     s2_s_label = coref_out[pos_id_to_order[s2s[0]],pos_id_to_order[s2s[1]]]
#                 else:
#                     s1_s_label = coref_out[pos_id_to_order[s1],pos_id_to_order[s]]
#                     s2_s_label = coref_out[pos_id_to_order[s2],pos_id_to_order[s]]

#                 if  s1_s_label == 1 and s2_s_label == 1:
#                     pairs[(s1,s2)] += reward
#                 elif s1_s_label != s2_s_label:
#                     pairs[(s1,s2)] -= penalty

#     clusters = { n: 0 for n in pos_idxs }
#     filtered_pairs = { k : v  for k, v in pairs.items() if v >= clustering_threshold }
#     sorted_pairs = sorted(filtered_pairs, key=lambda x: (filtered_pairs[x], x[0] - x[1]), reverse=True)

#     # clustering
#     group_no = 0
#     for s1, s2 in sorted_pairs:
#         if clusters[s1] == clusters[s2] == 0:
#             group_no += 1
#             clusters[s1] = clusters[s2] = group_no
#         elif clusters[s1] == 0:
#             clusters[s1] = clusters[s2]
#         else:
#             clusters[s2] = clusters[s1]

#     for s in pos_idxs:
#         if clusters[s] == 0:
#             group_no += 1
#             clusters[s] = group_no

#     cluster_grouped = {}
#     for k, v in clusters.items():
#         if v in cluster_grouped:
#             cluster_grouped[v].append(k)
#         else:
#             cluster_grouped[v] = [k, ]

#     return list(cluster_grouped.values())

# def read_from_json(fpath):
#    json_content=""
#    with open(fpath, "r", encoding="utf-8",errors='surrogatepass') as f:
#         json_content=json.loads(f.readline())
#    return json_content


# doc_batchsize = 2000
# max_length = 128
# max_num_sents = 6500#1750
# language = 'english'

# input_dir = "/data/pipeline_input/test"
# out_dir = "/data/pipeline_output/test/"
# all_filenames = list(glob(input_dir + "/http*"))


# def get_file_chunks(all_filenames, max_num_sents):
#     chunk = []
#     chunk_jsons = []
#     chunk_org_sentence_lengths = []
#     chunk_org_lengths = []
#     curr_sent_num = 0
#     for filename in all_filenames:
#         curr_json = read_from_json(filename)
#         # NOTE: If there is only sentences and not tokens, then there might be a problem
#         if "sentences" not in curr_json.keys() and "tokens" not in curr_json.keys():
#             sentences = sent_tokenize(curr_json["text"], language=language)

#             new_sentences = []
#             doc_tokens = []
#             for sent in sentences:
#                 curr_tokens = word_tokenize(sent, language=language)
#                 if len(curr_tokens) != 0:
#                     new_sentences.append(sent)
#                     doc_tokens.append(curr_tokens)

#             curr_json["sentences"] = new_sentences
#             curr_json["tokens"] = doc_tokens

#         else:
#             assert(len(curr_json["sentences"]) == len(curr_json["tokens"]))

#         if len(curr_json["tokens"]) > 0:
#             # NOTE: If we overflow the max_num_sents with this document's sentences,
#             # we first flush what we have, then start over with this document's sentences.
#             if curr_sent_num+len(curr_json["sentences"]) >= max_num_sents and len(chunk) != 0:
#                 yield chunk, chunk_jsons, chunk_org_sentence_lengths, chunk_org_lengths
#                 chunk = []
#                 chunk_jsons = []
#                 chunk_org_sentence_lengths = []
#                 chunk_org_lengths = []
#                 curr_sent_num = 0

#             chunk_jsons.append(curr_json)
#             chunk_org_sentence_lengths.append(len(curr_json["sentences"]))
#             curr_org_lengths = [len(sent_tokens) for sent_tokens in curr_json["tokens"]]
#             chunk_org_lengths.append(curr_org_lengths)

#             curr_sent_num += len(curr_json["sentences"])
#             chunk.extend(curr_json["tokens"][:max_num_sents]) # doc[:max_num_sents] is actually doc[:min(len(doc), max_num_sents)]

#     if len(chunk) != 0: # Flush the last batch
#         yield chunk, chunk_jsons, chunk_org_sentence_lengths, chunk_org_lengths


# start_time = time()
# for chunk, chunk_jsons, chunk_org_sentence_lengths, chunk_org_lengths in get_file_chunks(all_filenames, max_num_sents):
#     all_token_preds = []
#     all_sent_preds = []
#     all_doc_preds = []
#     all_coref_outs = []

#     chunk = tokenize_and_align_labels(chunk, max_length=max_length)
#     input_ids = chunk["input_ids"]
#     input_masks = chunk["attention_mask"]
#     mock_labels = numpy.array(chunk["mock_labels"])
#     if not no_token_type:
#         token_type_ids = chunk["token_type_ids"].to(encoder_device)

#     input_ids = input_ids.to(encoder_device)
#     input_masks = input_masks.to(encoder_device)
#     with torch.no_grad():
#         if no_token_type:
#             embeddings = encoder(input_ids, attention_mask=input_masks)[0]
#         else:
#             embeddings = encoder(input_ids, attention_mask=input_masks,
#                                  token_type_ids=token_type_ids)[0]

#     # TODO: if num_docs == 1, then we lost some sentences. Need to fill the sent_preds and
#     # token preds with negative labels for those lost sentences and their tokens. -> Maybe we
#     # don't care about too loooooooong documents.

#     # predict
#     curr_sent_num = 0
#     for doc_num in range(len(chunk_jsons)):
#         org_sent_length = chunk_org_sentence_lengths[doc_num]
#         lower = curr_sent_num
#         curr_sent_num += org_sent_length

#         curr_docs_embeddings = embeddings[lower:curr_sent_num, :, :]
#         curr_docs_mock_labels = mock_labels[lower:curr_sent_num, :]
#         token_preds, sent_preds, doc_pred, coref_out = model_predict(curr_docs_embeddings,
#                                                                      curr_docs_mock_labels,
#                                                                      chunk_org_lengths[doc_num])

#         data = chunk_jsons[doc_num]
#         doc_pred = int(doc_pred)
#         sent_preds = [int(pred) for pred in sent_preds]

#         pos_sent_idxs = [i for i,v in enumerate(sent_preds) if int(v) == 1]
#         pred_clusters = []
#         if len(pos_sent_idxs) > 1: # If we have 0 or 1 pos sentence, we don't need to do coreference.
#             coref_out = coref_out[pos_sent_idxs,:][:,pos_sent_idxs]
#             pred_clusters = clustering_algo(coref_out, pos_sent_idxs)

#         data["doc_label"] = doc_pred
#         data["token_labels"] = token_preds
#         data["sent_labels"] = sent_preds
#         data["event_clusters"] = pred_clusters

#         out_filename = re.sub(r"(\.html?|\.cms|\.ece\d?|\.json|)$", ".json", out_dir + data["id"])
#         with open(out_filename, "w", encoding="utf-8") as f:
#             f.write(json.dumps(data))

# elapsed = time() - start_time
# print("Elapsed time in seconds: %.2f" %elapsed)
