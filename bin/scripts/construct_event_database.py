import json
import argparse
from collections import Counter
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from nltk.corpus import stopwords
import os
import re

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
    parser.add_argument('-o', '--out_filename', help="Output json file")
    parser.add_argument('-f', '--out_folder', help="Output folder")
    parser.add_argument('-p', '--place_folder', help="A folder that contains state_alternatives.tsv, district_alternatives.tsv, foreign_alternatives.tsv and district_coords_dict.json for target country.")
    parser.add_argument('--sent_cascade', help="If true: Negative sentences' token labels are negative. false/true", default="false", choices=["false", "true"])
    parser.add_argument('--check_extracted_first', help="When doing geocoding, whether to check for places in extracted places first, rather than html places. false/true", default="false", choices=["false", "true"])
    parser.add_argument('--internal', help="If the output is for internal use only. false/true", default="false", choices=["false", "true"])
    parser.add_argument('--debug', help="Debug version. false/true", default="false", choices=["false", "true"])
    parser.add_argument('--dist_has_locality', help="Whether district_dict_coords.json has locality key for every item. false/true", default="false", choices=["false", "true"])
    parser.add_argument('--target_country', help="Name of the country we are doing the geocoding for. Used solely for geopy.", choices=["india", "south_africa"])
    parser.add_argument('--batch_name', help="Prefix to be used when assigning ids to events.")

    args = parser.parse_args()
    args = vars(args)

    args["sent_cascade"] = get_args_boolean(args["sent_cascade"])
    args["check_extracted_first"] = get_args_boolean(args["check_extracted_first"])
    args["internal"] = get_args_boolean(args["internal"])
    args["debug"] = get_args_boolean(args["debug"])
    args["dist_has_locality"] = get_args_boolean(args["dist_has_locality"])

    return(args)

def get_args_boolean(curr_arg):
    if curr_arg == "false":
        return False
    elif curr_arg == "true":
        return True
    else:
        print('Something wrong with argparse!!!')
        return -1

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

def filename_to_url(filename):
    url = re.sub("___?", "://", filename)
    url = re.sub("_", "/", url)
    url = re.sub("-h6j7k8-", "%", url)
    url = re.sub("\.json$", ".ece", url)
    return url

def get_coords_from_dict(dist_name, date):
    val = dist_dict[dist_name]
    if val[date]:
        coords, state_name = val[date]
        return coords, state_name
    else: # no entry for some reason. TODO : Why does this happen?
        # print("name - date conflict : %s - %s" %(dist_name, date))
        for year in census_years:
            if val[year]:
                coords, state_name = val[year]
                return coords, state_name

        # TODO : Catch this if it happens!
        print("No available coords in dist_dict for  : %s" %dist_name)
        return 0

