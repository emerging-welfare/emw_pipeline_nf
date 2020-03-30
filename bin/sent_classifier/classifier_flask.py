import os
import numpy
from pathlib import Path
import torch
import argparse
from pytorch_pretrained_bert.tokenization import BertTokenizer
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

def prepare_data(sentences, label_list, max_seq_length, tokenizer):
    batches = []
    for i in range(0,len(sentences),batchsize):
        input_ids_all = []
        input_mask_all = []
        segment_ids_all = []
        if len(sentences) - i > batchsize: length = batchsize
        else: length = len(sentences) - i
        for j in range(length):
            input_ids, input_mask, segment_ids = convert_text_to_features(sentences[i+j], label_list, max_seq_length, tokenizer)
            input_ids = torch.tensor(input_ids, dtype=torch.long).unsqueeze(0)
            input_mask = torch.tensor(input_mask, dtype=torch.long).unsqueeze(0)
            segment_ids = torch.tensor(segment_ids, dtype=torch.long).unsqueeze(0)

            input_ids_all.append(input_ids)
            input_mask_all.append(input_mask)
            segment_ids_all.append(segment_ids)

        batches.append((torch.cat(input_ids_all, dim=0), torch.cat(input_mask_all, dim=0), torch.cat(segment_ids_all, dim=0)))

    return batches

def convert_text_to_features(text, label_list, max_seq_length, tokenizer):
    label_map = {}
    for (i, label) in enumerate(label_list):
        label_map[label] = i

    tokens_a = tokenizer.tokenize(text)
    if len(tokens_a) > max_seq_length - 2:
        tokens_a = tokens_a[0:(max_seq_length - 2)]

    tokens = []
    segment_ids = []
    tokens.append("[CLS]")
    segment_ids.append(0)

    for token in tokens_a:
        tokens.append(token)
        segment_ids.append(0)

    tokens.append("[SEP]")
    segment_ids.append(0)

    input_ids = tokenizer.convert_tokens_to_ids(tokens)
    input_mask = [1] * len(input_ids)

    while len(input_ids) < max_seq_length:
        input_ids.append(0)
        input_mask.append(0)
        segment_ids.append(0)

    assert len(input_ids) == max_seq_length
    assert len(input_mask) == max_seq_length
    assert len(segment_ids) == max_seq_length

    return input_ids, input_mask, segment_ids

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



def predict(sentences,label_list,model,device):# protest classifier output list
    all_labels = [] 
    batches = prepare_data(sentences, label_list, max_seq_length, tokenizer)
    for batch in batches:
        input_ids, input_mask, segment_ids = batch
        input_ids = input_ids.to(device)
        input_mask = input_mask.to(device)
        segment_ids = segment_ids.to(device)
        logits = model(input_ids, segment_ids, input_mask)
        logits = logits.detach().cpu().numpy()

        labels = numpy.argmax(logits, axis=1)
        all_labels.extend(labels.tolist())

    return all_labels

class queryList(Resource):
    def post(self):
        parser = reqparse.RequestParser()
#        parser.add_argument('identifier', required=True)
        parser.add_argument('sentences', required=False, type=str, action='append', default=[])
        parser.add_argument('output', required=False)
        args = parser.parse_args()
        output_protest = predict(args['sentences'],label_list_protest,model_protest,device_protest)
        output_sem = predict(args['sentences'],trigger_sem_label_list,model_sem,device_Trigger)
        output_partic_sem = predict(args['sentences'],partic_sem_label_list,model_partic_sem,device_Partic)
        output_org_sem = predict(args['sentences'],org_sem_label_list,model_org_sem,device_Org)
        args["output_protest"] = output_protest
        args["output_sem"] = trigger_sem_label_list[output_sem].tolist()
        args["partic_sem"]=partic_sem_label_list[output_partic_sem].tolist()
        args["org_sem"]=org_sem_label_list[output_org_sem].tolist()
        return args, 201

