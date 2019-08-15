import json
from utils import postprocess
from utils import filename_to_url
from glob import glob
import csv
import pandas as pd

# csv_file = open("pipeline_all.csv", "w", encoding="utf-8")
# csv_writer = csv.writer(csv_file, delimiter=',', quotechar='|',
#                         quoting=csv.QUOTE_MINIMAL)
# csv_writer.writerow(["url","doc_text","sentence","triggers","places","times","participants","organizers","targets","facilities"])
df = pd.DataFrame(columns=["url","doc_text","sentence","triggers","places","times","participants","organizers","targets","facilities"])
# csv_file.write("url,doc_text,sentence,triggers,places,times,participants,organizers,targets,facilities\n")

class ToHoldStuff(object):
    def __init__(self):
        self.trigger_list = []
        self.facility_list = []
        self.place_list = []
        self.time_list = []
        self.participant_list = []
        self.target_list = []
        self.organizer_list = []

def add_tag(obj, span, label, tokens):
    text = " ".join([tokens[ind] for ind in span])
    if label == "trigger":
        obj.trigger_list.append(text)
    elif label == "place":
        obj.place_list.append(text)
    elif label == "etime":
        obj.time_list.append(text)
    elif label == "participant":
        obj.participant_list.append(text)
    elif label == "organizer":
        obj.organizer_list.append(text)
    elif label == "target":
        obj.target_list.append(text)
    elif label == "fname":
        obj.facility_list.append(text)
    else:
        print("Different label : %s" %label)

    return obj

for filename in glob("out_pos_jsons/http*"):
    with open(filename, "r", encoding="utf-8") as f:
        data = json.loads(f.read())

    if data["doc_label"] == 0:
        continue

    data = postprocess(data)
    if not data:
        print("Something wrong with postprocess")
        continue

    data["id"] = filename_to_url(data["id"])
    for i, sent_label in enumerate(data["sent_labels"]):
        if sent_label == 0:
            continue

        prev_label = "O"
        curr_span = []
        obj = ToHoldStuff()
        tokens = data["tokens"][i]
        for j,label in enumerate(data["token_labels"][i]):
            if label == "O" and curr_span:
                obj = add_tag(obj, curr_span, prev_label, tokens)
                curr_span = []

            elif label.startswith("B-"):
                if not curr_span:
                    curr_span.append(j)
                else:
                    obj = add_tag(obj, curr_span, prev_label, tokens)
                    curr_span = [j]
                prev_label = label[2:]

            elif label.startswith("I-"):
                if not curr_span:
                    curr_span.append(j)
                else:
                    if prev_label == label[2:]:
                        curr_span.append(j)
                    else:
                        obj = add_tag(obj, curr_span, prev_label, tokens)
                        curr_span = [j]
                prev_label = label[2:]

        # csv_file.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s" %(data["id"], data["text"], data["sentences"][i],
        #                                                  "\n".join(obj.trigger_list), "\n".join(obj.place_list),
        #                                                  "\n".join(obj.time_list), "\n".join(obj.participant_list),
        #                                                  "\n".join(obj.organizer_list), "\n".join(obj.target_list),
        #                                                  "\n".join(obj.facility_list)))

        # csv_writer.writerow([data["id"], data["text"], data["sentences"][i],
        #                      "\n".join(obj.trigger_list), "\n".join(obj.place_list),
        #                      "\n".join(obj.time_list), "\n".join(obj.participant_list),
        #                      "\n".join(obj.organizer_list), "\n".join(obj.target_list),
        #                      "\n".join(obj.facility_list)])

        df = df.append({"url":data["id"], "doc_text":data["text"], "sentence":data["sentences"][i],
                        "triggers":"\n".join(obj.trigger_list), "places":"\n".join(obj.place_list),
                        "times":"\n".join(obj.time_list), "participants":"\n".join(obj.participant_list),
                        "organizers":"\n".join(obj.organizer_list), "targets":"\n".join(obj.target_list),
                        "facilities":"\n".join(obj.facility_list)}, ignore_index=True)

df.to_csv("pipeline_all.csv", index=False)

# csv_file.close()
