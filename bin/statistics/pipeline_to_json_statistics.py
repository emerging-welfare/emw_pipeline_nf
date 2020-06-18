import json
from collections import Counter
import argparse

parser = argparse.ArgumentParser(description='Text')
parser.add_argument('input', type=str, help='Pipeline to json table')
parser.add_argument('type', type=str, help='file type')


args = parser.parse_args()
input_folder = args.input
file_type = args.type

def get_doc_count(content):
    return len(content)

def protest_count(content):
    count = 0
    for elem in content:
        data = json.loads(str(elem))
        if data['document']['doc_label'] == 1:
            count = count + 1
    return count


def count_tokens(content):
    count_json = {}
    tokens = list(json.loads(str(content[0]))['document']['sentences'][0].keys())
    tokens.remove('sentence')
    for elem in tokens:
        count_json[elem] = []
    #print(count_json)
    for doc in content:
        data = json.loads(doc)
        for elem in tokens:
            for sentence in data['document']['sentences']:
                #print(sentence)
                if not sentence[elem]:
                    pass
                else:
                    for item in sentence[elem]:
                        count_json[elem].append(item)
    for elem in count_json.keys():
        count_json[elem] = Counter(count_json[elem]).most_common(10)
    return count_json

def protest_with_place(content):
    count = 0
    for doc in content:
        data = json.loads(doc)
        if data['document']['doc_label'] == 1:
            place_count =0
            for sentence in data['document']['sentences']:
                if sentence['B-place']:
                    place_count = place_count + 1
            if place_count>=1:
                count = count + 1
    return count

def protest_with_flair(content):
    count = 0
    for doc in content:
        data = json.loads(doc)
        if data['document']['doc_label'] == 1:
            place_count =0
            for sentence in data['document']['sentences']:
                if sentence['flair']:
                    place_count = place_count + 1
            if place_count>=1:
                count = count + 1
    return count



#def protest_without_place_flair():




    


with open(input_folder, "r") as f:
    content = f.readlines()



print(protest_count(content))
print(get_doc_count(content))
#print(count_tokens(content)['B-place'])
print(protest_with_place(content)/protest_count(content))
print(protest_with_flair(content)/protest_count(content))


print(protest_with_flair(content))
print(protest_with_place(content))



file_dict = {
    "total_document" : get_doc_count(content),
    "protest_with_flair": protest_with_flair(content),
    "protest_with_place": protest_with_place(content),
    "protest_with_flair_total_protest_ratio": protest_with_flair(content)/protest_count(content),
    "protest_with_place_total_protest_ratio": protest_with_place(content)/protest_count(content),
    "frequency of tokens ": count_tokens(content)

    }



if file_type == "csv":
    with open('mycsvfile.csv', 'w') as f:  # Just use 'w' mode in 3.x
        w = csv.DictWriter(f, file_dict.keys())
        w.writeheader()
        w.writerow(file_dict)
else:
    with open('mycsvfile.json', 'w') as fp:
        json.dump(file_dict, fp)




























































