import json
import argparse
from collections import Counter
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from nltk.corpus import stopwords
import os

"""
This script constructs an event database from the given output of the pipeline.
This process includes:
  - Applying cascading mechanism if necessary
  - Taking each cluster as an event and finalizing each event's arguments
"""

# TODO : We are doing coreference in sentence level.
# So if sent_cascade is not used, then we may not have coreference information for some of the triggers.
# If it is used we may have sentences where there are no triggers.

# TODO : Do not discard anything, just store them differently. For example;
# - Create a column named "country" and default it with "India", if foreign
# name put it there.
# - If there is no place at all, store it nonetheless with no place name.
# - If state name, store it nonetheless with no lat and long

def get_args():
    '''
    This function parses and return arguments passed in
    '''
    parser = argparse.ArgumentParser(prog='construct_event_database.py')
    parser.add_argument('-i', '--input_file', help="Input json file")
    parser.add_argument('-o', '--out_file', help="Output json file")
    parser.add_argument('-p', '--place_folder', help="A folder that contains state_alternatives.tsv, district_alternatives.tsv, foreign_alternatives.tsv and district_coords_dict.json for target country.")
    parser.add_argument('--sent_cascade', help="If true: Negative sentences' token labels are negative", default="false")
    args = parser.parse_args()

    return(args)

def read_alternatives_tsv(tsv_filename): # returns a dict("alternative_name"->"place_name")
    with open(tsv_filename, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    out_dict = {}
    for line in lines[1:]: # first line is header
        alt_name, place_name = line.split("\t")
        out_dict[alt_name] = place_name

    return out_dict

def get_span(sent_tokens, span):
    return " ".join(sent_tokens[span[0]:span[1]+1]) # spans were exlusive

def get_coords_from_dict(dist_name, date):
    val = dist_dict[dist_name]
    if val[date]:
        coords = val[date]
    else: # no entry for some reason
        if val["2019"]:
            coords = val["2019"]
        elif val["2011"]:
            coords = val["2011"]
        elif val["2001"]:
            coords = val["2001"]
        else:
            print("No available coords in dist_dict for  : %s" %dist_name)
            return 0

    return coords

def get_place_coordinates(place_name, date):
    global all_processed_place_names, state_name_fail, dist_name_success, geopy_success, not_found_fail, geopy_dist_name_success, geopy_dist_name_fail, ignore_list_fail
    all_processed_place_names += 1
    place_name_lower = place_name.lower()

    # Ignore list contains stopwords and target country's name
    if place_name_lower in ignore_list:
        ignore_list_fail += 1
        return "Error"

    # State names
    if state_alts.get(place_name_lower, "") != "":
        state_name_fail += 1
        return "Error"

    # TODO : As an additional info, from dictionary, get the state that district belongs to.
    #   - You would need to do this according to date also, since a district's state might change over time
    #   - Adding a state name to 2001, 2011 and 2019 field would solve this

    # District names
    dist_name = dist_alts.get(place_name_lower, "")
    if dist_name != "":
        dist_name_success += 1
        coords = get_coords_from_dict(dist_name, date)
        return coords[0], coords[1], dist_name

    # GEOPY
    location = geopy_cache.get(place_name_lower, None) # Try cache first
    if location == None: # If name is not in our cache
        try: # Might throw error due to connection
            location = geocode(place_name)
            location = {"latitude": location.latitude, "longitude": location.longitude, "address": location.address}
        except:
            location = None

    # if there is a district name in location["adress"], its length is more than 2
    if location != None and location["address"].endswith("India") and len(location["address"].split(", ")) > 2:
        geopy_success += 1
        geopy_cache[place_name_lower] = location # Add to cache
        geopy_names = [a.lower().replace(" district", "") for a in reversed(location["address"].split(", ")[-5:-1])] # last 5 except the last one which is always India
        for name in geopy_names:
            dist_name = dist_alts.get(name, "")
            if dist_name != "":
                geopy_dist_name_success += 1
                coords = get_coords_from_dict(dist_name, date)
                return "geopy_success", coords[0], coords[1], dist_name, location["latitude"], location["longitude"], location["address"]

        geopy_dist_name_fail += 1
        with open("geopy_outs.txt", "a", encoding="utf-8") as f:
            text_to_write = place_name + "    " + location["address"] + "\n"
            f.write(text_to_write)

        return location["latitude"], location["longitude"], location["address"]

    not_found_names.append(place_name_lower)
    not_found_fail += 1
    return "Error"

def is_foreign_country(place_name):
    if foreign_alts.get(place_name.lower(), "") != "":
        return True
    return False

# GLOBAL STUFF
event_category_dict = {"demonst": "Demonstration", "arm_mil": "Armed Militancy", "group_clash": "Group Clash", "ind_act": "Industrial Action"}
organizer_category_dict = {"Grassroots_Organization": "Grassroots Organization", "Political_Party": "Political Party",
                           "Chambers_of_Professionals": "Chambers of Professionals", "Labor_Union": "Labor Union",
                           "Militant_Organization": "Militant Organization"}
participant_category_dict = {"halk": "Masses", "militan": "Militant", "aktivist": "Activist",
                             "köylü": "Peasant", "öğrenci": "Student",
                             "siyasetçi": "Politician", "profesyonel": "Professional",
                             "işçi": "Proletariat", "esnaf/küçük üretici": "Petty Bourgeoisie"}

# For Statistics
total_documents = 0
no_pos_sent = 0
one_pos_sent = 0
total_events = 0
events_with_html_place = 0
events_with_place_name = 0
events_with_state_name = 0
events_with_no_place_name = 0
foreign_place_name = 0
all_processed_place_names = 0
ignore_list_fail = 0
state_name_fail = 0
dist_name_success = 0
geopy_success = 0
geopy_dist_name_success = 0
geopy_dist_name_fail = 0
not_found_fail = 0

args = get_args()

if os.path.exists(args.place_folder + "/geopy_cache.json"):
    with open(args.place_folder + "/geopy_cache.json", "r", encoding="utf-8") as f:
        geopy_cache = json.loads(f.read())
else:
    geopy_cache = {}


with open(args.place_folder + "/district_coords_dict.json", "r", encoding="utf-8") as f:
    dist_dict = json.loads(f.read())

not_found_names = []
state_alts = read_alternatives_tsv(args.place_folder + "/state_alternatives.tsv")
dist_alts = read_alternatives_tsv(args.place_folder + "/district_alternatives.tsv")
foreign_alts = read_alternatives_tsv(args.place_folder + "/foreign_alternatives.tsv")
# Some list I created before. Does not really represent the extracted place names (except 'india' and maybe nltk stopwords)
# None of the alternative names that we have is in this list!
ignore_list = stopwords.words('english') + ['india', '!', '$', '%', '&', "'", "''", "'re", "'s", "'ve", '(', ')', '*', ',', '-', '--', '.', "n't", '...', '00:00', ':', ';', '<', '>', '?', '@', '[', ']', '_', '__', '`', '``', '|', '\x92\x92', '\x97', '–', '—', '‘', '’', '“', '”', "'m", "a.m.", '^', '/'] + [str(i) for i in range(1000)] + [str(i) for i in range(1980,2020)] + ["0" + str(i) for i in range(1,10)]
geolocator = Nominatim(user_agent="GLOCON")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1) # limit rate to 1 second

