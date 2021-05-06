import json
import pandas as pd
import sys

"""
This script is used after generating the database
using construct_event_database script. The result
of this script can be used in visualization.
This script is necessary, because there can be
small changes in coordinates of district in time.
So when visualizing, disregarding these small differences
would be better.
"""

input_database_filename = sys.argv[1]
district_coords_dict_filename = sys.argv[2]
output_filename = sys.argv[3]

# since this dict is global we read it here
with open(district_coords_dict_filename, "r", encoding="utf-8") as f:
    dist_dict = json.loads(f.read())

def get_latest_coord(row):
    if row.district_name not in dist_dict.keys():
        return row

    coords = dist_dict[row.district_name]
    avail_coords = [k for k,v in coords.items() if len(v) != 0] # get the available coordinates
    latest_coords = coords[sorted(avail_coords, reverse=True)[0]] # use most recent available coordinates

    row.latitude = latest_coords[0][1]
    row.longitude = latest_coords[0][0]

    return row

if __name__ == "__main__":

    db = pd.read_json(input_database_filename, orient="records", lines=True)
    db = db.apply(get_latest_coord, axis=1)

    db.to_json(output_filename, orient="records", lines=True, force_ascii=False)
