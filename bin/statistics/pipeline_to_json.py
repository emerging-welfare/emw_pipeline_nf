import glob
import json
from collections import Counter
import csv
import json

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

"""
protest_flair_count = 0
place_name_list = []
flair_name_list = []
count = 0
empty_list_flair_output = 0
protest_but_no_place = 0
protest_but_no_place_list = []
"""


"""
Dictionary başta eklemek lazım
öncesindekilerde eklenmemiş olacak
"""

json_list = []
token_list_all = []
for elem in glob.glob("new_india/19052020_10k/*.json"):
    print(elem)
    with open(elem) as f:
        content = json.loads(f.read())

    for elem in content['token_labels']:
        if elem.startswith("B-") and elem not in token_list_all:
            print(elem)
            token_list_all.append(elem)
print(token_list_all)








json_file = open("pipeline_to_json.json", "w+")
for elem in glob.glob("new_india/19052020_10k/*.json"):
    with open(elem) as f:
        content = json.loads(f.read())



        content = postprocess(content)

    doc_json = {}
    doc_json['document'] = {}
    doc_json['document']['sentences'] = []
    doc_json['document']['id'] = content['id']
    doc_json['document']['url'] = ""
    doc_json['document']['title'] = content['title']
    doc_json['document']['is_violent'] = content['is_violent']





    #print(content)
    for sent_idx,sentence_tokens in enumerate(content['token_labels']):
        json_sentence = {}
        json_sentence['sentence'] = content['sentences'][sent_idx]
        for token_feature in token_list_all:
            json_sentence[token_feature] = []
            for idx, token in enumerate(sentence_tokens):
                if token.startswith(token_feature):
                    token_items = []
                    token_items.append(content['tokens'][sent_idx][idx])
                    for second_index, elem in enumerate(content['token_labels'][sent_idx][idx+1:]):
                        #print(elem)

                        if elem.startswith("I-"+token_feature[1:]):
                            #print(content['id'])
                            token_items.append(content['tokens'][sent_idx][idx+second_index+1])
                        else:
                            break
                        
                    print(token_items)
                    full_item = " ".join(token_items)
                    print(full_item)
                    json_sentence[token_feature].append(full_item)
                    #print(json_sentence)
        #print(json_sentence)
        doc_json['document']['sentences'].append(json_sentence)
        print(doc_json)
        #print(doc_json)
    
                    
    json_file.write(json.dumps(doc_json)+"\n")

            #print(content['sentences'][idx])



"""
    {
        document : {
            document_id: "",
            document_url: "",
            title: "",
            is_violent : 1,
            sentences : [
                {sentence_idx : 2, partipant_semantic, organizer_semantic, sentence_label, target_semantic, trigger_semantic<},
                {}
            ],

        }
    }

    
    
    tüm   featureları kontrol et yoksa json list append
    bunun output'undan istatistik
    json dosyaya yazdır
    dosyaya tarih ekle

"""