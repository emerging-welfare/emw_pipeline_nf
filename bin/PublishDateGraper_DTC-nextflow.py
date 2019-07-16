#!/usr/bin/env python

import os,subprocess
from subprocess import STDOUT,PIPE,CalledProcessError
import argparse
import json

def get_args():
    parser = argparse.ArgumentParser(prog='PublishDateGraper_DTC-nextflow.py',
                                         description='extract PD from webpages')
    parser.add_argument('path', help="path to input file")

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

def compile_java(compileCmd):
    try:
        cmd = compileCmd.split()
        proc = subprocess.Popen(cmd, stdout=PIPE, stderr=STDOUT)
        stdout,stderr = proc.communicate()
        return stdout
    except  CalledProcessError as e:
        print (e)
def execute_java(excuteCmd):
    try:
        cmd = excuteCmd.split()
        proc = subprocess.Popen(cmd, stdout=PIPE, stderr=STDOUT)
        stdout,stderr = proc.communicate()
        stdout=stdout.decode('utf-8').replace('\n','\t').split('\t')
        return stdout[1]
    except  CalledProcessError as e:
        print (e)
    



if __name__ == "__main__":
    jardir="/nextflow_test/bin/DTC_Nextflow"
    INFILE = get_args()
    OUTFILE = get_basename(INFILE)+".DTC.json"
    content=''
    with open(OUTFILE, "w") as fw:
        with open (INFILE,'r',encoding="latin1") as fr:
            content=fr.read()
        compileCmd='javac -cp .:{0}/dct-finder-2015-01-22.jar:{0}/commons-lang3-3.8.1.jar:{0}/commons-cli-1.4.jar  {0}/main.java -d .'.format(jardir)
        excuteCmd = 'java -cp .:{0}/dct-finder-2015-01-22.jar:{0}/commons-lang3-3.8.1.jar:{0}/commons-cli-1.4.jar DTC_Nextflow.main {1}' .format(jardir,content)
        compiled=compile_java(compileCmd)
        pd=execute_java(excuteCmd)
        output={"identifier":get_args(),"publish data":pd}
        json.dump(output,fw, indent=4)
