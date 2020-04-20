import argparse
import json
import requests
from utils import load_from_json, write_to_json
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

if __name__ == "__main__":

    trigger_label_list = ['arm_mil', 'demonst', 'ind_act', 'group_clash']
    part_label_list = ['halk', 'militan', 'aktivist', 'köylü', 'öğrenci', 'siyasetçi', 'profesyonel', 'işçi', 'esnaf/küçük üretici', "No"]
    org_label_list = ['Militant_Organization', 'Political_Party', 'Chambers_of_Professionals', 'Labor_Union', 'Grassroots_Organization', "No"]

    args = get_args()
    sent_list = args.data.strip("[ ]").split(",")

    sent_labels = [0] * len(sent_list)
    trigger_labels = [0] * len(sent_list)
    part_labels = [0] * len(sent_list)
    org_labels = [0] * len(sent_list)
    for sent in sent_list:
        sent_num, sent_label, trigger, part, org = sent.strip().split(":")[1:]
        sent_labels[int(sent_num)] = int(sent_label)
        trigger_labels[int(sent_num)] = trigger_label_list[int(trigger)]
        part_labels[int(sent_num)] = part_label_list[int(part)]
        org_labels[int(sent_num)] = org_label_list[int(org)]

    filename = sent_list[0].strip().split(":")[0]
    with open(args.input_dir + filename, "r", encoding="utf-8") as f:
        json_data = json.loads(f.read())

    json_data["sent_labels"] = sent_labels
    json_data["trigger_semantic"] = trigger_labels
    json_data["participant_semantic"] = part_labels
    json_data["organizer_semantic"] = org_labels

    write_to_json(json_data, filename, out_dir=args.out_dir)
