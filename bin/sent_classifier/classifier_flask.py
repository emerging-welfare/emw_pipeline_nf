import os
import numpy
from pathlib import Path
import torch
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

def predict(sentences):
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

        output = predict(args['sentences'])
        args["output"] = output

        return args, 201


label_list = ["0", "1"]
max_seq_length = 128
batchsize = 32
HOME=os.getenv("HOME")
bert_model = HOME+ "/.pytorch_pretrained_bert/bert-base-uncased.tar.gz"
bert_vocab = HOME+ "/.pytorch_pretrained_bert/bert-base-uncased-vocab.txt"
model_path = HOME+ "/.pytorch_pretrained_bert/sent_model.pt"

num_labels = len(label_list)
# device = torch.device("cuda:1" if torch.cuda.is_available() else "cpu")
device = torch.device("cuda:6")

tokenizer = BertTokenizer.from_pretrained(bert_vocab)
model = BertForSequenceClassification.from_pretrained(bert_model, PYTORCH_PRETRAINED_BERT_CACHE, num_labels=num_labels)
if torch.cuda.is_available():
    model.load_state_dict(torch.load(model_path))
else:
    model.load_state_dict(torch.load(model_path, map_location='cpu'))

# model = torch.nn.DataParallel(model, device=device, dim=0)
model.to(device)

api.add_resource(queryList, '/queries')
app.run(host='0.0.0.0', port=4999, debug=True)
