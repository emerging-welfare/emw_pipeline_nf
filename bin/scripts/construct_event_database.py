import json
import argparse

"""
This script constructs an event database from the given output of the pipeline.
This process includes:
  - Applying cascading mechanism if necessary
  - Taking each cluster as an event and finalizing each event's arguments
"""

def get_args():
    '''
    This function parses and return arguments passed in
    '''
    parser = argparse.ArgumentParser(prog='construct_event_database.py')
    parser.add_argument('--input_file', help="Input file")
    parser.add_argument('--out_format', help="Output format (json | csv | xlsx)")
    # parser.add_argument('--doc_cascade', help="If true: Negative documents' all sentence and token labels are negative", action="store_true", default=False)
    # parser.add_argument('--sent_cascade', help="If true: Negative sentences' token labels are negative", action="store_true", default=False)
    parser.add_argument('--doc_cascade', help="If true: Negative documents' all sentence and token labels are negative", default="false")
    parser.add_argument('--sent_cascade', help="If true: Negative sentences' token labels are negative", default="false")
    args = parser.parse_args()

    return(args)

if __name__ == "__main__":
    args = get_args()

    input_file = open(args.input_file, "r", encoding="utf-8")
    for i, json_data in enumerate(input_file):
        json_data = json.loads(json_data)

        # TODO : continue
