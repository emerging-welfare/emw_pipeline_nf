import json
import argparse
from collections import Counter
from geopy.geocoders import Nominatim
import ipdb

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
    parser.add_argument('-p', '--place_folder', help="A folder that contains state_names.txt, foreign_places.txt and all_cities.tsv for target country.")
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
    global all_processed_place_names, state_name_fail, city_name_success, geopy_success, not_found_fail
    all_processed_place_names += 1
    place_name_lower = place_name.lower()
    if place_name_lower in state_names:
        state_name_fail += 1
        return "Error", "Error"

    coords = city_dict.get(place_name_lower, [])
    if len(coords) > 0:
        city_name_success += 1
        return coords[0], coords[1]

    location = geolocator.geocode(place_name)
    if location != None and "India" in location.address:
        geopy_success += 1
        return location.latitude, location.longitude

    not_found_fail += 1
    return "Error", "Error"

def is_foreign_country(place_name):
    # TODO : make this a dictionary?
    if place_name.lower() in foreign_places:
        return True
    return False


# GLOBAL STUFF
event_category_dict = {"demonst": "Demonstration", "arm_mil": "Armed Militancy", "group_clash": "Group Clash", "ind_act": "Industrial Action"}
 # TODO : What to do with "No"?
organizer_category_dict = {"Grassroots_Organization": "Grassroots Organization", "Political_Party": "Political Party",
                           "Chambers_of_Professionals": "Chambers of Professionals", "Labor_Union": "Labor Union",
                           "Militant_Organization": "Militant Organization", "No": "N-A"}
participant_category_dict = {"halk": "Masses", "militan": "Militant", "aktivist": "Activist",
                             "köylü": "Peasant", "öğrenci": "Student", "No": "N-A",
                             "siyasetçi": "Politician", "profesyonel": "Professional",
                             "işçi": "Proletariat", "esnaf/küçük üretici": "Petty Bourgeoisie"}

# For Statistics
total_documents = 0
no_pos_sent = 0
one_pos_sent = 0
total_events = 0
events_with_html_place = 0
events_with_place_name = 0
events_with_no_place_name = 0
foreign_place_name = 0
all_processed_place_names = 0
state_name_fail = 0
city_name_success = 0
geopy_success = 0
not_found_fail = 0

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

    # ipdb.set_trace()
    for json_data in input_file:
        json_data = json.loads(json_data)
        print(json_data["id"])
        clusters = json_data.get("event_clusters", [])
        total_documents += 1

        # TODO : If sent_cascade == "false", add another for loop going over other sentences and collect information.
        # -> How do we add this info to other events since we won't know which one they belong

        if clusters == None: # Happens if there is only one positive sentence or no positive sentence
            sent_labels = json_data["sent_labels"]
            pos_sents = [i for i in range(len(sent_labels)) if sent_labels[i] == 1]
            if len(pos_sents) > 0:
                clusters = [pos_sents]
                one_pos_sent += 1
            else:
                no_pos_sent += 1
                continue

        # Html place
        curr_place_name = ""
        latitude = "Error"
        html_place = json_data.get("html_place", "") # might not exist in data
        if html_place != "" and not is_foreign_country(html_place):
            latitude, longitude = get_place_coordinates(html_place)
            curr_place_name = html_place


        for cluster in clusters:
            total_events += 1
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
                str_sent_idx = str(sent_idx)
                sent_tokens = json_data["tokens"][sent_idx]

                # Place
                curr_place = json_data["place"].get(str_sent_idx, [])
                for p in curr_place:
                    all_place[get_span(sent_tokens, p)] += 1

                curr_flair = json_data["flair"].get(str_sent_idx, [])
                for p in curr_flair:
                    all_place[get_span(sent_tokens, p)] += 1

                # Semantic stuff
                trig_sem[json_data["trigger_semantic"][sent_idx]] += 1
                part_sem[json_data["participant_semantic"][sent_idx]] += 1
                org_sem[json_data["organizer_semantic"][sent_idx]] += 1

                # Other stuff
                triggers.extend([get_span(sent_tokens, trig) for trig in json_data["trigger"].get(str_sent_idx, [])])
                participants.extend([get_span(sent_tokens, part) for part in json_data["participant"].get(str_sent_idx, [])])
                organizers.extend([get_span(sent_tokens, org) for org in json_data["organizer"].get(str_sent_idx, [])])
                targets.extend([get_span(sent_tokens, target) for target in json_data["target"].get(str_sent_idx, [])])
                fnames.extend([get_span(sent_tokens, fname) for fname in json_data["fname"].get(str_sent_idx, [])])
                etimes.extend([get_span(sent_tokens, etime) for etime in json_data["etime"].get(str_sent_idx, [])])

            # Place
            if latitude == "Error": # if html_place failed
                if any([is_foreign_country(place_name) for place_name in all_place]):
                    # TODO : Discard event or whole document?
                    foreign_place_name += 1
                    continue

                # We will use the most common place name if it is a place name and it is from target country.
                for place_name in all_place.most_common():
                    latitude, longitude = get_place_coordinates(place_name[0])
                    if latitude != "Error":
                        curr_place_name = place_name[0]
                        break

                # NOTE : If no place name is found, we discard the event!
                if latitude == "Error":
                    events_with_no_place_name += 1
                    continue

                events_with_place_name += 1

            else:
                events_with_html_place += 1

            # Place
            out_json["CityCode"] = curr_place_name
            out_json["latitude"] = latitude
            out_json["longitude"] = longitude

            # TODO : Should we check for if these exist in data?
            out_json["year"] = json_data["html_year"]
            out_json["month"] = json_data["html_month"]
            out_json["day"] = json_data["html_day"]
            out_json["urbanrural"] = json_data["urbanrural"]

            # Semantic stuff
            out_json["eventcategory"] = event_category_dict[trig_sem.most_common(1)[0][0]]
            for j,part in enumerate(part_sem.most_common(4)):
                out_json["participant" + str(j) + "category"] = participant_category_dict[part[0]]

            for j,org in enumerate(org_sem.most_common(9)):
                out_json["organizer" + str(j) + "category"] = organizer_category_dict[org[0]]

            # Other stuff
            out_json["triggers"] = "\n".join(triggers)
            out_json["participants"] = "\n".join(participants)
            out_json["organizers"] = "\n".join(organizers)
            out_json["targets"] = "\n".join(targets)
            out_json["fnames"] = "\n".join(fnames)
            out_json["etimes"] = "\n".join(etimes)
            # TODO : eventethnicity, eventideology

            out_file.write(json.dumps(out_json) + "\n")

    input_file.close()
    out_file.close()

print("Out of %d documents processed, %d had no positive sentence and %d had only one positive sentence." %(total_documents, no_pos_sent, one_pos_sent))
print()
print("Total number of events encountered : %d" %total_events)
print("    %d of these used html_place as their final place name" %events_with_html_place)
print("    For the remaining %d events : " %(total_events - events_with_html_place))
print("        %d had succesfully obtained place names" %events_with_place_name)
print("        %d had foreign places" %foreign_place_name)
print("        %d had no usable place name" %events_with_no_place_name)
print()
print("Total number of processed place names with get_coordinates function : %d" %all_processed_place_names)
print("    %d of these were state names" %state_name_fail)
print("    %d of these were city names" %city_name_success)
print("    %d of these were decided to be place names in india by geopy" %geopy_success)
print("    %d of these failed all the way" %not_found_fail)
