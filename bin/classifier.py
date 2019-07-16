#!/usr/bin/env python3
import argparse
import json 
import requests 
import pandas as pd 
from nltk import sent_tokenize
import pickle
def get_args():
    '''
    This function parses and return arguments passed in
    '''
    parser = argparse.ArgumentParser(prog='classifier.py',
                                     description='Document FLASK SVM Classififer Application ')
    parser.add_argument('fasta', help="path to fasta input file")
    args = parser.parse_args()
                                     
    infile = args.fasta
                                     
    return(infile)

def request(id,text):
    r = requests.post(url = "http://host.docker.internal:5000/queries", data = {'identifier':id,'text':text},json={"Content-Type":"application/json"})     
    return json.loads(r.text)

def get_basename(filename):
    dotsplit = filename.split(".")
    if len(dotsplit) == 1 :
        basename = filename
    else:
        basename = ".".join(dotsplit[:-1])
        if len(basename.split("."))!=1:
            basename = ".".join(basename.split(".")[:-1])
    return(basename)

if __name__ == "__main__":
    INFILE = get_args()
    OUTFILE = get_basename(INFILE)+".classifier.json"
    #with open("/nextflow_test/20180919_protest_classifier-Matthews-70onTest29onChina.pickle","rb") as f :
    #        classifer= pickle.load(f)

    with open (INFILE,'r') as fr:
        input=json.load(fr)
    #protestO= str(int(classifer.predict([input["text"]])[0]))
    rtext = request(id=input["identifier"],text=input["text"])
    #eventSentences=sent_tokenize(input["text"])[0:2]
    try:
        if(rtext["output"]=="0"):OUTFILE = get_basename(INFILE)+".0classifier.json"
        if(rtext["output"]=="1"):OUTFILE = get_basename(INFILE)+".classifier.json"
        with open(OUTFILE, "w") as fw:
            #output={"identifier":input["identifier"],"title":input["title"],"length":len(input["text"]),"text":input["text"],"output":protestO,"eventSenteces":eventSentences}
            output={"identifier":input["identifier"],"title":input["title"],"length":len(input["text"]),"text":input["text"],"output":rtext["output"],"eventSenteces":rtext["eventSenteces"]}
            json.dump(output ,fw , indent=4)
    except Exception as er: 
        print(INFILE,"\n",er.args)
    

    
