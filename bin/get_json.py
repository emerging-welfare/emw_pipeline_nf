import argparse
import json
from utils import dump_to_json

def get_args():
    '''
    This function parses and return arguments passed in
    '''
    parser = argparse.ArgumentParser(prog='classifier.py',
                                     description='Document FLASK SVM Classififer Application ')
    parser.add_argument('--input_file', help="Input file")
    args = parser.parse_args()

    return(args)

if __name__ == "__main__":
    args = get_args()

    with open(args.input_file, "r", encoding="utf-8") as f:
        data = json.loads(f.read())

    print(dump_to_json(data))
