#!/usr/bin/env python
import subprocess
from subprocess import STDOUT,PIPE,CalledProcessError
import argparse
import json
from utils import load_from_json
from utils import dump_to_json

def get_args():
    parser = argparse.ArgumentParser(prog='PublishDateGraper_DTC-nextflow.py',
                                         description='extract PD from webpages')
    parser.add_argument('--input_dir', help="path to input folder")
    parser.add_argument('--data', help="Serialized json string")
    parser.add_argument('--no_byte', help="If html file needs to be read with 'r' tag.", action="store_true")
    args = parser.parse_args()

    return(args)

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
    jardir="/emw_pipeline_nf/bin/DTC_Nextflow"
    args = get_args()
    with open("asd", "w") as f:
        f.write(args.data)
    data = load_from_json(args.data)
    filename = args.input_dir + "/" + data["id"]

    if args.no_byte:
        with open(filename,'r') as fr:
            html_string = str(fr.read())
    else:
        with open(filename,'rb') as fr:
            html_string = str(fr.read())

    compileCmd = 'javac -cp .:{0}/dct-finder-2015-01-22.jar:{0}/commons-lang3-3.8.1.jar:{0}/commons-cli-1.4.jar  {0}/main.java -d .'.format(jardir)
    excuteCmd = 'java -cp .:{0}/dct-finder-2015-01-22.jar:{0}/commons-lang3-3.8.1.jar:{0}/commons-cli-1.4.jar DTC_Nextflow.main {1}' .format(jardir, html_string)
    compiled = compile_java(compileCmd)
    pd = execute_java(excuteCmd)
    data["publish_time"] = pd

    print(dump_to_json(data))
