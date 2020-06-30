import json
import argparse
from collections import Counter
from geopy.geocoders import Nominatim

"""
This script constructs an event database from the given output of the pipeline.
This process includes:
  - Applying cascading mechanism if necessary
  - Taking each cluster as an event and finalizing each event's arguments
"""

# TODO : We are doing coreference in sentence level.
# So if sent_cascade is not used, then we may not have coreference information for some of the triggers.
# If it is used we may have sentences where there are no triggers.

def get_args():
    '''
    This function parses and return arguments passed in
    '''
    parser = argparse.ArgumentParser(prog='construct_event_database.py')
    parser.add_argument('-i', '--input_file', help="Input json file")
    parser.add_argument('-o', '--out_file', help="Output json file")
    parser.add_argument('-p', '--place_folder', help="A folder that contains state_names.txt and all_cities.tsv for target country.")
    parser.add_argument('--sent_cascade', help="If true: Negative sentences' token labels are negative", default="false")
    args = parser.parse_args()

    return(args)

def tsv_to_dict(tsv_filename):
    with open(tsv_filename, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    out_dict = {}
    for line in lines[1:]: # first line is header
        name, latitude, longtitude = line.split("\t")
        out_dict[name] = (float(latitude), float(longtitude))

    return out_dict

def get_span(sent_tokens, span):
    return " ".join(sent_tokens[span[0]:span[1]+1]) # spans were exlusive

def get_place_coordinates(place_name):
    place_name_lower = place_name.lower()
    if place_name_lower in state_names:
        # TODO : Return something else for statistics?
        return "Error", "Error"

    coords = city_dict.get(place_name_lower, [])
    if len(coords) > 0:
        return coords[0], coords[1]

    location = geolocator.geocode(place_name)
    if location != None and "India" in location.address:
        # TODO : Return something else for statistics?
        return location.latitude, location.longitude

    # TODO : Return something else for statistics?
    return "Error", "Error"

def is_foreign_country(place_name):
    # TODO : make this a dictionary?
    if place_name.lower() in foreign_places:
        return True
    return False


# Global stuff
args = get_args()
with open(args.place_folder + "/state_names.txt", "r", encoding="utf-8") as f:
    state_names = f.read().splitlines()

with open(args.place_folder + "/foreign_places.txt", "r", encoding="utf-8") as f:
    foreign_places = f.read().splitlines()

city_dict = tsv_to_dict(args.place_folder + "/all_cities.tsv")
geolocator = Nominatim(user_agent="GLOCON")

if __name__ == "__main__":
    input_file = open(args.input_file, "r", encoding="utf-8")
    out_file = open(args.out_file, "w", encoding="utf-8")

    for json_data in input_file:
        json_data = json.loads(json_data)
        clusters = json_data.get("event_clusters", [])

        # TODO : If sent_cascade == "false", add another for loop going over other sentences and collect information.
        # -> How do we add this info to other events since we won't know which one they belong

        if clusters == None: # Happens if there is only one positive sentence or no positive sentence
            sent_labels = json_data["sent_labels"]
            clusters = [[i for i in range(len(sent_labels)) if sent_labels[i] == 1]]

        if len(clusters[0]) == 0: # No positive sentence
            continue

        for cluster in clusters:
            out_json = {}

            all_place = Counter()
            trig_sem = Counter()
            part_sem = Counter()
            org_sem = Counter()
            triggers = []
            participants = []
            organizers = []
            targets = []
            fnames = []
            etimes = []
            for sent_idx in cluster:
                # TODO : What else do we need from this loop? (trigger, etime, fname, participant, organizer, target)?
                sent_tokens = json_data["tokens"]

                # Place
                curr_place = json_data["place"].get(sent_idx, [])
                for p in curr_place:
                    all_place[get_span(sent_tokens, p)] += 1

                curr_flair = json_data["flair"].get(sent_idx, [])
                for p in curr_flair:
                    all_place[get_span(sent_tokens, p)] += 1

                # Semantic stuff
                trig_sem[json_data["trigger_semantic"][sent_idx]] += 1
                part_sem[json_data["participant_semantic"][sent_idx]] += 1
                org_sem[json_data["organizer_semantic"][sent_idx]] += 1

                # Other stuff
                triggers.extend([get_span(sent_tokens, trig) for trig in json_data["trigger"].get(sent_idx, [])])
                participants.extend([get_span(sent_tokens, part) for part in json_data["participant"].get(sent_idx, [])])
                organizers.extend([get_span(sent_tokens, org) for org in json_data["organizer"].get(sent_idx, [])])
                targets.extend([get_span(sent_tokens, target) for target in json_data["target"].get(sent_idx, [])])
                fnames.extend([get_span(sent_tokens, fname) for fname in json_data["fname"].get(sent_idx, [])])
                etimes.extend([get_span(sent_tokens, etime) for etime in json_data["etime"].get(sent_idx, [])])

            # Html place
            latitude = "Error"
            html_place = json_data.get("html_place", "") # might not exist in data
            if html_place != "" and not is_foreign_country(html_place):
                latitude, longitude = get_place_coordinates(html_place)

            # Place
            if latitude == "Error": # if html_place failed
                if any([is_foreign_country(place_name) for place_name in all_place]):
                    # TODO : Discard event or whole document?
                    # TODO : Discard or keep somewhere else?
                    continue

                # We will use the most common place name if it is a place name and it is from target country.
                for place_name in all_place.most_common():
                    latitude, longitude = get_place_coordinates(place_name)
                    if latitude != "Error":
                        break

                # NOTE : If no place name is found, we discard the event!
                if latitude == "Error":
                    continue

            # TODO : CityCode?
            out_json["latitude"] = latitude
            out_json["longitude"] = longitude
            # TODO : Should we check for if these exist in data?
            out_json["year"] = json_data["html_year"]
            out_json["month"] = json_data["html_month"]
            out_json["day"] = json_data["html_day"]
            out_json["urbanrural"] = json_data["urbanrural"]
            out_json["eventcategory"] = trig_sem.most_common(1)[0][0]

            for j,part in enumerate(part_sem.most_common(4)):
                out_json["participant" + str(j) + "category"] = part[0]

            for j,org in enumerate(part_sem.most_common(9)):
                out_json["organizer" + str(j) + "category"] = org[0]

            # TODO : eventethnicity, eventideology

            out_file.write(json.dumps(out_json) + "\n")

    input_file.close()
    out_file.close()
