#Abdurrahman Beyaz. abdurrahmanbeyaza@gmail.com
"""
This class is one of component of the pipeline.It reads a given json files as a batch and send request to FLASK documenet classifier API.
This component may be positioned either as first where the news articles are already in JSON format, or as second after the news articles that are in formatted stuctured like HTML converted to JSON format.
the lines that end with '#' must be used in case of this component is used as first and lines that end with '##' must be used in case of this component is used as second. 
"""

import argparse
import json
import requests
import re
from utils import write_to_json
from utils import dump_to_json
from utils import read_from_json
from utils import change_extension
from datetime import datetime # can be not used check it 

def get_args():
    '''
    This function parses and return arguments passed in
    '''
    parser = argparse.ArgumentParser(prog='classifier.py',
                                     description='Document FLASK SVM Classififer Application ')
    parser.add_argument('--input_files', help="Input file")
    parser.add_argument('--out_dir', help="output folder")
    parser.add_argument('--cascaded', help="enable cascaded version" ,action="store_true",default=False)
    parser.add_argument('--first', help="enable cascaded version" ,action="store_true",default=False)
    args = parser.parse_args()

    return(args)

def request(texts):
    r = requests.post(url = "http://localhost:5000/queries", data = {'texts':texts},json={"Content-Type":"application/json"})
    return json.loads(r.text)

if __name__ == "__main__":
    args = get_args()
    jsons = []
    if args.first:
        files=args.input_files.strip("[ ]").split(",")
        for filename in files:
            filename=filename.strip("' ")
            jsons.append(read_from_json(filename)) 
    else:
        files = eval(args.input_files) 
        for filename in files:
            filename=filename.strip("' ")
            read_file=read_from_json(args.out_dir+filename)
            if read_file=="":continue 
            jsons.append(read_file) 
    
    rtext = request([data["text"] for data in jsons])
    event_sentences = rtext["event_sentences"]
    output_data = []
    for i,data in enumerate(jsons):
        out = int(rtext["outputs"][i])
        data["doc_label"] = out
        data["length"] = len(data["text"])
        out_sentences= event_sentences.pop(0)
        data["sentences"]= out_sentences if len(out_sentences)>0 else []
        keys=data.keys()
        if "id" not in keys and 'url' in keys:
            data["id"]=data["url"].replace(":","_").replace("/","_")+ datetime.now().strftime("%f")
        else:
            # if a document doesn't have id nor url fields, use the filename as id (i.e. url)
            data["id"] = files[i]
        #output_data.append(dump_to_json(data))
        write_to_json(data, data["id"], extension="json", out_dir=args.out_dir) 
        if (out==1 and args.cascaded) or (not args.cascaded): 
            # if cascaded is on then document label must be 1 in order to the document to pass to the next level.
            # where if the cascaded option is false that means there will not be any filter apply and all the files should pass to next level.
            output_data.append(args.out_dir+change_extension(data["id"],".json"))
        
    if len(output_data)>0:
        print(str(output_data))