def get_place_coordinates(place_name, date):
    global all_processed_place_names, state_name_fail, dist_name_success, geopy_success, not_found_fail, geopy_dist_name_success, geopy_dist_name_fail, ignore_list_fail
    all_processed_place_names += 1

    # Ignore list contains stopwords and target country's name
    if place_name in all_ignore_list:
        ignore_list_fail += 1
        return "Error", "Ignore List"

    # State names
    if state_alts.get(place_name, "") != "":
        state_name_fail += 1
        return "Error", "State Name"

    # NOTE : Coordinates are [X, Y] which is to say [longitude, latitude]

    # District names
    dist_name = dist_alts.get(place_name, "")
    if dist_name != "":
        dist_name_success += 1
        coords, state_name = get_coords_from_dict(dist_name, date)
        return coords[1], coords[0], dist_name, state_name

    # GEOPY
    location = geopy_cache.get(place_name, "") # Try cache first
    if location == "": # If name is not in our cache
        try: # Might throw error due to connection
            location = geocode(place_name)
        except:
            location = None

        if location != None:
            location = {"latitude": location.latitude, "longitude": location.longitude, "address": location.address}

        geopy_cache[place_name] = location # Add to cache even if it is None

    if args["target_country"] == "india":
        # if there is a district name in location["adress"], its length is more than 2
        if location != None and location["address"].lower().endswith("india") and len(location["address"].split(", ")) > 2:
            geopy_success += 1
            geopy_names = [a.lower().replace(" district", "") for a in reversed(location["address"].split(", ")[-5:-1])] # last 5 except the last one which is always India
            for name in geopy_names:
                dist_name = dist_alts.get(name, "")
                if dist_name != "":
                    geopy_dist_name_success += 1
                    coords, state_name = get_coords_from_dict(dist_name, date)
                    return "geopy", coords[1], coords[0], dist_name, state_name, location["latitude"], location["longitude"], location["address"]

            geopy_dist_name_fail += 1
            with open(args["out_folder"] + "/geopy_outs.txt", "a", encoding="utf-8") as f:
                text_to_write = place_name + "    " + location["address"] + "\n"
                f.write(text_to_write)

            return "geopy", location["latitude"], location["longitude"], "", "", location["latitude"], location["longitude"], location["address"]

    # Pretty much the same code as india's, but it can change significantly for some other country.
    elif args["target_country"] == "south_africa":
        # if there is a district name in location["adress"], its length is more than 2
        if location != None and location["address"].lower().endswith("south africa") and len(location["address"].split(", ")) > 2:
            geopy_places.append(place_name)
            geopy_success += 1
            # NOTE: Since these are in reversed order, we first match with the more local place.
            geopy_names = [a.lower() for a in reversed(location["address"].split(", ")[-5:-1])] # last 5 except the last one which is always South Africa
            for name in geopy_names:
                dist_name = dist_alts.get(name, "")
                if dist_name != "":
                    geopy_dist_name_success += 1
                    coords, state_name = get_coords_from_dict(dist_name, date)
                    return "geopy", coords[1], coords[0], dist_name, state_name, location["latitude"], location["longitude"], location["address"]

            geopy_dist_name_fail += 1
            with open(args["out_folder"] + "/geopy_outs.txt", "a", encoding="utf-8") as f:
                text_to_write = place_name + "    " + location["address"] + "\n"
                f.write(text_to_write)

            return "geopy", location["latitude"], location["longitude"], "", "", location["latitude"], location["longitude"], location["address"]

    not_found_names.append(place_name)
    not_found_fail += 1
    return "Error", "Not Found"

def is_foreign_country(place_name):
    if foreign_alts.get(place_name, "") != "":
        return True
    return False

def sorted_nicely(l):
    # Copied from this post -> https://stackoverflow.com/questions/2669059/how-to-sort-alpha-numeric-set-in-python
    def convert(text): return int(text) if text.isdigit() else text
    def alphanum_key(key): return [convert(c) for c in re.split('([0-9]+)', key)]

    return sorted(l, key=alphanum_key)


# GLOBAL STUFF
event_category_dict = {"demonst": "Demonstration", "arm_mil": "Armed Militancy", "group_clash": "Group Clash", "ind_act": "Industrial Action"}
organizer_category_dict = {"Grassroots_Organization": "Grassroots Organization", "Political_Party": "Political Party",
                           "Chambers_of_Professionals": "Chambers of Professionals", "Labor_Union": "Labor Union",
                           "Militant_Organization": "Militant Organization"}
participant_category_dict = {"halk": "Masses", "militan": "Militant", "aktivist": "Activist",
                             "köylü": "Peasant", "öğrenci": "Student",
                             "siyasetçi": "Politician", "profesyonel": "Professional",
                             "işçi": "Proletariat", "esnaf/küçük üretici": "Petty Bourgeoisie"}
# TODO: This is a pretty sloppy way to do this. But other ways bring unneccesary complexity.
all_possible_census_years = ["1990", "1991", "1992", "1993", "1994", "1995", "1996", "1997", "1998",
                             "1999", "2000", "2001", "2002", "2003", "2004", "2005", "2006", "2007",
                             "2008", "2009", "2010", "2011", "2012", "2013", "2014", "2015", "2016",
                             "2017", "2018", "2019", "2020", "2021"]

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

if os.path.exists(args["place_folder"] + "/geopy_cache.json"):
    with open(args["place_folder"] + "/geopy_cache.json", "r", encoding="utf-8") as f:
        geopy_cache = json.loads(f.read())
else:
    geopy_cache = {}

with open(args["place_folder"] + "/district_coords_dict.json", "r", encoding="utf-8") as f:
    dist_dict = json.loads(f.read())

# we check all entries since some of them might not have some of the census years as keys
census_years = list(set([k for v in dist_dict.values() for k in v.keys()]))
census_years = list(reversed(sorted_nicely([a for a in census_years if a in all_possible_census_years]))) # descending order yearwise
if len(census_years) == 0:
    raise "No census year given as key in district_coords_dict.json"

