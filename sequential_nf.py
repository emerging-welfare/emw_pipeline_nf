import subprocess
import os
import time 
import requests

os.environ['PYTHONPATH']="/emw_pipeline_nf/bin"
l="http://localhost:"
ports=["5000/","4999/","4998/","4996/"] #used ports 
links=[l+ p for p in ports] #l+ports 
APIpaths=["classifier/classifier_flask.py ",
"sent_classifier/classifier_flask.py","token_classifier/classifier_flask.py","violent_classifier/classifier_flask.py"] # API paths 
pyscript=["python3 /emw_pipeline_nf/bin/"+x for x in APIpaths]
nextflowOP=[] #nextflow stdouts 
for x,l in enumerate(links): 
    script="nextflow run emw_pipeline.nf"
    while 1: # while there is no answer from the API, wait
            try:
                r = requests.get(url = l) 
                print(pyscript[x]," is working on  ",l ,"tmux session name ",str(x))
                break
            except Exception:
                tmuxop=os.popen('tmux ls').read() # to prevent dublicated session
                if len(tmuxop.split(":"))>0:
                    if(tmuxop.split(":")[0]!=str(x)): 
                        os.popen('tmux new-session -d -s'+ str(x)+" \'"+pyscript[x]+"\'" )
                if len(tmuxop)==0:
                        os.popen('tmux new-session -d -s'+ str(x)+" \'"+pyscript[x]+"\'" )
            time.sleep(20)
    if x==0:
        _=os.popen(script).read()
        nextflowOP.append(_)
    elif x==len(APIpaths)-1:
        _=os.popen(script+" -resume -with-trace trace.txt").read() # execute nextflow run with resume and trace report 
        nextflowOP.append(_)
    else :
        _=os.popen(script+" -resume").read() # execute nextflow run with resume after first time
        nextflowOP.append(_)
    print("tmux kill-session -t "+str(x))
    os.popen("tmux kill-session -t "+str(x) )
#print(nextflowOP)
with open("nextflow_output.txt","w") as r :
    r.write("".join(nextflowOP))

