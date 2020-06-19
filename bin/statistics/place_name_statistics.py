import json
from collections import Counter
import argparse


parser = argparse.ArgumentParser(description='Place name information for India Provinces')
parser.add_argument('--input', type=str, help='Pipeline to json table')

args = parser.parse_args()
input_folder = args.input

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
        count_json[elem] = Counter(count_json[elem])
    return count_json




with open(input_folder, "r") as f:
    content = f.readlines()

tokens = count_tokens(content)

print(tokens['B-place'])

with open("india_states_unions.txt", "r") as f:
    states = f.read().splitlines()

print(states)

def token_province_ratio(tokens, tag):
    b_place_count = 0
    for elem in tokens[tag]:
        if elem in states:
            b_place_count = b_place_count + 1


    print(b_place_count/len(tokens[tag]))

    state_count = 0
    for elem in states:
        if elem in tokens[tag]:
            state_count = state_count + 1

    print(state_count/len(states))






token_province_ratio(tokens, "B-place")
token_province_ratio(tokens, "flair")


