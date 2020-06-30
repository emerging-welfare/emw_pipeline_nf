import json
import argparse
from collections import Counter

"""
This script constructs an event database from the given output of the pipeline.
This process includes:
  - Applying cascading mechanism if necessary
  - Taking each cluster as an event and finalizing each event's arguments
"""

# TODO : We are doing coreference in sentence level.
# So if sent_cascade is not used, then we may not have coreference information for some of the triggers.
# If it is used we may have sentences where there are no triggers.

# TODO : give "html_place" precedence and if there is none use "place" and "flair".

def get_args():
    '''
    This function parses and return arguments passed in
    '''
    parser = argparse.ArgumentParser(prog='construct_event_database.py')
    parser.add_argument('--input_file', help="Input json file")
    parser.add_argument('--out_file', help="Output json file")
    parser.add_argument('--sent_cascade', help="If true: Negative sentences' token labels are negative", default="false")
    args = parser.parse_args()

    return(args)

def get_span(sent_tokens, span):
    return sent_tokens[span[0]:span[1]+1] # spans were exlusive

def get_place_coordinates(place_name):
    # TODO : check ~/geonames/README.txt
    # TODO : Fill here -> return "Error" if not place name or state or district!
    # TODO : In order: check if state, check if district, check if province from dictionaries with lat and long, geopy(towns,villages,not place name)
    # TODO : Can geopy be run on local?
    return 0.0, 0.0

def is_foreign_country(place_name):
    # TODO : check with a dictionary containing country names and capitals
    return False

if __name__ == "__main__":
    args = get_args()
    input_file = open(args.input_file, "r", encoding="utf-8")
    out_file = open(args.out_file, "w", encoding="utf-8")

    for i, json_data in enumerate(input_file):
        json_data = json.loads(json_data)
        clusters = json_data["event_clusters"]

        # TODO : If sent_cascade == "false", add another for loop going over other sentences and collect information.
        # -> How do we add this info to other events since we won't know which one they belong

        for cluster in clusters:
            out_json = {}

            all_place = Counter()
            trig_sem = Counter()
            part_sem = Counter()
            org_sem = Counter()
            for sent_idx in cluster:
                # TODO : What else do we need from this loop? (trigger, etime, fname, participant, organizer, target)?
                sent_tokens = json_data["tokens"]

                # Place
                curr_place = json_data["place"][sent_idx]
                for p in curr_place:
                    all_place[get_span(sent_tokens, p)] += 1

                curr_flair = json_data["flair"][sent_idx]
                for p in curr_flair:
                    all_place[get_span(sent_tokens, p)] += 1

                # TODO : Get all the other stuff here

                # Semantic stuff
                trig_sem[json_data["trigger_semantic"][sent_idx]] += 1
                part_sem[json_data["participant_semantic"][sent_idx]] += 1
                org_sem[json_data["organizer_semantic"][sent_idx]] += 1

            # TODO : Check if there is any "html_place". If there is process it.

            # Place
            if any([is_foreign_country(place_name) for place_name i all_place]):
                # TODO : Discard event or whole document?
                # TODO : Discard or keep somewhere else?
                continue

            # We will use the most common place name if it is a place name and it is from target country.
            for place_name in all_place.most_common():
                latitude, longtitude = get_place_coordinates(place_name)
                if latitude != "Error":
                    break

            # NOTE : If no place name is found, we discard the event!
            if latitude == "Error":
                continue


            # TODO : What else is needed? -> write all info even if they won't be used
            # TODO : Name these according to glocon input
            out_json["latitude"] = latitude
            out_json["longtitude"] = longtitude
            # TODO : Should we check for if these exist in data?
            out_json["year"] = json_data["html_year"]
            out_json["month"] = json_data["html_month"]
            out_json["day"] = json_data["html_day"]
            out_json["trigger_semantic"] = trig_sem.most_common(1)[0]
            # TODO : Not only the most common, but take all of them from most common to least and put them in ordered keys indicated below
            out_json["participant_semantic"] = part_sem.most_common(1)[0]
            out_json["organizer_semantic"] = org_sem.most_common(1)[0]

            # TODO :
            # eventcategory, participant1category, ..., participant4category
            # organizer1category, ..., organizer9category, eventethnicity, eventideology, urbanrural
            # day, month, year, CityCode, latitude, longtitude

            # from geopy.geocoders import Nominatim
            # geolocator = Nominatim(user_agent="GLOCON")
            # location = geolocator.geocode(row[col])
            # print(location.latitude, location.longitude)

            out_file.write(json.dumps(out_json) + "\n")

    input_file.close()
    out_file.close()
