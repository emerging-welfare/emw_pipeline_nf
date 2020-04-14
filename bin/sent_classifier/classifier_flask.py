import os
import numpy
from pathlib import Path
import torch
import argparse
from pytorch_pretrained_bert.modeling import BertForSequenceClassification
# Import the framework
from flask import Flask, g
from flask_restful import Resource, Api, reqparse
# Create an instance of Flask
app = Flask(__name__)

# Create the API
api = Api(app)

PYTORCH_PRETRAINED_BERT_CACHE = Path(os.getenv('PYTORCH_PRETRAINED_BERT_CACHE',
                                               Path.home() / '.pytorch_pretrained_bert'))

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

def prepare_data(sentences, max_seq_length):
    input_ids_all = torch.zeros((len(sentences), max_seq_length), dtype=torch.long)
    input_mask_all = torch.zeros((len(sentences), max_seq_length), dtype=torch.long)
    segment_ids_all = torch.zeros((len(sentences), max_seq_length), dtype=torch.long)
    for i,input_ids in enumerate(sentences):
        input_mask = [1] * len(input_ids)
        input_ids = input_ids + [0] * (max_seq_length - len(input_ids))
        input_mask = input_mask + [0] * (max_seq_length - len(input_mask))
        input_ids = torch.tensor(input_ids, dtype=torch.long)
        input_mask = torch.tensor(input_mask, dtype=torch.long)

        input_ids_all[i,:] = input_ids
        input_mask_all[i,:] = input_mask

    return input_ids_all, input_mask_all, segment_ids_all

def get_args():
    '''
    This function parses and return arguments passed in
    '''
    parser = argparse.ArgumentParser(prog='classifier_flask.py',
                                     description='Flask Server for Sentence Classification')
    parser.add_argument('--gpu_number_protest', help="Insert the gpu count/number , if more than gpu will be allocated please use the following format '0,1,2,3', where 0,1,2 and 3 gpus will be allocated.\n or just type the number of required gpu, i.e 6 ",default='6')
    parser.add_argument('--gpu_number_tsc', help="Insert the gpu number",default='3')
    parser.add_argument('--gpu_number_psc', help="Insert the gpu number, i.e 6 ",default='4')
    parser.add_argument('--gpu_number_osc', help="Insert the gpu number, i.e 6 ",default='5')

    args = parser.parse_args()
    return(args)

def predict(input_ids, input_mask, segment_ids, model, device):
    input_ids = input_ids.to(device)
    input_mask = input_mask.to(device)
    segment_ids = segment_ids.to(device)

    logits = model(input_ids, segment_ids, input_mask)
    logits = logits.detach().cpu().numpy()
    labels = numpy.argmax(logits, axis=1)
    return labels.tolist()

class queryList(Resource):
    def post(self):
        parser = reqparse.RequestParser()
#        parser.add_argument('identifier', required=True)
        parser.add_argument('sentences', required=False, type=str, action='append', default=[])
        parser.add_argument('output', required=False)
        args = parser.parse_args()

        sentences = [[int(tok) for tok in token_ids.split()] for token_ids in args['sentences']]
        input_ids, input_mask, segment_ids = prepare_data(sentences, max_seq_length)

        output_protest = predict(input_ids, input_mask, segment_ids, model_protest, device_protest)
        output_sem = predict(input_ids, input_mask, segment_ids, model_sem, device_trigger)
        output_part_sem = predict(input_ids, input_mask, segment_ids, model_part_sem, device_part)
        output_org_sem = predict(input_ids, input_mask, segment_ids, model_org_sem, device_org)

        args["output_protest"] = output_protest
        args["trigger_sem"] = output_sem # trigger_sem_label_list[output_sem].tolist()
        args["part_sem"] = output_part_sem # partic_sem_label_list[output_part_sem].tolist()
        args["org_sem"] = output_org_sem # org_sem_label_list[output_org_sem].tolist()
        # NOTE : Note that we are returning int values here not the actual label strings even though we have the label lists. This is because of the "r+" trick in sent_classifier.py. If the written text's length is smaller than the read text's length, we would be in trouble (For example; if a label got changed with a label that has less characters in it). So in order to prevent this we use integers, and we can make them strings again at postprocessing
        return args, 201

#gloabl configuration
max_seq_length = 128
HOME=os.getenv("HOME")
bert_model = HOME+ "/.pytorch_pretrained_bert/bert-base-uncased.tar.gz"
# device_cpu = torch.device("cpu")

args=get_args()

