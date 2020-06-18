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
    

json_list = []
token_list_all = []
file_id = 0
for elem in glob.glob("/data/pipeline_output/new_india/04072020_all/*.json"):
    print(elem)
    print(file_id)
    with open(elem) as f:
        content = json.loads(f.read())
    try:
        for elem in content['token_labels']:
            if elem.startswith("B-") and elem not in token_list_all:
                print(elem)
                token_list_all.append(elem)
    except:
        file_id = file_id + 1
        print("token label")









excp_count = 0
json_file = open("pipeline_to_json.json", "w+")
for elem in glob.glob("new_india/04072020_all/*.json"):
    with open(elem) as f:
        content = json.loads(f.read())
        

        try:
            content = postprocess(content)
        except:
            continue



    doc_json = {}
    doc_json['document'] = {}
    doc_json['document']['sentences'] = []
    doc_json['document']['id'] = content['id']
    doc_json['document']['url'] = ""
    doc_json['document']['doc_label'] = content['doc_label']
    doc_json['document']['title'] = content['title']
    doc_json['document']['is_violent'] = content['is_violent']


#10k output üzerinden protesto olanlarını json olarak hazırla

    for sent_idx,sentence_tokens in enumerate(content['token_labels']):
        json_sentence = {}
        json_sentence['sentence'] = content['sentences'][sent_idx]
        json_sentence['flair'] = []
        for token_feature in token_list_all:
            json_sentence[token_feature] = []
            for idx, token in enumerate(sentence_tokens):
                if token.startswith(token_feature):
                    token_items = []
                    token_items.append(content['tokens'][sent_idx][idx])
                    for second_index, elem in enumerate(content['token_labels'][sent_idx][idx+1:]):
                        #print(elem)

                        if elem.startswith("I-"+token_feature[2:]):
                            #print(content['id'])
                            token_items.append(content['tokens'][sent_idx][idx+second_index+1])
                        else:
                            break

                    #print(token_items)
                    full_item = " ".join(token_items)
                    print(full_item)
                    json_sentence[token_feature].append(full_item)
                    #print(json_sentence)
        #print(json_sentence)
        doc_json['document']['sentences'].append(json_sentence)
        #print(doc_json)
        #print(doc_json)
    try:
        flair_output = content['flair_output']
        # If it is protest and there is no flair output
        for elem in flair_output:
            #print(content['tokens'][elem[0]][elem[1]:elem[2]+1])
            #print(doc_json['document']['sentences'][elem[0]]['flair'])
            doc_json['document']['sentences'][elem[0]]['flair'].append(" ".join(content['tokens'][elem[0]][elem[1]:elem[2]+1]))
    except:
        print("There is no flair output")

                    
    json_file.write(json.dumps(doc_json)+"\n")

            #print(content['sentences'][idx])

print(excp_count)


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
"""

