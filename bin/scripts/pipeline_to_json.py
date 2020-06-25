import json
import argparse
import pandas as pd

# TODO : Think about the list of things below!
#  - Drop the text?
#  - Drop the sentences?
#  - Drop all tokens and only keep the predicted ones? -> We would keep each span as a list of words in that span
#  - Drop negative sentences?
#  - Instead of a dict for a tag, create one dict and make predictions a three membered tuple that also contains a tag info?

# TODO : Since each doc is independent, find a way to use them simultaneously. We can't load the whole document since it is huge!
# Possible solution -> chunking : Read some amount of lines and put them into a list. Process this list simultaneously and output the results.

def get_args():
    parser = argparse.ArgumentParser(prog='pipeline_to_json.py')
    parser.add_argument('-i', '--input_file', help="Input file")
    parser.add_argument('-o', '--out_file', help="Output file")
    parser.add_argument('-d', '--dates_and_places_file', default="" ,help="Dates file. A csv with url, date(YYYY/MM/DD) and place columns")
    args = parser.parse_args()

    return(args)

def filename_to_url(filename):
    url = re.sub(r"___?", r"://", filename)
    url = re.sub(r"_", r"/", url)
    return url

def postprocess_tokens_and_labels(data):
    """
    Turns "tokens" from a list to a list of lists. In doing so,
    handles "token_labels" turning them into spans and placing
    them into corresponding tag dictionaries.
    Example:

    Input has a sentence with "2" as its sent_idx :
    ["O", "B-trigger", "I-trigger", "O", "O", "B-place", "O", "B-place"]

    Output is added to multiple dictionaries :
    data["trigger"]["2"] = [(1,3)]
    data["place"]["2"] = [(5,6), (7,8)]
    """

    # Turning tokens from a list to a list of lists
    sent_idx = 0
    j = 0 # idx inside sentence
    prev_token_label = "O"
    start_idx = 0
    all_tokens = []
    for i, token in enumerate(data["tokens"]):
        if token == "SAMPLE_START":
            tokens = []
        elif token == "[SEP]":
            sent_idx += 1
            j = 0
            prev_token_label = "O"
            all_tokens.append(tokens)
            tokens = []
        else:
            tokens.append(token)
            token_label = data["token_labels"][i]

            # Handle spans
            if token_label == "O" and prev_token_label != "O":
                # Add to corresponding tag dictionary.
                # NOTE : All spans are exclusive!
                data[prev_token_label].setdefault(sent_idx, []).append((start_idx, j-1))
                prev_token_label = "O"

            elif token_label.startswith("B-"):
                if prev_token_label != "O":
                    data[prev_token_label].setdefault(sent_idx, []).append((start_idx, j-1))

                start_idx = j
                prev_token_label = token_label[2:]

            elif token_label.startswith("I-"):
                if prev_token_label == "O":
                    start_idx = j
                else:
                    if prev_token_label != token_label[2:]:
                        data[prev_token_label].setdefault(sent_idx, []).append((start_idx, j-1))
                        start_idx = j

                prev_token_label = token_label[2:]

            j += 1

    data["tokens"] = all_tokens
    return data

if __name__ == "__main__":
    args = get_args()

    out_file = open(args.out_file, "w", encoding="utf-8")
    if args.dates_and_places_file != "":
        dates_and_places = pd.read_csv(args.dates_and_places_file)

    # Start postprocessing
    with open(args.input_file, "r", encoding="utf-8") as input_file:
        for line in input_file: # For each document
            data = json.loads(line)

            # NOTE : These are kept as dicts instead of lists of lists because they are sparse and usually we deal with sentences individually.
            data["trigger"], data["participant"], data["organizer"], data["target"], data["fname"], data["etime"], data["place"], data["flair"] = [dict() for _ in range(8)]
            data = postprocess_tokens_and_labels(data)

            # Flair output
            # NOTE : We want to be able to get all spans in a sentence without going
            # through all spans in a document. That's why we do this.
            for (sent_idx, start_idx, end_idx) in data["flair_output"]:
                data["flair"].setdefault(sent_idx, []).append((start_idx, end_idx))

            # Date and place from html
            if args.dates_and_places_file != "":
                curr_url = filename_to_url(data["id"])
                matches = dates_and_places[dates_and_places.url == curr_url]
                if len(matches) > 0:
                    data["html_year"], data["html_month"], data["html_day"] = matches.iloc["date"].split("/")
                    if matches.iloc["place"] != "":
                        data["html_place"] = matches.iloc["place"]

            # Remove unnecessary keys
            data.pop("token_labels")
            data.pop("flair_output")
            data.pop("doc_label")

            out_file.write(json.dumps(data) + "\n")

    out_file.close()

"""
    Each line is :
    {
        id: "...",
        violent : 1,
        sent_labels : [0,1,0,0,1,1],
        event_clusters : [[1,4], [5]],
        trigger_semantic : [-1,"demonst",-1,-1,"demonst","group_clash"],
        participant_semantic : [-1,"halk",-1,-1,"halk","işçi"],
        organizer_semantic : [-1,"Political_Party",-1,-1,"Political_Party","Labor_Union"],
        sentences : ["A bird flew over Marakesh", "...", ...]
        text: "..."
        tokens: [["A", "bird", "flew", "over", "Marakesh"], [...], ...]
        trigger: {
            "1": [(3,3)]
            "3": [(1,2)] # We don't filter these regarding sent_labels yet.
            "4": [(4,5), (7,7)]
        }
        "participant": {}, # same as trigger
        "organizer": {}, # same as trigger
        "target": {}, # same as trigger
        "etime": {}, # same as trigger
        "fname": {}, # same as trigger
        "place": {}, # same as trigger
        "flair": {}, # same as trigger

        # Optional keys
        "html_place": "Bihar",
        "html_year": "1992",
        "html_month": "11",
        "html_day": "05",
    }
"""
