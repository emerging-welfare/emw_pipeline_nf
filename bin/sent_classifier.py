import argparse
import json
import requests
from utils import read_from_json, write_to_json
import os
import numpy
import time

def get_args():
    '''
    This function parses and return arguments passed in
    '''
    parser = argparse.ArgumentParser(prog='sent_classifier.py',
                                     description='Sentence FLASK Classififer Application ')
    parser.add_argument('--input_files', help="Input filenames(relative path)")
    parser.add_argument('--input_dir', help="Input folder")
    parser.add_argument('--out_dir', help="Output folder")
    parser.add_argument('--sent_batchsize', type=int,
                        help="How many sentence to process in a single minibatch")
    parser.add_argument('--sent_cascaded', default=False, action="store_true",
                        help="Do we process negatively predicted sentences?")
    args = parser.parse_args()

    return(args)

def request(sentences):
    r = requests.post(url = "http://localhost:4999/queries", json={'sentences':sentences})
    out = json.loads(r.text)

    retries = 0
    while ("trigger_sem" not in out.keys() and retries < 10):
        time.sleep(10.0) # sleep 10 seconds before trying again
        r = requests.post(url = "http://localhost:4999/queries", json={'sentences':sentences})
        out = json.loads(r.text)
        retries += 1

    return out

if __name__ == "__main__":
    args = get_args()
    files=args.input_files.strip("[ ]").split(", ")

    all_jsons = []
    if args.sent_cascaded:
        all_file_pos_idxs = []
    else:
        all_file_ranges = []
        curr_file_idx_start = 0
    chunk = []
    all_trig_labels = []
    all_part_labels = []
    all_org_labels = []
    all_flair_outputs = []
    for file_idx, filename in enumerate(files):
        curr_json = read_from_json(args.input_dir + "/" + filename)

        assert(len(curr_json["sentences"]) == len(curr_json["tokens"]))
        curr_sentences = curr_json["sentences"]
        if len(curr_sentences) == 0:
            continue

        all_jsons.append(curr_json)

        if args.sent_cascaded:
            assert("sent_labels" in curr_json.keys() and len(curr_json["sent_labels"]) == len(curr_sentences))
            curr_pos_idxs = []
            curr_pos_sentences = []
            for i, sent in enumerate(curr_sentences):
                if curr_json["sent_labels"][i] == 1:
                    curr_pos_idxs.append(i)
                    curr_pos_sentences.append(sent)

            all_file_pos_idxs.append(curr_pos_idxs)
            chunk.extend(curr_pos_sentences)

        else:
            all_file_ranges.append((curr_file_idx_start, curr_file_idx_start+len(curr_sentences)))
            curr_file_idx_start += len(curr_sentences)
            chunk.extend(curr_sentences)

        if len(chunk) >= args.sent_batchsize:
            # NOTE: This for loop handles docs that have multiples of args.sent_batchsize
            # length of sentences in them. If we cut these docs at args.sent_batchsize sentences,
            # this code could have been written differently -> See get_chunks in multi_task flask.
            # Handles multiples of the batchsize
            for i in range(0, len(chunk)-(args.sent_batchsize-1), args.sent_batchsize):
                rtext = request(chunk[i:i+args.sent_batchsize])
                all_trig_labels.extend(rtext["trigger_sem"])
                all_part_labels.extend(rtext["part_sem"])
                all_org_labels.extend(rtext["org_sem"])
                # IMPORTANT NOTE: flair_output may be just an empty list!
                all_flair_outputs.extend(rtext["flair_output"])

            chunk = chunk[i+args.sent_batchsize:] # becomes [] if len(chunk) is a multiple of batchsize

    if len(chunk) > 0: # Last chunk
        rtext = request(chunk)
        all_trig_labels.extend(rtext["trigger_sem"])
        all_part_labels.extend(rtext["part_sem"])
        all_org_labels.extend(rtext["org_sem"])
        all_flair_outputs.extend(rtext["flair_output"])


    if args.sent_cascaded:
        lo = 0
        for file_idx, file_pos_idxs in enumerate(all_file_pos_idxs):
            hi = lo + len(file_pos_idxs)
            if len(file_pos_idxs) > 0:
                pos_trig_labels = all_trig_labels[lo:hi]
                pos_part_labels = all_part_labels[lo:hi]
                pos_org_labels = all_org_labels[lo:hi]
                pos_flair_outputs = all_flair_outputs[lo:hi]

            curr_data = all_jsons[file_idx]

            trig_out_labels = numpy.array([-1] * len(curr_data["sentences"]), dtype=object)
            part_out_labels = numpy.array([-1] * len(curr_data["sentences"]), dtype=object)
            org_out_labels = numpy.array([-1] * len(curr_data["sentences"]), dtype=object)
            out_flair = []

            if len(file_pos_idxs) > 0:
                trig_out_labels[file_pos_idxs] = pos_trig_labels
                part_out_labels[file_pos_idxs] = pos_part_labels
                org_out_labels[file_pos_idxs] = pos_org_labels

                for pos_idx, curr_sent_flair_output in zip(file_pos_idxs, pos_flair_outputs):
                    out_flair.extend([(pos_idx, span[0], span[1]) for span in curr_sent_flair_output])

            curr_data["trigger_semantic"] = trig_out_labels.tolist()
            curr_data["participant_semantic"] = part_out_labels.tolist()
            curr_data["organizer_semantic"] = org_out_labels.tolist()
            curr_data["flair_output"] = out_flair
            write_to_json(curr_data, curr_data["id"], extension="json", out_dir=args.out_dir)

            lo = hi

    else:
        assert(all_file_ranges[-1][1] == len(all_trig_labels))
        for file_idx, file_range in enumerate(all_file_ranges):
            lo = file_range[0]
            hi = file_range[1]
            curr_trig_labels = all_trig_labels[lo:hi]
            curr_part_labels = all_part_labels[lo:hi]
            curr_org_labels = all_org_labels[lo:hi]
            curr_flair_outputs = all_flair_outputs[lo:hi]

            out_flair = []
            for idx, curr_sent_flair_output in enumerate(curr_flair_outputs):
                out_flair.extend([(idx, span[0], span[1]) for span in curr_sent_flair_output])

            curr_data = all_jsons[file_idx]
            curr_data["trigger_semantic"] = curr_trig_labels
            curr_data["participant_semantic"] = curr_part_labels
            curr_data["organizer_semantic"] = curr_org_labels
            curr_data["flair_output"] = out_flair
            write_to_json(curr_data, curr_data["id"], extension="json", out_dir=args.out_dir)
