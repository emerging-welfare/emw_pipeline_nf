#!/usr/bin/env python3
import os,argparse
import geograpy
import requests 
from bs4 import BeautifulSoup
import json
from geopy.geocoders import Nominatim
import pandas as pd 
from geopy.extra.rate_limiter import RateLimiter
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

    
def cityDic(places):
    geolocator = Nominatim(user_agent="specify_your_app_name_here")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
    df = pd.DataFrame({'city': places})
    df['location'] = df['city'].apply(geocode)
    df['address']=df['location'].apply(lambda loc: loc.address if loc else None)
    df['lat']=df['location'].apply(lambda loc: tuple(loc.point)[0] if loc else None)
    df['lon']=df['location'].apply(lambda loc: tuple(loc.point)[1] if loc else None)
    df.drop(['location'],axis=1,inplace=True)
    return json.loads(df.to_json(orient='records'))


if __name__ == '__main__':
    INFILE = get_args()
    OUTFILE = get_basename(INFILE)+".placeTagger.json"
    with open(OUTFILE, "w") as fw:
        with open (INFILE,'r') as fr:
            input=json.load(fr)
            places = geograpy.get_place_context(text=" ".join(input["eventSenteces"]))
            placesList=cityDic(places.cities)
            placesList.insert(0,input)
            #strOutput=" ".join([str(cityDic) for cityDic in placesList]).replace('\'',"").replace("{","\n{").lstrip("\n")
            #fw.write(INFILE+"\n")
        json.dump(placesList , fw, indent=4)

