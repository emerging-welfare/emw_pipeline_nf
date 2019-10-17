import json
from utils import postprocess
from utils import filename_to_url
from glob import iglob
#import csv
#import pandas as pd
import tqdm
#df = pd.DataFrame(columns=["url","doc_text","sentence","triggers","places","times","participants","organizers","targets","facilities"])

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
processing = tqdm.tqdm(total=2370894, desc='Files', position=0)
file_log = tqdm.tqdm(total=0, position=1, bar_format='{desc}')
with open("all_json.jl","w+") as wr:
    for filename in iglob("jsons/*json"):
        try:
                with open(filename, "r", encoding="utf-8") as f:
                    data = json.loads(f.read())
                file_log.set_description_str(f'Current file: {filename}')
                if "doc_label" not in data.keys():
                     continue
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
                    #df = df.append({"url":data["id"], "doc_text":data["text"], "sentence":data["sentences"][i],
                    #                "triggers":" ".join(obj.trigger_list), "places":" ".join(obj.place_list),
                    #                "times":" ".join(obj.time_list), "participants":" ".join(obj.participant_list),
                    #                "organizers":" ".join(obj.organizer_list), "targets":" ".join(obj.target_list),
                    #                "facilities":" ".join(obj.facility_list)}, ignore_index=True)
                    output_dict={"url":data["id"], "doc_text":data["text"], "sentence":data["sentences"][i],"triggers":" ".join(obj.trigger_list), "places":" ".join(obj.place_list),"times":" ".join(obj.time_list), "participants":" ".join(obj.participant_list),"organizers":" ".join(obj.organizer_list), "targets":" ".join(obj.target_list),"facilities":" ".join(obj.facility_list)}
                    wr.write(str(output_dict)+"\n")
                    processing.update(1)
        except Exception as e :
               print("there is a problem with {0} file happened cuz the following error {1} \n\n\n".format(filename , e))
               processing.update(1)
	
#df.to_csv("pipeline_all.csv", index=False)

# csv_file.close()
