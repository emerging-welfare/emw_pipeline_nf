#!/usr/bin/env python3
import json
import os,argparse
from sutime import SUTime
import requests
def get_args():
    '''
        This function parses and return arguments passed in
        '''
    parser = argparse.ArgumentParser(prog='temporalTagger.py',description='SUTime is a library for recognizing and normalizing time expressions. That is, it will convert next wednesday at 3pm to something like 2016-02-17T15:00 (depending on the assumed current reference time). ')
    parser.add_argument('path', help="insert a vaild input ")
    args = parser.parse_args()
    infile = args.path
    return(infile)

def get_basename(filename):
    dotsplit = filename.split(".")
    if len(dotsplit) == 1 :
        basename = filename
    else:
        basename = ".".join(dotsplit[:-1])
        if len(basename.split("."))!=1:
            basename = ".".join(basename.split(".")[:-1])
    return(basename)

def request(id,eventSenteces):
    r = requests.post(url = "http://host.docker.internal:12345/tts", data = {'identifier':id,'eventSenteces':eventSenteces},json={"Content-Type":"application/json"}) 
    return json.loads(r.text)

if __name__ == '__main__':
    INFILE = get_args()
    OUTFILE = get_basename(INFILE)+".temporalTagger.json"
    with open(OUTFILE, "w") as fw:
        with open (INFILE,'r') as fr:
            #jar_files = os.path.join("/nextflow_test/bin/", 'jars')
            #print(jar_files)
            #sutime = SUTime(jars=jar_files, mark_time_ranges=True)
            input=json.load(fr)
            rtext=request(input["identifier"],input["eventSenteces"])
            #ojson=json.loads(json.dumps(sutime.parse(input["text"])))
            ins={"identifier":input["identifier"],"title":input["title"],"length":len(input["text"]),"text":input["text"],"temporalTagger":rtext["temporaltaggers"]}
            #ojson.insert(0,ins)
            #output=json.dumps(sutime.parse(input), sort_keys=True, indent=4)
        json.dump(ins,fw, indent=4)
        # Ignore converting links from HTML
            #fw.write(INFILE+"\n")
        #fw.write(output)
