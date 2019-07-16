#!/usr/bin/env python3
import os,argparse
import geograpy
import requests 
from bs4 import BeautifulSoup
import json

def get_args():
    '''
        This function parses and return arguments passed in
        '''
    parser = argparse.ArgumentParser(prog='placeTagger.py',description='Extract place names from a text, and add context to those names -- for example distinguishing between a country, region or city.')
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

def HTMLDic(c,html):
    if html==None:
        return {"City":c,
                "Country":None , 
                "Population":float("nan") ,#soup[3].text.split()[-1],
                "latitude":None,
                "longitude":None
                }
    soup = BeautifulSoup(html,'lxml').findAll("td")
    if(len(soup[3].text.split("population"))>1):
        po=float(soup[3].text.split("population")[1].strip().split()[0].rstrip(',').replace(",",""))
    else:
        po=float("nan")    
    dic={"City":c,
     "Country":soup[2].text.rstrip("\n"), 
     "Population":po,#soup[3].text.split()[-1],
     "latitude":soup[4].text,
     "longitude":soup[5].text}
    return dic

def getCityHTML(c):
    html=None
    URL = "http://www.geonames.org/search.html?q=$&country="
    HEADERS={"Host": "www.geonames.org",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
            "Referer": "http://www.geonames.org/istanbul.html",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language":"en-US,en;q=0.9,ar;q=0.8,tr;q=0.7"
            }
    URL=URL.replace("$",c)
    # sending get request and saving the response as response object 
    r = requests.get(url = URL,headers=HEADERS) 
    soup = BeautifulSoup(r.text,'lxml')
    table=soup.find("table", {"class":"restable"}).findAll("tr")
    for cell in range(2,len(table)-2):
        if table[cell].findAll("td")[1].find("a",href=True).text==c : 
            html=str(table[cell])
            break
    return html
    
def cityDic(c):
    return HTMLDic(c,getCityHTML(c))


if __name__ == '__main__':
    INFILE = get_args()
    OUTFILE = get_basename(INFILE)+".placeTagger.json"
    with open(OUTFILE, "w") as fw:
        with open (INFILE,'r') as fr:
            input=json.load(fr)
            places = geograpy.get_place_context(text=" ".join(input["eventSenteces"]))
            placesList=[cityDic(city) for city in places.cities]
            placesList.insert(0,input)
            #strOutput=" ".join([str(cityDic) for cityDic in placesList]).replace('\'',"").replace("{","\n{").lstrip("\n")
            #fw.write(INFILE+"\n")
        json.dump(placesList , fw)

