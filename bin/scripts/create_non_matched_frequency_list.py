import json
from collections import Counter
import unicodedata
from nltk.corpus import stopwords
import sys

input_filename = sys.argv[1] # processed_positive_docs.json
out_filename = sys.argv[2] # a tsv file
place_folder = sys.argv[3] # geocoding_dictionaries folder
target_language = "portuguese"

def read_alternatives_tsv(tsv_filename): # returns a dict("alternative_name"->"place_name")
    with open(tsv_filename, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    out_dict = {}
    for line in lines[1:]: # first line is header
        alt_name, place_name = line.split("\t")
        out_dict[alt_name] = place_name

    return out_dict

def get_span(sent_tokens, span):
    return " ".join(sent_tokens[span[0]:span[1]+1]) # spans were exlusive


state_alts = read_alternatives_tsv(place_folder + "/state_alternatives.tsv")
dist_alts = read_alternatives_tsv(place_folder + "/district_alternatives.tsv")
foreign_alts = read_alternatives_tsv(place_folder + "/foreign_alternatives.tsv")
with open(place_folder + "/ignore_list.json", "r", encoding="utf-8") as f:
    ignore_list = json.loads(f.read())

ignore_list = stopwords.words(target_language) + ignore_list + [str(i) for i in range(1000)] + [str(i) for i in range(1980,2023)] + ["0" + str(i) for i in range(1,10)]

all_places = Counter()
with open(input_filename, "r", encoding="utf-8") as input_file:
    for line in input_file:
        data = json.loads(line)
        html_place = data.get("html_place", "").lower() # might not exist in data
        if html_place:
            html_place = unicodedata.normalize("NFKD", html_place)
            all_places[html_place] += 1

        for sent_idx, place_list in data["place"].items():
            sent_tokens = data["tokens"][int(sent_idx)]
            for p in place_list:
                p = unicodedata.normalize("NFKD", get_span(sent_tokens, p).lower())
                all_places[p] += 1

    with open(out_filename, "w", encoding="utf-8") as out_file:
        out_file.write("place_name\tfrequency\n")
        for place, freq in all_places.most_common():
            # These could be the same if, but we might want to save them or something.
            if place in ignore_list:
                continue
            elif foreign_alts.get(place, ""):
                continue
            elif state_alts.get(place, ""):
                continue
            elif dist_alts.get(place, ""):
                continue

            out_file.write("{}\t{}\n".format(place, freq))