geopy_places = []
not_found_names = []
state_alts = read_alternatives_tsv(args["place_folder"] + "/state_alternatives.tsv")
dist_alts = read_alternatives_tsv(args["place_folder"] + "/district_alternatives.tsv")
foreign_alts = read_alternatives_tsv(args["place_folder"] + "/foreign_alternatives.tsv")

if os.path.exists(args["place_folder"] + "/geopy_false_positives.json"):
    with open(args["place_folder"] + "/geopy_false_positives.json", "r", encoding="utf-8") as f:
        geopy_false_positives = json.loads(f.read())
else:
    geopy_false_positives = []

if os.path.exists(args["place_folder"] + "/ignore_list.json"):
    with open(args["place_folder"] + "/ignore_list.json", "r", encoding="utf-8") as f:
        ignore_list = json.loads(f.read())
else:
    ignore_list = []

# Some list I created before. Does not really represent the extracted place names (except 'india' and maybe nltk stopwords)
# Make sure none of the alternative names that we have is in this list!
all_ignore_list = stopwords.words('english') + geopy_false_positives + ignore_list + [str(i) for i in range(1000)] + [str(i) for i in range(1980,2020)] + ["0" + str(i) for i in range(1,10)]

geolocator = Nominatim(user_agent="GLOCON")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1) # limit rate to 1 second