if __name__ == "__main__":
    input_file = open(args.input_file, "r", encoding="utf-8")
    out_file = open(args.out_file, "w", encoding="utf-8")

    for json_data in input_file:
        json_data = json.loads(json_data)
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

        # Date of article
        html_year = int(json_data["html_year"]) # must exist in data
        if html_year < 2002:
            html_year = "2001"
        elif html_year > 2001 and html_year < 2012:
            html_year = "2011"
        elif html_year > 2011:
            html_year = "2019"

        # Html place
        curr_place_name = ""
        latitude = 0.0
        geopy_lat, geopy_long, geopy_name = 0.0, 0.0, ""
        html_place = json_data.get("html_place", "") # might not exist in data
        if html_place != "":
            if is_foreign_country(html_place): # Discard whole document if foreign name
                continue

            vals = get_place_coordinates(html_place, html_year)
            if vals == "Error":
                pass
            elif vals[0] == "geopy_success":
                latitude, longitude, returned_place_name, geopy_lat, geopy_long, geopy_name = vals[1:]
                curr_place_name = returned_place_name
            else:
                latitude, longitude, returned_place_name = vals
                curr_place_name = returned_place_name

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
                part = json_data["participant_semantic"][sent_idx]
                if part != "No":
                    part_sem[part] += 1

                org = json_data["organizer_semantic"][sent_idx]
                if org != "No":
                    org_sem[org] += 1

                # Other stuff
                triggers.extend([get_span(sent_tokens, trig) for trig in json_data["trigger"].get(str_sent_idx, [])])
                participants.extend([get_span(sent_tokens, part) for part in json_data["participant"].get(str_sent_idx, [])])
                organizers.extend([get_span(sent_tokens, org) for org in json_data["organizer"].get(str_sent_idx, [])])
                targets.extend([get_span(sent_tokens, target) for target in json_data["target"].get(str_sent_idx, [])])
                fnames.extend([get_span(sent_tokens, fname) for fname in json_data["fname"].get(str_sent_idx, [])])
                etimes.extend([get_span(sent_tokens, etime) for etime in json_data["etime"].get(str_sent_idx, [])])

            # Place
            if latitude == 0.0: # if html_place failed
                # Check if any place name we found is from a foreign country. If so, discard this event!
                if any([is_foreign_country(place_name) for place_name in all_place]):
                    # TODO : Should we really discard this event?
                    foreign_place_name += 1
                    continue # Discard event
                    # break # Discard document -> Not possible, because we already write the previous clusters to output file.
                    # So the only events we discard are this and the rest of the clusters, not the whole document.

                # We will use the most common place name if it is a place name and it is from target country.
                for place_name in all_place.most_common():
                    vals = get_place_coordinates(place_name[0], html_year)
                    if vals == "Error":
                        pass
                    elif vals[0] == "geopy_success":
                        latitude, longitude, returned_place_name, geopy_lat, geopy_long, geopy_name = vals[1:]
                        curr_place_name = returned_place_name
                        break
                    else:
                        latitude, longitude, returned_place_name = vals
                        curr_place_name = returned_place_name
                        break

                # No place name was found in our dist_dict or using geopy
                if latitude == 0.0:
                    if state_alts.get(html_place.lower(), "") != "":
                        curr_place_name = state_alts[html_place.lower()]
                        latitude = 0.0
                        longitude = 0.0
                    else:
                        no_state_name = True
                        for place_name in all_place.most_common():
                            if state_alts.get(place_name[0].lower(), "") != "":
                                no_state_name = False
                                curr_place_name = state_alts[place_name[0].lower()]
                                latitude = 0.0
                                longitude = 0.0

                        if no_state_name:
                            # NOTE : If no place name is found, we discard the event!
                            events_with_no_place_name += 1
                            # Write out whole json and which event that we could not find any place for
                            with open("nothing_found.json", "a", encoding="utf-8") as f:
                                json_data["no_name_cluster"] = cluster
                                f.write(json.dumps(json_data) + "\n")

                            continue

                        # Write out whole json and which event that we could not find any place for except a state name
                        with open("only_state_found.json", "a", encoding="utf-8") as f:
                            json_data["no_name_cluster"] = cluster
                            json_data["state_name"] = curr_place_name
                            f.write(json.dumps(json_data) + "\n")

                        events_with_state_name += 1

                events_with_place_name += 1

            else:
                events_with_html_place += 1

            # Place
            out_json["CityCode"] = curr_place_name
            out_json["latitude"] = latitude
            out_json["longitude"] = longitude
            if geopy_lat != 0.0:
                out_json["specific_latitude"] = geopy_lat
                out_json["specific_longitude"] = geopy_long
                out_json["specific_place_name"] = geopy_name

            out_json["year"] = json_data["html_year"]
            out_json["month"] = json_data["html_month"]
            out_json["day"] = json_data["html_day"]
            out_json["urbanrural"] = json_data["urbanrural"]

            # Semantic stuff
            out_json["eventcategory"] = event_category_dict[trig_sem.most_common(1)[0][0]]

            # If there is no sentence predicted with our predefined categories, then this
            # event's category is "Other"
            if len(part_sem) == 0:
                out_json["participant0category"] = "Other"
            else:
                for j,part in enumerate(part_sem.most_common(4)):
                    out_json["participant" + str(j) + "category"] = participant_category_dict[part[0]]

            # If there is no sentence predicted with our predefined categories, then this
            # event's category is "Other"
            if len(org_sem) == 0:
                out_json["organizer0category"] = "Other"
            else:
                for j,org in enumerate(org_sem.most_common(9)):
                    out_json["organizer" + str(j) + "category"] = organizer_category_dict[org[0]]

            # Other stuff
            out_json["triggers"] = triggers
            out_json["participants"] = participants
            out_json["organizers"] = organizers
            out_json["targets"] = targets
            out_json["fnames"] = fnames
            out_json["etimes"] = etimes
            # TODO : eventethnicity, eventideology

            out_file.write(json.dumps(out_json) + "\n")

    input_file.close()
    out_file.close()

    # Write out geopy cache
    with open(args.place_folder + "/geopy_cache.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(geopy_cache))

    with open("not_found_names.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(not_found_names))

print("Out of %d documents processed, %d had no positive sentence and %d had only one positive sentence." %(total_documents, no_pos_sent, one_pos_sent))
print()
print("Total number of events encountered : %d" %total_events)
print("    %d of these used html_place as their final place name" %events_with_html_place)
print("    For the remaining %d events : " %(total_events - events_with_html_place))
print("        %d had succesfully obtained place names" %(events_with_place_name - events_with_state_name))
print("        %d had only state names" %events_with_state_name)
print("        %d had foreign places" %foreign_place_name)
print("        %d had no usable place name" %events_with_no_place_name)
print()
print("Total number of processed place names with get_coordinates function : %d" %all_processed_place_names)
print("    %d of these were ignored (stopwords or 'india')" %ignore_list_fail)
print("    %d of these were state names" %state_name_fail)
print("    %d of these were province names" %dist_name_success)
print("    %d of these were decided to be place names in india by geopy" %geopy_success)
print("        %d of the returned addresses of geopy were in our district dictionary" %geopy_dist_name_success)
print("        %d of the returned addresses of geopy were not in our district dictionary" %geopy_dist_name_fail)
print("    %d of these failed all the way" %not_found_fail)