#gloabl configuration
max_seq_length = 128
batchsize = 32
HOME=os.getenv("HOME")
bert_model = HOME+ "/.pytorch_pretrained_bert/bert-base-uncased.tar.gz"
bert_vocab = HOME+ "/.pytorch_pretrained_bert/bert-base-uncased-vocab.txt"
tokenizer = BertTokenizer.from_pretrained(bert_vocab)

args=get_args()

#### Trigger Semantic Categorization ####
trigger_sem_label_list=numpy.array(['arm_mil', 'demonst', 'ind_act', 'group_clash'])
trigger_sem_model=HOME+"/.pytorch_pretrained_bert/sem_cats_128.pt"
num_labels_sem=len(trigger_sem_label_list)
model_sem= BertForSequenceClassification.from_pretrained(bert_model, PYTORCH_PRETRAINED_BERT_CACHE, num_labels=num_labels_sem)
device_Trigger=torch.device("cuda:{0}".format((int(args.gpu_number_tsc))))
model_sem.load_state_dict(torch.load(trigger_sem_model, map_location='cpu'))
model_sem.to(device_Trigger)
######

### Participant Semantic Categorization ### 
partic_sem_model_path =HOME+"/.pytorch_pretrained_bert/part_sem_cats_128.pt"
partic_sem_label_list=numpy.array(['halk', 'militan', 'aktivist', 'köylü', 'öğrenci', 'siyasetçi', 'profesyonel', 'işçi', 'esnaf/küçük üretici', "No"])
num_labels_sem_part=len(partic_sem_label_list)
model_partic_sem= BertForSequenceClassification.from_pretrained(bert_model, PYTORCH_PRETRAINED_BERT_CACHE, num_labels=num_labels_sem_part)
device_Partic=torch.device("cuda:{0}".format((int(args.gpu_number_psc))))
model_partic_sem.load_state_dict(torch.load(partic_sem_model_path, map_location='cpu'))
model_partic_sem.to(device_Partic)
#####

### Organizer Semantic Categorization ### 
org_sem_model_path =HOME+"/.pytorch_pretrained_bert/org_sem_cats_128.pt"
org_sem_label_list=numpy.array(['Militant_Organization', 'Political_Party', 'Chambers_of_Professionals', 'Labor_Union', 'Grassroots_Organization', "No"])
num_labels_org_sem=len(org_sem_label_list)
model_org_sem= BertForSequenceClassification.from_pretrained(bert_model, PYTORCH_PRETRAINED_BERT_CACHE, num_labels=num_labels_org_sem)
model_org_sem.load_state_dict(torch.load(org_sem_model_path, map_location='cpu'))
device_Org=torch.device("cuda:{0}".format((int(args.gpu_number_osc))))
model_org_sem.to(device_Org)
#####

### protest classifier #### 
model_path_protest_path = HOME+ "/.pytorch_pretrained_bert/sent_model.pt"
label_list_protest = ["0", "1"]
num_labels_protest = len(label_list_protest)
model_protest = BertForSequenceClassification.from_pretrained(bert_model, PYTORCH_PRETRAINED_BERT_CACHE, num_labels=num_labels_protest)
model_protest.load_state_dict(torch.load(model_path_protest_path, map_location='cpu'))
if torch.cuda.is_available():
    gpu_range=args.gpu_number_protest.split(",")
    if len(gpu_range)==1:
        device_protest=torch.device("cuda:{0}".format(int(gpu_range[0])))
    elif len(gpu_range)>=2:
        device_ids= [int(x) for x in gpu_range]
        device_protest=torch.device("cuda:{0}".format(int(device_ids[0])))
        model_protest = torch.nn.DataParallel(model_protest,device_ids=device_ids,output_device=device_protest, dim=0)

    model_protest.to(device_protest)
else:
    device_protest = torch.device("cpu")
    model_protest.to(device_protest)
#####

api.add_resource(queryList, '/queries')
app.run(host='0.0.0.0', port=4999, debug=True)
