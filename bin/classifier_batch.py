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
    files = eval(args.input_files) #untagge it when doc classifier component its not the first 
    jsons = []
    for filename in files:
        filename=filename.strip("' ")
        #with open(args.out_dir+filename, "r", encoding="utf-8") as f:
        #    jsons.append(json.loads(f.read()))
        jsons.append(read_from_json(args.out_dir+filename)) # when doc classifier component its not the first 200 finish
        #jsons.append(read_from_json(filename)) #when doc classifier component is first
    rtext = request([data["text"] for data in jsons])
    event_sentences = rtext["event_sentences"]
    output_data = []
    for i,data in enumerate(jsons):
        out = int(rtext["outputs"][i])
        data["doc_label"] = out
        data["length"] = len(data["text"])
#to activate the filter untagge the below condition and untag line #128 on  bin/classifier/classifier_batch_flask.py  
      #  if out == 0:
      #      write_to_json(data, data["id"], extension="json", out_dir=args.out_dir)     
      #      output_data.append(dump_to_json(data)) # remove it 
      #  if out == 1:
        data["sentences"] = event_sentences.pop()
        output_data.append(dump_to_json(data))

    if len(output_data) > 0:
        str_out = str(output_data)
#attemp to solve issue#11
#        while len(str_out) > 65533:
#            output_data.pop()
#            str_out = str(output_data)
#
        print(str(output_data))
