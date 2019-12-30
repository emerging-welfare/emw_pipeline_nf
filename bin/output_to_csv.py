import json
from utils import postprocess
from utils import filename_to_url
from glob import iglob,glob
import argparse
import tqdm
import csv

def get_args():
    '''
    This function parses and return arguments passed in
    '''
    parser = argparse.ArgumentParser(prog='out_to_csv.py',
                                     description= """This script is written to generate a detailed csv file from json files in a folder.
        The output is sentence based. which contains the following values "url","doc_text","doc_label","doc_is_violent","sentence_number","sentence_text","sentence_label","publish_date","triggers", "places","times","participants","organizers","targets","facilities","trigger_semantic","participant_semantic","organizer_semantic" for each sentences.
        Each of "places","times","participants","organizers","targets","facilities" values represent list of span/ or a span.
       """
       )
    parser.add_argument('--output_type', help="csv or json",default="csv")
    parser.add_argument('--input_folder', help="input folder path",required=True)
    parser.add_argument('--o', help="output file name",default="output_file",required=True)
    parser.add_argument('--date_key', help="output file name",default="publish_date")
    parser.add_argument('--csv_spliter', help="token used as spliter in csv output",default="[SEP]")
    parser.add_argument('--filter_unprotested_sentence', action="store_true",help="filter unprotested sentences",default=False)
    parser.add_argument('--filter_unprotested_doc', action="store_true",help="filter unprotested documents",default=False)
    args = parser.parse_args()

    return(args)

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


def main():
    args=get_args()
    files=glob(args.input_folder+"*json")
    if len(files)==0:
        raise RuntimeError("input folder is empty")
    file_log = tqdm.tqdm(total=0, position=1, bar_format='{desc}')
    header_csv=["url","doc_text","doc_label","doc_is_violent","sentence_number","sentence_text","sentence_label","publish_date","triggers", "places","times","participants","organizers","targets","facilities","trigger_semantic","participant_semantic","organizer_semantic"]
    output_file_name=args.o+".csv" if args.output_type=="csv" else args.o+".json"

    with open(output_file_name,"w",errors='surrogatepass',encoding='utf-8') as wr:

        if args.output_type=="csv":
            writer = csv.DictWriter(wr, fieldnames=header_csv)
            writer.writeheader()
            #wr.write(args.csv_spliter.join(header_csv)+"\n") #header
        for filename in tqdm.tqdm(files):
            try:
                    with open(filename, "r", encoding="utf-8",errors='surrogatepass') as f:
                        data = json.loads(f.read())
                    
                    file_log.set_description_str(f'Current file: {filename}')
                    
                    doc_text_wrote=False
                    if "doc_label" not in data.keys():
                        continue
                    if args.filter_unprotested_doc:
                        if data["doc_label"] == 0:
                            continue 

                    data = postprocess(data)
                    if not data:
                        print("Something wrong with postprocess")
                        continue
        
                    data["id"] = filename_to_url(data["id"])
                    for i, sent_label in enumerate(data["sent_labels"]):
                        if args.filter_unprotested_sentence:
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
                        # if args.output_type=="csv":
                        #         wr.write(args.csv_spliter.join([data["id"]
                        #         ,data["text"].replace("\n"," ").replace("\"","\\\"").replace("\'","\\\'")
                        #         ,str(data["doc_label"])
                        #         ,str(data["is_violent"])
                        #         ,str(i)
                        #         ,str(data["sentences"][i]).replace("\n"," ").replace("\"","\\\"").replace("\'","\\\'")
                        #         ,str(data["sent_labels"][i])
                        #         ,data[args.date_key].strip("\n")
                        #         ," & ".join(obj.trigger_list).strip("\n")
                        #         ," & ".join(obj.place_list).strip("\n")
                        #         ," & ".join(obj.time_list).strip("\n")
                        #         ," & ".join(obj.participant_list).strip("\n")
                        #         ," & ".join(obj.organizer_list).strip("\n")
                        #         ," & ".join(obj.target_list).strip("\n")
                        #         ," & ".join(obj.facility_list).strip("\n")
                        #         ,data["Trigger_Semantic_label"][i].strip("\n")
                        #         ,data["participant_semantic"][i].strip("\n")
                        #         ,data["organizer_semantic"][i].strip("\n")])+"\n")
                        # else:
                        output_dict={"url":data["id"]
                        ,"doc_text":"" if doc_text_wrote else data["text"].replace("\n"," ")
                        ,"doc_label":str(data["doc_label"])
                        ,"doc_is_violent":str(data["is_violent"])
                        ,"sentence_number":str(i)
                        ,"sentence_text":str(data["sentences"][i]).replace("\n"," ")
                        ,"sentence_label":str(data["sent_labels"][i])
                        ,"publish_date":data[args.date_key].strip("\n")
                        ,"triggers":" & ".join(obj.trigger_list)
                        ,"places":" & ".join(obj.place_list)
                        ,"times":" ".join(obj.time_list)
                        ,"participants":" ".join(obj.participant_list)
                        ,"organizers":" ".join(obj.organizer_list)
                        , "targets":" ".join(obj.target_list)
                        ,"facilities":" ".join(obj.facility_list)
                        ,"trigger_semantic":data["Trigger_Semantic_label"][i]
                        ,"participant_semantic":data["participant_semantic"][i]
                        ,"organizer_semantic":data["organizer_semantic"][i]}

                        doc_text_wrote=True
                        if args.output_type=="csv":
                            writer.writerow(output_dict)
                        else:
                            wr.write(json.dumps(output_dict)+"\n")
            except Exception as e :

                print(e.with_traceback)
                print(data["id"])
                raise RuntimeError

if __name__ == '__main__':
    main()