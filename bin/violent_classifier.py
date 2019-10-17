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
    parser.add_argument('--data', help="Serialized json string")
    parser.add_argument('--out_dir', help="Output folder")
    args = parser.parse_args()

    return(args)

def request(id,text):
    r = requests.post(url = "http://localhost:4996/queries", json={'identifier':id,'text':text})
    return json.loads(r.text)


if __name__ == "__main__":
    args = get_args()
    #files = eval(args.data)
    data =[]
    with open(args.out_dir+args.data,"r") as f :
         data=json.loads(f.read())
    data["violent_label"] = request(id=data["id"],text=data["text"])
    write_to_json(data, data["id"], extension="json", out_dir=args.out_dir)
    
    #for filename in files:
    #   with open(args.out_dir + filename, "r", encoding="utf-8") as f:
    #       jsons.append(json.loads(f.read()))
    #for i,data in enumerate(jsons):
    #   data["violent_label"] = request(id=data["id"],text=data["text"])
    #   write_to_json(data, data["id"], extension="json", out_dir=args.out_dir)

   
    #rtext = request(str([data["text"] for data in jsons]))
    #all_texts_labels = rtext["output"]
    #output_data = list()
    #for i,data in enumerate(jsons):
    #    write_to_json(data, data["id"], extension="json", out_dir=args.out_dir)
