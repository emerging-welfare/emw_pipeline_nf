import argparse
import json
import requests
from utils import write_to_json
from utils import load_from_json
from utils import dump_to_json
import json
def get_args():
    '''
    This function parses and return arguments passed in
    '''
    parser = argparse.ArgumentParser(prog='violent_classifier.py',
                                     description='Violent FLASK Classififer Application ')
    parser.add_argument('--input_file', help="Input file")
    parser.add_argument('--out_dir', help="Output folder")
    args = parser.parse_args()

    return(args)

def request(id,text):
    r = requests.post(url = "http://localhost:4996/queries", json={'identifier':id,'text':text})
    return json.loads(r.text)


if __name__ == "__main__":
    args = get_args()
    if args.input_file != "": # Might happen when no document in the batch is predicted as positive
        with open(args.out_dir+args.input_file.strip(), "r", encoding="utf-8") as f:
             data = json.loads(f.read())

        r = request(id=data["id"],text=data["text"])
        data["is_violent"] = int(r["violent"])
        data["urbanrural"] = r["urbanrural"]
        write_to_json(data, data["id"], extension="json", out_dir=args.out_dir)
