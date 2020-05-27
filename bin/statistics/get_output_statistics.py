import glob
import json
from collections import Counter

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
for elem in glob.glob("new_india/19052020_10k/*.json"):
    with open(elem) as f:
        content = json.loads(f.read())
        if content['doc_label'] == 1:
            count = count + 1
            print(count)
            b_place_count = 0
            for idx, token_label in enumerate(content['token_labels']):
                if token_label == "B-place":
                    b_place_count = b_place_count + 1
                    place_name_list.append(content['tokens'][idx])
                    print(token_label)
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


# STATISTICS
print("Total protest number is " + str(count))
print("Total protest number without flair_output " + str(protest_flair_count))
print("Most Frequent Words : ")
print(Counter(place_name_list).most_common(10))
print("Protest without flair output total protest file ratio " + str(protest_flair_count/count))




print(flair_name_list)
print("Protest with flair output total protest file ratio " + str(1-(protest_flair_count/count)))
print("Protest but no place " + str(protest_but_no_place))
print("Protest but no place protest ratio" + str(protest_but_no_place/count))
print(protest_but_no_place_list)