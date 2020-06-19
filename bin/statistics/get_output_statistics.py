import glob
import json
from collections import Counter
import csv
import json


import argparse





parser = argparse.ArgumentParser(description='Text')
parser.add_argument('input', type=str, help='Input files should be nextflow output')
parser.add_argument('tag', type=str, help='Tag')
parser.add_argument('type', type=str, help='file type')

args = parser.parse_args()
input_folder = args.input
tag = args.tag
file_type = args.type

def postprocess(data):
    all_tokens = []
    # sent_count = 0
    all_token_labels = []

    for i, token in enumerate(data["tokens"]):
        if token == "SAMPLE_START":
            token_labels = []
            tokens = []
        elif token == "[SEP]":
            all_tokens.append(tokens)
            # if data["sent_labels"][sent_count] == 0: # If sentence's label is 0, ignore all predicted tokens and reset them to 'O' tag.
            #     token_labels = ["O"] * len(token_labels)

            all_token_labels.append(token_labels)
            # sent_count += 1
            token_labels = []
            tokens = []
        else:
            tokens.append(token)
            token_labels.append(data["token_labels"][i])

    all_token_labels.append(token_labels)
    all_tokens.append(tokens)
    data["token_labels"] = all_token_labels
    data["tokens"] = all_tokens
    return data


protest_flair_count = 0
place_name_list = []
flair_name_list = []
count = 0
empty_list_flair_output = 0
protest_but_no_place = 0
protest_but_no_place_list = []


"""
--input_file
--output_file
--place name, other features
--argparse kullanarak
--help script hakkında bilgi verecek
json dosyasını pipeline outputbatch klasörüne koyabiliriz
bütün protestolarda ya da place name olan dosyalarda trigger var mı?
place name trigger olan cümlede mi? percentage, aynısı flair output için de aynısı
flair output and place name extractor comparison
logging --  exception file --
--tag place, trigger, time, 
nextflowoutputtohumanreadable
nf2

"""


for elem in glob.glob(input_folder+"*json"):
    with open(elem) as f:
        content = json.loads(f.read())
        if content['doc_label'] == 1:
            count = count + 1
            #print(count)
            b_place_count = 0
            for idx, token_label in enumerate(content['token_labels']):
                if token_label == "B-"+tag:
                    token_items = []
                    token_items.append(content['tokens'][idx])
                    flag = True
                    for second_index, elem in enumerate(content['token_labels'][idx+1:]):
                        #print(elem)

                        if elem == "I-"+tag:
                            print('YESSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS')
                            print(content['id'])
                            token_items.append(content['tokens'][idx+second_index+1])
                        else:
                            break
                    print(" ".join(token_items))
                    b_place_count = b_place_count + 1
                    """
                    if content['tokens'][idx] == "South":
                        print(content['id'])
                    """
                    place_name_list.append(" ".join(token_items))
                    #print(token_label)
                    #print(content['tokens'][idx])
            if b_place_count == 0:
                protest_but_no_place = protest_but_no_place + 1
                protest_but_no_place_list.append(content['id'])
            content = postprocess(content)
            try:
                flair_output = content['flair_output']
                # If it is protest and there is no flair output
                for elem in flair_output:
                    flair_name_list.append(content['tokens'][elem[0]][elem[1]:elem[2]+1])
            except:
                print("There is no flair output")
                protest_flair_count = protest_flair_count + 1

#STATISTICS
#PLACE NAME
print("Total protest number is " + str(count))
print("Total protest number without flair_output " + str(protest_flair_count))
print("Most Frequent Place Names : ")
print(Counter(place_name_list).most_common(80))
print("Protest without flair output total protest file ratio " + str(protest_flair_count/count))

print(flair_name_list)
print("Protest with flair output total protest file ratio " + str(1-(protest_flair_count/count)))
print("Protest but no place " + str(protest_but_no_place))
print("Protest but no place protest ratio" + str(protest_but_no_place/count))
print(protest_but_no_place_list)

file_dict = {
    "total_document" : count,
    "protest_without_flair": protest_flair_count,
    "most_frequent_place_names": Counter(place_name_list).most_common(80),
    "protest_without_flair_total_protest_ratio": protest_flair_count/count,
    "Protest_but_no_place": protest_but_no_place,
    "Protest_but_no_place_protest_ratio": protest_but_no_place/count
    }

if file_type == "csv":
    with open('mycsvfile.csv', 'w') as f:  # Just use 'w' mode in 3.x
        w = csv.DictWriter(f, file_dict.keys())
        w.writeheader()
        w.writerow(file_dict)
else:
    with open('mycsvfile.json', 'w') as fp:
        json.dump(file_dict, fp)