#### Trigger Semantic Categorization ####
trigger_sem_label_list = numpy.array(['arm_mil', 'demonst', 'ind_act', 'group_clash'])
trigger_sem_model = HOME+"/.pytorch_pretrained_bert/sem_cats_128.pt"
num_labels_sem = len(trigger_sem_label_list)
model_sem = BertForSequenceClassification.from_pretrained(bert_model, PYTORCH_PRETRAINED_BERT_CACHE, num_labels=num_labels_sem)

model_sem.load_state_dict(torch.load(trigger_sem_model, map_location='cpu'))
gpu_range = args.gpu_number_tsc.split(",")
if len(gpu_range) == 1:
    device_trigger = torch.device("cuda:{0}".format(int(gpu_range[0])))
elif len(gpu_range) >= 2:
    device_ids = [int(x) for x in gpu_range]
    device_trigger = torch.device("cuda:{0}".format(int(device_ids[0])))
    model_sem = torch.nn.DataParallel(model_sem,device_ids=device_ids,output_device=device_trigger, dim=0)

model_sem.to(device_trigger)
model_sem.eval()
# ######

# ### Participant Semantic Categorization ###
part_sem_model_path = HOME+"/.pytorch_pretrained_bert/part_sem_cats_128.pt"
part_sem_label_list = ['halk', 'militan', 'aktivist', 'köylü', 'öğrenci', 'siyasetçi', 'profesyonel', 'işçi', 'esnaf/küçük üretici', "No"]
num_labels_sem_part = len(part_sem_label_list)
model_part_sem = BertForSequenceClassification.from_pretrained(bert_model, PYTORCH_PRETRAINED_BERT_CACHE, num_labels=num_labels_sem_part)

model_part_sem.load_state_dict(torch.load(part_sem_model_path, map_location='cpu'))
gpu_range = args.gpu_number_psc.split(",")
if len(gpu_range) == 1:
    device_part = torch.device("cuda:{0}".format(int(gpu_range[0])))
elif len(gpu_range) >= 2:
    device_ids = [int(x) for x in gpu_range]
    device_part = torch.device("cuda:{0}".format(int(device_ids[0])))
    model_part_sem = torch.nn.DataParallel(model_part_sem,device_ids=device_ids,output_device=device_part, dim=0)

model_part_sem.to(device_part)
model_part_sem.eval()
# #####

# ### Organizer Semantic Categorization ###
org_sem_model_path = HOME+"/.pytorch_pretrained_bert/org_sem_cats_128.pt"
org_sem_label_list = ['Militant_Organization', 'Political_Party', 'Chambers_of_Professionals', 'Labor_Union', 'Grassroots_Organization', "No"]
num_labels_org_sem = len(org_sem_label_list)
model_org_sem = BertForSequenceClassification.from_pretrained(bert_model, PYTORCH_PRETRAINED_BERT_CACHE, num_labels=num_labels_org_sem)

model_org_sem.load_state_dict(torch.load(org_sem_model_path, map_location='cpu'))
gpu_range = args.gpu_number_osc.split(",")
if len(gpu_range) == 1:
    device_org = torch.device("cuda:{0}".format(int(gpu_range[0])))
elif len(gpu_range) >= 2:
    device_ids = [int(x) for x in gpu_range]
    device_org = torch.device("cuda:{0}".format(int(device_ids[0])))
    model_org_sem = torch.nn.DataParallel(model_org_sem,device_ids=device_ids,output_device=device_part, dim=0)

model_org_sem.to(device_org)
model_org_sem.eval()
# #####

### protest classifier ####
model_path_protest_path = HOME+ "/.pytorch_pretrained_bert/sent_model.pt"
label_list_protest = ["0", "1"]
num_labels_protest = len(label_list_protest)
model_protest = BertForSequenceClassification.from_pretrained(bert_model, PYTORCH_PRETRAINED_BERT_CACHE, num_labels=num_labels_protest)

model_protest.load_state_dict(torch.load(model_path_protest_path, map_location='cpu'))
gpu_range = args.gpu_number_protest.split(",")
if len(gpu_range)==1:
    device_protest = torch.device("cuda:{0}".format(int(gpu_range[0])))
elif len(gpu_range)>=2:
    device_ids = [int(x) for x in gpu_range]
    device_protest = torch.device("cuda:{0}".format(int(device_ids[0])))
    model_protest = torch.nn.DataParallel(model_protest,device_ids=device_ids,output_device=device_protest, dim=0)

model_protest.to(device_protest)
model_protest.eval()
#####

api.add_resource(queryList, '/queries')
app.run(host='0.0.0.0', port=4999, debug=True)
