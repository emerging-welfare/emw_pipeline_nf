import argparse
import json
import requests
from utils import write_to_json, read_from_json
import json
def get_args():
    '''
    This function parses and return arguments passed in
    '''
    parser = argparse.ArgumentParser(prog='violent_classifier.py',
                                     description='Violent FLASK Classififer Application ')
    parser.add_argument('--input_files', help="Input filenames")
    parser.add_argument('--input_dir', help="Input folder")
    parser.add_argument('--out_dir', help="Output folder")
    parser.add_argument('--language', help="The source language. Ex. 'english'")
    args = parser.parse_args()

    return(args)

def request(texts):
    r = requests.post(url = "http://localhost:4996/queries", json={'texts':texts})
    return json.loads(r.text)


if __name__ == "__main__":
    args = get_args()
    files=args.input_files.strip("[ ]").split(", ")
    jsons = [read_from_json(args.input_dir + "/" + filename) for filename in files]

    if len(jsons) > 0:
        rtext = request([data["text"] for data in jsons])
        for i, data in enumerate(jsons):
            data["violent"] = rtext["violent_output"][i]
            if args.language == "english":
                data["urbanrural"] = rtext["urbanrural"]

            write_to_json(data, data["id"], extension="json", out_dir=args.out_dir)
