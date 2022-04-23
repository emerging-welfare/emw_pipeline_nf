import argparse
import json
import requests
from utils import write_to_json
from utils import read_from_json
import os.path
from nltk import sent_tokenize, word_tokenize
from itertools import combinations
import numpy
import time

def get_args():
    '''
    This function parses and return arguments passed in
    '''
    parser = argparse.ArgumentParser(prog='classifier.py',
                                     description='Document FLASK SVM Classififer Application ')
    parser.add_argument('--input_files', help="Input filenames")
    parser.add_argument('--input_dir', help="Input folder")
    parser.add_argument('--out_dir', help="Output folder")
    parser.add_argument('--language', help="The source language. Ex. 'english'")
    args = parser.parse_args()

    return(args)

def request(tokens):
    try:
        r = requests.post(url = "http://localhost:5000/queries",
                          json={'tokens':tokens},
                          timeout=600) # 10 min timeout
        return json.loads(r.text)
    except requests.exceptions.Timeout as e:
        print("Timeout")
        data = {"fail": "Timeout"}
        return data
    except Exception as e:
        print("Error")
        data = {"fail": "Error", "error": e}
        return data


def clustering_algo(coref_out, pos_idxs, rescoring=True, ignore_lower_part=False):
    """
    Receives the output from the CorefHead with the positive sentence's indexes.
    Converts this output, which is a matrix representing relations between positive sentences,
    into actual clusters (lists of lists of sentence indexes).
    Optionally, applies rescoring to relations.
    """
    reward = penalty = 0.1
    clustering_threshold = 0.5

    # NOTE : pos_idxs are always ordered, so each tuple in ids are always ordered, soo we only use the upper part of the score matrix when deciding labels.
    ids = list(combinations(pos_idxs, 2))
    pos_id_to_order = {}
    for i, idx in enumerate(pos_idxs):
        pos_id_to_order[idx] = i

    pairs = {}
    for v in ids:
        pairs[v] = coref_out[pos_id_to_order[v[0]], pos_id_to_order[v[1]]]

    coref_out = (coref_out >= 0.5).astype(int)

    # rescoring
    if rescoring:
        for s1, s2 in ids:
            for s in pos_idxs:
                if s1 == s or s2 == s:
                    continue

                # When we train and use only the upper part of the matrix, we need to order these
                if ignore_lower_part:
                    s1s = sorted([s1,s])
                    s2s = sorted([s2,s])
                    s1_s_label = coref_out[pos_id_to_order[s1s[0]],pos_id_to_order[s1s[1]]]
                    s2_s_label = coref_out[pos_id_to_order[s2s[0]],pos_id_to_order[s2s[1]]]
                else:
                    s1_s_label = coref_out[pos_id_to_order[s1],pos_id_to_order[s]]
                    s2_s_label = coref_out[pos_id_to_order[s2],pos_id_to_order[s]]

                if  s1_s_label == 1 and s2_s_label == 1:
                    pairs[(s1,s2)] += reward
                elif s1_s_label != s2_s_label:
                    pairs[(s1,s2)] -= penalty

    clusters = { n: 0 for n in pos_idxs }
    filtered_pairs = { k : v  for k, v in pairs.items() if v >= clustering_threshold }
    sorted_pairs = sorted(filtered_pairs, key=lambda x: (filtered_pairs[x], x[0] - x[1]), reverse=True)

    # clustering
    group_no = 0
    for s1, s2 in sorted_pairs:
        if clusters[s1] == clusters[s2] == 0:
            group_no += 1
            clusters[s1] = clusters[s2] = group_no
        elif clusters[s1] == 0:
            clusters[s1] = clusters[s2]
        else:
            clusters[s2] = clusters[s1]

    for s in pos_idxs:
        if clusters[s] == 0:
            group_no += 1
            clusters[s] = group_no

    cluster_grouped = {}
    for k, v in clusters.items():
        if v in cluster_grouped:
            cluster_grouped[v].append(k)
        else:
            cluster_grouped[v] = [k, ]

    return list(cluster_grouped.values())


if __name__ == "__main__":
    args = get_args()
    files=args.input_files.strip("[ ]").split(", ")
    jsons = []
    for filename in files:
        filename = args.input_dir + "/" + filename
        if os.path.exists(filename):
            curr_json = read_from_json(filename)
            # NOTE: If there is only sentences and not tokens, then there might be a problem
            if "sentences" not in curr_json.keys() and "tokens" not in curr_json.keys():
                if not curr_json["text"].strip():
                    continue

                sentences = sent_tokenize(curr_json["text"], language=args.language)

                new_sentences = []
                doc_tokens = []
                for sent in sentences:
                    curr_tokens = word_tokenize(sent, language=args.language)
                    if len(curr_tokens) != 0:
                        new_sentences.append(sent)
                        doc_tokens.append(curr_tokens)

                curr_json["sentences"] = new_sentences
                curr_json["tokens"] = doc_tokens

            else:
                assert(len(curr_json["sentences"]) == len(curr_json["tokens"]))

            if len(curr_json["tokens"]) > 0:
                jsons.append(curr_json)

    if len(jsons) != 0:
        rtext = request([data["tokens"] for data in jsons])
        retries = 0
        while ("token_preds" not in rtext.keys() and retries < 10):
            time.sleep(10.0) # sleep 10 seconds before trying again
            rtext = request([data["tokens"] for data in jsons])
            retries += 1

        if "token_preds" in rtext.keys():
            token_preds = rtext["token_preds"]
            sent_preds = rtext["sent_preds"]
            doc_preds = rtext["doc_preds"]
            coref_outs = rtext["coref_outs"]

            for i, data in enumerate(jsons):
                curr_token_preds = token_preds[i]
                curr_sent_preds = [int(pred) for pred in sent_preds[i]]
                curr_doc_pred = int(doc_preds[i])

                # TODO: Maybe we don't process coref_out for negative files if doc_cascaded is true.
                pred_clusters = []
                pos_sent_idxs = [i for i,v in enumerate(curr_sent_preds) if int(v) == 1]
                if len(pos_sent_idxs) > 1: # If we have 0 or 1 pos sentence, we don't need to do coreference.
                    curr_coref_out = numpy.array(coref_outs[i])
                    curr_coref_out = curr_coref_out[pos_sent_idxs,:][:,pos_sent_idxs]
                    pred_clusters = clustering_algo(curr_coref_out, pos_sent_idxs)
                elif len(pos_sent_idxs) == 1: # TODO: Do we need this here?
                    pred_clusters = [[pos_sent_idxs[0]]]

                data["doc_label"] = curr_doc_pred
                data["token_labels"] = curr_token_preds
                data["sent_labels"] = curr_sent_preds
                data["event_clusters"] = pred_clusters

                write_to_json(data, data["id"], extension="json", out_dir=args.out_dir)

        # else:# TODO: Just log this
        #     raise(rtext["fail"])
