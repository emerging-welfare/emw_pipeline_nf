import os
import numpy
import torch
import argparse
from transformers import AutoModel, AutoTokenizer
import flask
from flask_restful import Resource, Api
import flair

app = flask.Flask(__name__) # Create an instance of Flask
api = Api(app) # Create the API

@app.route("/")
def index():
    # Open the README file
    #with open(os.path.dirname(app.root_path) + '/README.md', 'r') as markdown_file:
    # Read the content of the file
    #content = str("\n ".join(main(file)))

    # Convert to HTML
    if classifer is not None :
        # return markdown.markdown("classifier is loaded")
        return "<html><body><p>classifier is loaded</p></body></html>"
    else :
        return "<html><body><p>classifier is not loaded</p></body></html>"
        # return markdown.markdown("classifier is not loaded")

def prepare_data(sentences, max_seq_length, has_token_type_ids=False):
    encoded_input = tokenizer(sentences, padding="max_length", truncation=True,
                              max_length=max_seq_length)
    input_ids = torch.tensor(encoded_input["input_ids"], dtype=torch.long)
    input_mask = torch.tensor(encoded_input["attention_mask"], dtype=torch.long)
    if has_token_type_ids:
        token_type_ids = torch.tensor(encoded_input["token_type_ids"], dtype=torch.long)
        return input_ids, input_mask, token_type_ids

    return input_ids, input_mask

def get_args():
    '''
    This function parses and return arguments passed in
    '''
    parser = argparse.ArgumentParser(prog='classifier_flask.py',
                                     description='Flask Server for Sentence Classification')
    parser.add_argument('--gpu_number_tsc', help="Insert the gpu number",default='3')
    parser.add_argument('--gpu_number_psc', help="Insert the gpu number, i.e 6 ",default='4')
    parser.add_argument('--gpu_number_osc', help="Insert the gpu number, i.e 6 ",default='5')
    parser.add_argument('--language', help="Source language. Ex: english")

    args = parser.parse_args()
    return(args)

def tag_places_flair(all_sentences):
    # Place Tagger
    all_flair_sentences = [flair.data.Sentence(sentence) for sentence in all_sentences]
    place_tagger.predict(all_flair_sentences)

    all_sent_place_tags = []
    for flair_sentence in all_flair_sentences:
        curr_sent_place_tags = []
        for span in flair_sentence.get_spans("ner"):
            if span.tag == "LOC":
                # Ids are 1-indexed for some reason
                idxs = sorted([tok.idx - 1 for tok in span.tokens])
                curr_sent_place_tags.append([idxs[0], idxs[-1]]) # start_idx of span and end_idx for span

        all_sent_place_tags.append(curr_sent_place_tags)

    return all_sent_place_tags


def predict(input_ids, input_mask, encoder, classifier, device):
    input_ids = input_ids.to(device)
    input_mask = input_mask.to(device)

    with torch.no_grad():
        embeddings = encoder(input_ids, attention_mask=input_mask)[1]
        logits = classifier(embeddings)

    logits = logits.detach().cpu().numpy()
    labels = numpy.argmax(logits, axis=1)
    return labels

class queryList(Resource):
    def post(self):
        args = flask.request.get_json(force=True)

        input_ids, input_mask = prepare_data(args["sentences"], max_seq_length)

        trig_out = predict(input_ids, input_mask, trig_encoder, trig_classifier, trig_device)
        part_out = predict(input_ids, input_mask, part_encoder, part_classifier, part_device)
        org_out = predict(input_ids, input_mask, org_encoder, org_classifier, org_device)

        if place_tagger is not None:
            place_output = tag_places_flair(args["sentences"])
        else:
            place_output = []

        out_data = {}
        out_data["trigger_sem"] = trig_label_list[trig_out].tolist()
        out_data["part_sem"] = part_label_list[part_out].tolist()
        out_data["org_sem"] = org_label_list[org_out].tolist()
        out_data["flair_output"] = place_output
        return out_data, 201

#### Global configuration
HOME=os.getenv("HOME")
max_seq_length = 128
encoder_pretrained_model = "sentence-transformers/paraphrase-xlm-r-multilingual-v1"
tokenizer = AutoTokenizer.from_pretrained(encoder_pretrained_model)
args=get_args()
language = args.language

# NOTE: Flair model only works for English and Spanish.
FLAIR_CACHE_ROOT = HOME +  "/.pytorch_pretrained_bert"
place_tagger = None
if language == "english":
    place_tagger = flair.models.SequenceTagger.load("flair/ner-english-large") # flair/ner-english-fast
    place_tagger.eval()