if __name__ == "__main__":
    input_file = open(args["input_file"], "r", encoding="utf-8")
    out_file = open(args["out_folder"] + "/" + args["out_filename"], "w", encoding="utf-8")
    if args["debug"]:
        debug_file = open(args["out_folder"] + "/" + re.sub("\.json$", "_debug.json", args["out_filename"]), "w", encoding="utf-8")

    curr_event_id = 0
    for json_data in input_file:
        json_data = json.loads(json_data)
        clusters = json_data.get("event_clusters", [])
        total_documents += 1
        if args["debug"]:
            debug_data = {}
            debug_data["url"] = filename_to_url(json_data["id"])
            debug_data["sentences"] = json_data["sentences"]

        # TODO : If sent_cascade == "false", add another for loop going over other sentences and collect information.
        # -> How do we add this info to other events since we won't know which one they belong

        if clusters == None or len(clusters) == 0: # Happens if there is only one positive sentence or no positive sentence
            sent_labels = json_data["sent_labels"]
            pos_sents = [i for i in range(len(sent_labels)) if sent_labels[i] == 1]
            if len(pos_sents) > 0:
                clusters = [pos_sents]
                one_pos_sent += 1
            else:
                no_pos_sent += 1
                if args["debug"]:
                    debug_data["pred_clusters"] = []
                    debug_file.write(json.dumps(debug_data) + "\n")

                continue

        # Date of article
        census_year = census_years[-1] # if len of census_years is 1 or if html_year <= this value, this does not change
        html_year = int(json_data["html_year"]) # must exist in data
        for year_idx in range(1,len(census_years)):
            if html_year > int(census_years[year_idx]):
                census_year = census_years[year_idx-1]
                break

        # Html place
        html_latitude, html_geopy_lat = 0.0, 0.0
        html_place = json_data.get("html_place", "").lower() # might not exist in data

        if args["debug"]:
            debug_data["html_place"] = html_place
            if html_place == "":
                debug_data["html_place_status"] = "No Html Place"

            debug_data["pred_clusters"] = clusters
            debug_clusters = []

        if html_place != "":
            if is_foreign_country(html_place): # Discard whole document if foreign name
                if args["debug"]:
                    debug_data["html_place_status"] = "Foreign Html Place"
                    debug_file.write(json.dumps(debug_data) + "\n")

                continue

            vals = get_place_coordinates(html_place, census_year)
            if vals[0] == "Error":
                returned_place_name = ""
                returned_state_name = ""
                if args["debug"]:
                    debug_data["html_place_status"] = vals[1] + " Fail"

            elif vals[0] == "geopy":
                html_latitude, html_longitude, returned_place_name, returned_state_name, html_geopy_lat, html_geopy_long, html_geopy_name = vals[1:]
                if args["debug"]:
                    debug_data["html_place_status"] = "Geopy Success"

            else:
                html_latitude, html_longitude, returned_place_name, returned_state_name = vals
                if args["debug"]:
                    debug_data["html_place_status"] = "Success"

            html_place_name = returned_place_name
            html_state_name = returned_state_name

        for cluster in clusters:
            total_events += 1

            # Reset stuff
            out_json = {}
            latitude, longitude, geopy_lat, geopy_long = 0.0, 0.0, 0.0, 0.0
            curr_place_name, curr_state_name, geopy_name = "", "", ""
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

            # Gather info
            for sent_idx in cluster:
                str_sent_idx = str(sent_idx)
                sent_tokens = json_data["tokens"][sent_idx]

                # Place
                curr_place = json_data["place"].get(str_sent_idx, [])
                for p in curr_place:
                    all_place[get_span(sent_tokens, p).lower()] += 1

                curr_flair = json_data["flair"].get(str_sent_idx, [])
                for p in curr_flair:
                    all_place[get_span(sent_tokens, p).lower()] += 1

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
            if args["check_extracted_first"] or html_latitude == 0.0: # if html place failed or was non-existent (If check_extracted_places_first is True enters here regardless!)
                # Check if any place name we found is from a foreign country. If so, discard this event!
                if any([is_foreign_country(place_name) for place_name in all_place]):
                    # TODO : Should we really discard this event?
                    foreign_place_name += 1

                    if args["debug"]:
                        debug_clusters.append({"sentence_ids": cluster, "extracted_places": list(all_place.keys()), "geocoding_status": "Foreign Place Fail"})

                    continue # Discard event
                    # break # Discard document -> Not possible, because we already write the previous clusters to output file.
                    # So the only events we discard are this and the rest of the clusters, not the whole document.

                if args["dist_has_locality"]: # dist_dict has "locality" key
                    possible_places = {} # its keys are a tuple of (locality, number_of_mentions_in_extracted_places)
                    # We will use the most "local" and then most common place name, if it is a place name and it is from target country.
                    # This for loop will check for every place name in all_place to compare their locality later.
                    for place_name in all_place.keys():
                        vals = get_place_coordinates(place_name, census_year)
                        if vals[0] == "Error":
                            continue

                        elif vals[0] == "geopy":
                            _returned_place_name = vals[3]
                            if _returned_place_name != "": # we found a dist_name in the returned address from geopy
                                curr_locality = dist_dict[_returned_place_name]["locality"]
                                possible_places[(curr_locality, all_place[place_name])] = list(vals) + [place_name]
                            else: # since this is not preferable, we assign 0 as its locality.
                                possible_places[(0, all_place[place_name])] = list(vals) + [place_name]

                        else:
                            _returned_place_name = vals[2]
                            curr_locality = dist_dict[_returned_place_name]["locality"]
                            possible_places[(curr_locality, all_place[place_name])] = list(vals) + [place_name]

                    if len(possible_places) > 0: # we had at least one non-error
                        best_key = sorted(possible_places.keys(), reverse=True)[0] # sort in descending order
                        vals = possible_places[best_key]
                        place_name = vals[-1]
                        vals = vals[:-1]
                        if vals[0] == "geopy":
                            latitude, longitude, curr_place_name, curr_state_name, geopy_lat, geopy_long, geopy_name = vals[1:]
                            if args["debug"]:
                                debug_clusters.append({"sentence_ids": cluster, "extracted_places": list(all_place.keys()),
                                                       "geocoding_status": "Geopy Success", "geocoding_original_name": place_name,
                                                       "geocoding_final_district": curr_place_name, "geocoding_final_state": curr_state_name,
                                                       "geopy_address": geopy_name})

                        else:
                            latitude, longitude, curr_place_name, curr_state_name = vals
                            if args["debug"]:
                                debug_clusters.append({"sentence_ids": cluster, "extracted_places": list(all_place.keys()),
                                                       "geocoding_status": "Success", "geocoding_original_name": place_name,
                                                       "geocoding_final_district": curr_place_name, "geocoding_final_state": curr_state_name,
                                                       "geopy_address": ""})

                else: # dist_dict does not have "locality" key
                    # We will use the most common place name, if it is a place name and it is from target country.
                    # This for loop stops after finding a suitable place name
                    for place_name in all_place.most_common():
                        vals = get_place_coordinates(place_name[0], census_year)
                        if vals[0] == "Error":
                            continue
                        elif vals[0] == "geopy":
                            latitude, longitude, returned_place_name, returned_state_name, geopy_lat, geopy_long, geopy_name = vals[1:]
                            if args["debug"]:
                                debug_clusters.append({"sentence_ids": cluster, "extracted_places": list(all_place.keys()),
                                                       "geocoding_status": "Geopy Success", "geocoding_original_name": place_name[0],
                                                       "geocoding_final_district": returned_place_name, "geocoding_final_state": returned_state_name,
                                                       "geopy_address": geopy_name})
                        else:
                            latitude, longitude, returned_place_name, returned_state_name = vals
                            if args["debug"]:
                                debug_clusters.append({"sentence_ids": cluster, "extracted_places": list(all_place.keys()),
                                                       "geocoding_status": "Success", "geocoding_original_name": place_name[0],
                                                       "geocoding_final_district": returned_place_name, "geocoding_final_state": returned_state_name,
                                                       "geopy_address": ""})

                        curr_place_name = returned_place_name
                        curr_state_name = returned_state_name
                        break

                # No place name was found in extracted places
                if latitude == 0.0:
                    # No place name was found in extracted places, so we check if we have any html_place (in case we didn't look there first!)
                    if args["check_extracted_first"] and html_latitude != 0.0:
                        latitude, longitude, curr_place_name, curr_state_name = html_latitude, html_longitude, html_place_name, html_state_name
                        if html_geopy_lat != 0.0:
                            geopy_lat, geopy_long, geopy_name = html_geopy_lat, html_geopy_long, html_geopy_name

                        if args["debug"]:
                            debug_clusters.append({"sentence_ids": cluster, "extracted_places": list(all_place.keys()),
                                                   "geocoding_status": "Success from Html", "geocoding_original_name": html_place,
                                                   "geocoding_final_district": curr_place_name, "geocoding_final_state": curr_state_name,
                                                   "geopy_address": geopy_name})

                        events_with_html_place += 1

                    # No place name was found in extracted and html place using our dist_dict or geopy, so we try to find a state name.
                    else:
                        if state_alts.get(html_place, "") != "": # Check for state name in html place
                            curr_state_name = state_alts[html_place]
                            if args["debug"]:
                                debug_clusters.append({"sentence_ids": cluster, "extracted_places": list(all_place.keys()),
                                                       "geocoding_status": "Only State Name from Html", "geocoding_original_name": html_place,
                                                       "geocoding_final_district": "", "geocoding_final_state": curr_state_name, "geopy_address": ""})
                        else: # Check for state name in extracted places
                            no_state_name = True
                            for place_name in all_place.most_common():
                                if state_alts.get(place_name[0], "") != "":
                                    no_state_name = False
                                    curr_state_name = state_alts[place_name[0]]
                                    if args["debug"]:
                                        debug_clusters.append({"sentence_ids": cluster, "extracted_places": list(all_place.keys()),
                                                               "geocoding_status": "Only State Name", "geocoding_original_name": place_name[0],
                                                               "geocoding_final_district": "", "geocoding_final_state": curr_state_name, "geopy_address": ""})

                                    break

                            if no_state_name:
                                # NOTE : If no place name is found, we discard the event!
                                events_with_no_place_name += 1
                                # Write out whole json and which event that we could not find any place for
                                with open(args["out_folder"] + "/nothing_found.json", "a", encoding="utf-8") as f:
                                    json_data["no_name_cluster"] = cluster
                                    f.write(json.dumps(json_data) + "\n")

                                    # TODO : Also need all of the places for the whole document.
                                    # But doing this would slow the script too much !
                                    # json_to_write = {"no_name_cluster": {"cluster_sent_ids": cluster,
                                    #                                      "cluster_sents": [json_data["sentences"][i] for i in cluster],
                                    #                                      "cluster_places": list(all_place.keys())},
                                    #                  "sent_labels": json_data["sent_labels"],
                                    #                  "all_sentences": json_data["sentences"],
                                    #                  "all_clusters": json_data["event_clusters"]}
                                    # f.write(json.dumps(json_to_write) + "\n")

                                if args["debug"]:
                                    debug_clusters.append({"sentence_ids": cluster, "extracted_places": list(all_place.keys()), "geocoding_status": "No Name Fail"})

                                continue

                            # Write out whole json and which event that we could not find any place for except a state name
                            with open(args["out_folder"] + "/only_state_found.json", "a", encoding="utf-8") as f:
                                json_data["no_name_cluster"] = cluster
                                json_data["state_name"] = curr_state_name
                                f.write(json.dumps(json_data) + "\n")

                                # TODO : Also need all of the places for the whole document.
                                # But doing this would slow the script too much !
                                # json_to_write = {"no_name_cluster": {"cluster_sent_ids": cluster,
                                #                                      "cluster_sents": [json_data["sentences"][i] for i in cluster],
                                #                                      "cluster_places": list(all_place.keys()),
                                #                                      "found_state_name": curr_state_name},
                                #                  "sent_labels": json_data["sent_labels"],
                                #                  "all_sentences": json_data["sentences"],
                                #                  "all_clusters": json_data["event_clusters"]}
                                # f.write(json.dumps(json_to_write) + "\n")

                            events_with_state_name += 1

                events_with_place_name += 1

            else: # If there is an html place (and check_extracted_places_first is False!)
                latitude, longitude, curr_place_name, curr_state_name = html_latitude, html_longitude, html_place_name, html_state_name
                if html_geopy_lat != 0.0:
                    geopy_lat, geopy_long, geopy_name = html_geopy_lat, html_geopy_long, html_geopy_name

                if args["debug"]:
                    debug_clusters.append({"sentence_ids": cluster, "extracted_places": list(all_place.keys()),
                                           "geocoding_status": "Success from Html", "geocoding_original_name": html_place,
                                           "geocoding_final_district": curr_place_name, "geocoding_final_state": curr_state_name,
                                           "geopy_address": geopy_name})

                events_with_html_place += 1

            # ID
            curr_event_id += 1
            out_json["event_id"] = args["batch_name"] + "_" + str(curr_event_id)

            # Place
            out_json["district_name"] = curr_place_name # can be empty
            out_json["state_name"] = curr_state_name # can be empty
            out_json["latitude"] = latitude
            out_json["longitude"] = longitude
            if geopy_lat != 0.0:
                out_json["specific_latitude"] = geopy_lat
                out_json["specific_longitude"] = geopy_long
                out_json["specific_place_name"] = geopy_name

            out_json["year"] = int(json_data["html_year"])
            out_json["month"] = int(json_data["html_month"])
            out_json["day"] = int(json_data["html_day"])
            out_json["urbanrural"] = json_data["urbanrural"]

            if curr_place_name:
                out_json["coordinate_dates"] = census_year
            elif curr_state_name: # there is no district name but there is a state name (no coordinates, so this is empty)
                out_json["coordinate_dates"] = ""
            else: # In case of geopy_fail (goes to geopy, but does not take coords from our dictionary)
                out_json["coordinate_dates"] = "geopy-2.0-2020/08"

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

            out_json["title"] = json_data.get("title", "")
            out_json["violent"] = "violent" if json_data["is_violent"] == 1 else "non-violent"
            doc_text = " ".join([sent for sent in json_data["sentences"]])
            out_json["text_snippet"] = doc_text[:(len(doc_text)//10)] # First tenth of the text
            out_json["url"] = filename_to_url(json_data["id"])

            if args["internal"]: # Text are for only internal use only due to copyright issues
                out_json["doc_text"] = doc_text
                out_json["event_sentences"] = [json_data["sentences"][i] for i in cluster]
                out_json["event_sentence_numbers"] = [i+1 for i in cluster]

            # TODO : eventethnicity, eventideology

            out_file.write(json.dumps(out_json) + "\n")

        if args["debug"]:
            if debug_clusters:
                debug_data["clusters_info"] = debug_clusters
            debug_file.write(json.dumps(debug_data) + "\n")

    input_file.close()
    out_file.close()

    # Write out geopy cache
    with open(args["place_folder"] + "/geopy_cache.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(geopy_cache))

    with open(args["out_folder"] + "/not_found_names.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(Counter(not_found_names)))

    with open(args["out_folder"] + "/geopy_places.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(Counter(geopy_places)))

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
print("    %d of these were ignored (stopwords, geopy_false_positives, ignore_list etc.)" %ignore_list_fail)
print("    %d of these were state names" %state_name_fail)
print("    %d of these were district names" %dist_name_success)
print("    %d of these were decided to be place names in target country by geopy" %geopy_success)
print("        %d of the returned addresses of geopy were in our district dictionary" %geopy_dist_name_success)
print("        %d of the returned addresses of geopy were not in our district dictionary" %geopy_dist_name_fail)
print("    %d of these failed all the way" %not_found_fail)
