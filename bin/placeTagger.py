#!/usr/bin/env python3
import argparse
import geograpy
import requests
import json
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from utils import load_from_json
from utils import write_to_json

def get_args():
    '''
        This function parses and return arguments passed in
        '''
    parser = argparse.ArgumentParser(prog='placeTagger.py',description='Extract place names from a text, and add context to those names -- for example distinguishing between a country, region or city.')
    parser.add_argument('--data', help="Serialized json string")
    parser.add_argument('--out_dir', help="Output folder")
    args = parser.parse_args()
    return args

def cityDic(places):
    geolocator = Nominatim(user_agent="specify_your_app_name_here")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
    place_dicts = []
    for place in places:
        place_dict = {"text":place, "address":"", "latitude":"", "longtitude":""}
        location = geocode(place)
        if location:
            place_dict["address"] = location.address
            point = tuple(location.point)
            place_dict["latitude"] = point[0]
            place_dict["longtitude"] = point[1]

        place_dicts.append(place_dict)
    return place_dicts

if __name__ == '__main__':
    args = get_args()
    data = load_from_json(args.data)

    place_tags = []
    # TODO : Process only sentences with label 1
    for sentence in data["event_sentences"]:
        places = geograpy.get_place_context(text=sentence)
        place_dicts = cityDic(places.cities) # Only cities ???
        place_tags.append(place_dicts)

    data["place_tags"] = place_tags
    write_to_json(data, data["id"], extension="json", out_dir=args.out_dir)
