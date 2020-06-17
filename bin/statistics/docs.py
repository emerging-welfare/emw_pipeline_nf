import json
from collections import Counter


def get_doc_count(content):
    return len(content)

def protest_count(content):
    count = 0
    for elem in content:
        data = json.loads(str(elem))
        if data['document']['is_violent'] == 1:
            count = count + 1
    return count


def count_tokens(content):
    count_json = {}
    tokens = list(json.loads(str(content[0]))['document']['sentences'][0].keys())
    tokens.remove('sentence')
    for elem in tokens:
        count_json[elem] = []
    print(count_json)
    for doc in content:
        data = json.loads(doc)
        for elem in tokens:
            for sentence in data['document']['sentences']:
                print(sentence)
                if not sentence[elem]:
                    pass
                else:
                    for item in sentence[elem]:
                        count_json[elem].append(item)
    for elem in count_json.keys():
        count_json[elem] = Counter(count_json[elem])
    return count_json
    


with open("/home/heyo/code/emw_pipeline_code_server/pipeline_to_json.json", "r") as f:
    content = f.readlines()



print(protest_count(content))
print(get_doc_count(content))
print(count_tokens(content)['B-place'])