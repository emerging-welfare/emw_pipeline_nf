import subprocess
import os
import time 
import requests
import json
import pandas  as pd
import argparse 

def get_args():
    '''
    This function parses and return arguments passed in
    '''
    parser = argparse.ArgumentParser(prog='bootstrap.py',
                                     description='bootstrap is a script to execute nextflow and generate reports ')
    parser.add_argument('--input', help="""--input <input dir/input pattern> inputpath/pattern of input file """,nargs='?',default=None)
    parser.add_argument('-resume',help="""The `-resume` option skips the execution of any step that has been processed in a previous 
execution. """,action='store_true')
    parser.add_argument('--output',help="output folder name",nargs='?',default=None)
	
    args = parser.parse_args()                                                                 
    parameters=""
    if args.input is not None:
        parameters=parameters+"--input {0}".format(args.input)
    if args.resume:
        parameters=parameters+" -resume"
    if args.output is not None:
        parameters=parameters+" --output {0}".format(args.output)
                                     
    return(parameters)

def executeNF(fname):
    _="nextflow "+fname
    nf= os.popen(_).read()
    Slist=nf.split("\n")
    worklist=[]
    for x in range(3,len(Slist)):
         worklist.append(Slist[x])
    
    return [w.split() for w in worklist]

def todf(wl):
    try:
        df=pd.DataFrame(wl,columns=["hashing","process","process 1",">", "class_name","class_number"])
        df.drop(">",axis=1,inplace=True)
        df["processes"]=df["process"]+" "+df["process 1"]
        df.drop("process",axis=1,inplace=True)
        df.drop("process 1",axis=1,inplace=True)
        df=df[["hashing","processes","class_name","class_number"]]
        df["hashing"]=df["hashing"].str.strip("[]")
        df["fileName"]=None
        df["Odir"]=None
        df["Opreview"]=None
        df["OLast_modified_date"]=None
        df["OCreated_date"]=None
        df["class_number"]=df["class_number"].str.strip("()")
        df=df[~df["hashing"].isnull()]
        df=df[df["processes"]=="Submitted process"]
        return df
    except Exception as err:
        print(wl,"\n",err.with_traceback())
        raise RuntimeError()
def getFFN(path,stratW):
    for x in os.listdir(path):
        if (x.startswith(stratW)):
            return os.path.join(path,x)
def summarizedf(ds,gby="filename",toexcel=True):
    gr=ds.groupby(["fileName"])
    dicss=[]
    for key,value in gr.groups.items():
        places=None
        tt=None
        _=value.tolist()
        fInfo=ds.ix[_][ds.ix[_]["class_name"]=="clean"]["Opreview"].tolist()[0]
        output=ds.ix[_][ds.ix[_]["class_name"]=="classifier"]["Opreview"].tolist()[0]["output"]
        fInfo["protest"]=output
        dtc=ds.ix[_][ds.ix[_]["class_name"]=="DTC"]["Opreview"].tolist()[0]["publish data"]
        fInfo["DTC"]=dtc
        if(int(output)==1):
                places=ds.ix[_][ds.ix[_]["class_name"]=="placeTagger"]["Opreview"].tolist()[0][1:]
                tt=ds.ix[_][ds.ix[_]["class_name"]=="temporalTagger"]["Opreview"].tolist()[0][1:]
        fInfo["places"]=places
        fInfo["temporalTagger"]=tt
        dicss.append(fInfo)
        if toexcel :pd.DataFrame(dicss).to_excel("Process_Summary"+time.strftime("%H-%M-%Y%m%d")+".xlsx")
    return pd.DataFrame(dicss)

def outputFilter (nfo):
    nfOutput=[]
    for i,x in enumerate(nfo):
        if len(x)==5:
           nfOutput=nfo[i+1:] 
           break
    return nfOutput

def getAlldir(df,file):
    for _,p in df.iterrows():
        #if _ < 4 : continue;
        hdir=p["hashing"].split("/")
        fpath=getFFN(os.path.join(file,hdir[0]),hdir[1])
        matching = [s for s in os.listdir(fpath) if p["class_name"]+".json" in s]
        if len(matching)>1:
            print("there are more than 1 matched file")
            break
        path=os.path.join(fpath,matching[0])
        df.at[_,"Odir"]=path
        with open(path,"r") as pr:
            df.at[_,"Opreview"]=json.load(pr)
        df.at[_,"fileName"]= df.at[_,"Opreview"][0]["identifier"].split(".")[0] if isinstance(df.at[_,"Opreview"], list) else df.at[_,"Opreview"]["identifier"].split(".")[0]
        df.at[_,"OLast_modified_date"]=time.ctime(os.path.getmtime(path))
        df.at[_,"OCreated_date"]=time.ctime(os.path.getctime(path))
    return df

if __name__ == "__main__":
    workdir=os.path.join(os.getcwd(),"work")
    args=get_args()
    wl=executeNF("run emw_pipeline.nf"+args) 
    nfop=outputFilter(wl)
    df=getAlldir(todf(nfop),workdir)
    df.sort_values(by=["fileName","OLast_modified_date"]).set_index("fileName").to_excel(time.strftime("%H-%M-%Y%m%d")+".xlsx")
    ds=summarizedf(df)
    print("All done\n","Reports have been created successfully")