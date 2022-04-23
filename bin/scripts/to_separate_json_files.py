import json
import sys
import re
import os.path

input_json_file = sys.argv[1]
out_json_folder = sys.argv[2]

input_file = open(input_json_file, "r", encoding="utf-8")

# TODO : If we use positive_docs.json in this script:
# Revert "tokens" field back to its original way. From
# list of lists to a list, starts with "SAMPLE_START"
# and sentences are separated with "[SEP]" token.

for line in input_file:
    d = json.loads(line)
    filename = re.sub(r"(\.ece\d?|\.json|\.html?|\.cms|)$", r".json", d["id"])
    if len(filename) > 255:
        continue
    if not os.path.isfile(out_json_folder + "/" + filename):
        with open(out_json_folder + "/" + filename, "w", encoding="utf-8") as f:
            f.write(line)

input_file.close()