elif language == "spanish":
    place_tagger = flair.models.SequenceTagger.load("flair/ner-spanish-large") # flair/ner-multi-fast
    place_tagger.eval()

####

# TODO: Could have just merged the encoder and classifier parts of the models into 1 model.

#### Trigger Semantic Categorization ####
trig_label_list = numpy.array(["Demonstration", "Armed Militancy", "Group Clash",
                               "Industrial Action", "Other"])
trig_encoder_path = HOME+"/.pytorch_pretrained_bert/multilingual_trig_sem_encoder.pt"
trig_classifier_path = HOME+"/.pytorch_pretrained_bert/multilingual_trig_sem_classifier.pt"

trig_encoder = AutoModel.from_pretrained(encoder_pretrained_model)
# trig_classifier = MLP(trig_encoder.config.hidden_size, trig_encoder.config.hidden_size * 4,
#                       len(trig_label_list))
trig_classifier = torch.nn.Linear(trig_encoder.config.hidden_size, len(trig_label_list))

gpu_range = args.gpu_number_tsc.split(",")
trig_device = torch.device("cuda:{0}".format(int(gpu_range[0])))
trig_encoder.load_state_dict(torch.load(trig_encoder_path, map_location=trig_device))
trig_classifier.load_state_dict(torch.load(trig_classifier_path, map_location=trig_device))
if len(gpu_range) >= 2:
    device_ids = [int(x) for x in gpu_range]
    trig_encoder = torch.nn.DataParallel(trig_encoder, device_ids=device_ids)

trig_encoder.to(trig_device)
trig_classifier.to(trig_device)
trig_encoder.eval()
trig_classifier.eval()
# ######

# ### Participant Semantic Categorization ###
part_label_list = numpy.array(["Peasant", "Proletariat", "Professional", "Student", "Masses",
                               "Politician", "Activist", "Militant", "Other", "No"])
part_encoder_path = HOME+"/.pytorch_pretrained_bert/multilingual_part_sem_encoder.pt"
part_classifier_path = HOME+"/.pytorch_pretrained_bert/multilingual_part_sem_classifier.pt"

part_encoder = AutoModel.from_pretrained(encoder_pretrained_model)
# part_classifier = MLP(part_encoder.config.hidden_size, part_encoder.config.hidden_size * 4,
#                       len(part_label_list))
part_classifier = torch.nn.Linear(part_encoder.config.hidden_size, len(part_label_list))

gpu_range = args.gpu_number_psc.split(",")
part_device = torch.device("cuda:{0}".format(int(gpu_range[0])))
part_encoder.load_state_dict(torch.load(part_encoder_path, map_location=part_device))
part_classifier.load_state_dict(torch.load(part_classifier_path, map_location=part_device))
if len(gpu_range) >= 2:
    device_ids = [int(x) for x in gpu_range]
    part_encoder = torch.nn.DataParallel(part_encoder, device_ids=device_ids)

part_encoder.to(part_device)
part_classifier.to(part_device)
part_encoder.eval()
part_classifier.eval()
# #####

# ### Organizer Semantic Categorization ###
org_label_list = numpy.array(["Political Party", "Grassroots Organization", "Labor Union",
                              "Militant Organization", "Chambers of Professionals", "No"])
org_encoder_path = HOME+"/.pytorch_pretrained_bert/multilingual_org_sem_encoder.pt"
org_classifier_path = HOME+"/.pytorch_pretrained_bert/multilingual_org_sem_classifier.pt"

org_encoder = AutoModel.from_pretrained(encoder_pretrained_model)
# org_classifier = MLP(org_encoder.config.hidden_size, org_encoder.config.hidden_size * 4,
#                       len(org_label_list))
org_classifier = torch.nn.Linear(org_encoder.config.hidden_size, len(org_label_list))

gpu_range = args.gpu_number_osc.split(",")
org_device = torch.device("cuda:{0}".format(int(gpu_range[0])))
org_encoder.load_state_dict(torch.load(org_encoder_path, map_location=org_device))
org_classifier.load_state_dict(torch.load(org_classifier_path, map_location=org_device))
if len(gpu_range) >= 2:
    device_ids = [int(x) for x in gpu_range]
    org_encoder = torch.nn.DataParallel(org_encoder, device_ids=device_ids)

org_encoder.to(org_device)
org_classifier.to(org_device)
org_encoder.eval()
org_classifier.eval()
# #####

api.add_resource(queryList, '/queries')
app.run(host='0.0.0.0', port=4999, debug=False)
