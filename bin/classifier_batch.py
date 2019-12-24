import argparse
import json
import requests
import re
from utils import write_to_json
from utils import dump_to_json
from utils import read_from_json
def get_args():
    '''
    This function parses and return arguments passed in
    '''
    parser = argparse.ArgumentParser(prog='classifier.py',
                                     description='Document FLASK SVM Classififer Application ')
    parser.add_argument('--input_files', help="Input file")
    parser.add_argument('--out_dir', help="output folder")
    args = parser.parse_args()

    return(args)

def request(texts):
    r = requests.post(url = "http://localhost:5000/queries", data = {'texts':texts},json={"Content-Type":"application/json"})
    return json.loads(r.text)

if __name__ == "__main__":
    args = get_args()
    # jsons = eval(re.sub(r"\[QUOTE\]", r"'", args.data))
    #files=args.input_files.strip("[ ]").split(",") # when doc classifier component is first
    files = eval(args.input_files) #when doc classifier component its not the first 
    jsons = []
    for filename in files:
        filename=filename.strip("' ")
        jsons.append(read_from_json(args.out_dir+filename)) #when doc classifier component its not first
        #jsons.append(read_from_json(filename)) #when doc classifier component is first
    rtext = request([data["text"] for data in jsons])
    event_sentences = rtext["event_sentences"]
    output_data = []
    for i,data in enumerate(jsons):
######## those are only for 20_K_Sample expirement 
        if "token_labels" in data:
                del data["token_labels"]
        if "tokens" in data:
                del data["tokens"]
########
        out = int(rtext["outputs"][i])
        data["doc_label"] = out
        data["length"] = len(data["text"])
        if out == 0:
            write_to_json(data, data["id"], extension="json", out_dir=args.out_dir)     
        if out == 1:
            data["sentences"] = event_sentences.pop(0)
            write_to_json(data, data["id"], extension="json", out_dir=args.out_dir) 
            output_data.append(args.out_dir+change_extension(data["id"],".json"))
    print(str(output_data))
