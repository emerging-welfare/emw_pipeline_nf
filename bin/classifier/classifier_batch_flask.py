import os
from nltk import sent_tokenize
import numpy
from pathlib import Path
import torch
from pytorch_pretrained_bert.tokenization import BertTokenizer
from pytorch_pretrained_bert.modeling import BertForSequenceClassification
from sklearn.externals import joblib
import argparse
# Import the framework
from flask import Flask, g
from flask_restful import Resource, Api, reqparse
# Create an instance of Flask
app = Flask(__name__)

# Create the API
api = Api(app)

PYTORCH_PRETRAINED_BERT_CACHE = Path(os.getenv('PYTORCH_PRETRAINED_BERT_CACHE', Path.home() / '.pytorch_pretrained_bert'))
HOME = os.getenv("HOME")

BATCHSIZE = 10

def text_iter(text, max_length=512):
    """splits long text into a chunk of max_length"""
    sentences = sent_tokenize(text)
    sentences_lengths = []

    for s in sentences:
        s_length = len(tokenizer.tokenize(s))
        sentences_lengths.append(s_length if s_length < max_length else max_length)

    text_length = 0
    chunk = ''

    for i, s in enumerate(sentences):
        if text_length + sentences_lengths[i] >= max_length:
            yield chunk
            chunk = s
            text_length = sentences_lengths[i]
        else:
            chunk += ' ' + s
            text_length += sentences_lengths[i]
    yield chunk


def convert_text_to_features(text, max_seq_length, tokenizer):

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


def get_predictions(inputs, max_length=512):
    global tokenizer
    all_input_ids, all_input_masks, all_segment_ids = [], [], []
    
    inputs = [ convert_text_to_features(i, max_length, tokenizer) for i in inputs ]

    for i_ids, i_masks, s_ids in inputs:
        all_input_ids.append(torch.tensor(i_ids, dtype=torch.long).unsqueeze(0))
        all_input_masks.append(torch.tensor(i_masks, dtype=torch.long).unsqueeze(0))
        all_segment_ids.append(torch.tensor(s_ids, dtype=torch.long).unsqueeze(0))

    all_input_ids = torch.cat(all_input_ids, dim=0).to(device)
    all_input_masks = torch.cat(all_input_masks, dim=0).to(device)
    all_segment_ids = torch.cat(all_segment_ids, dim=0).to(device)
    logits = model(all_input_ids, all_segment_ids, all_input_masks)
    logits = logits.detach().cpu().numpy()
    labels = numpy.argmax(logits, axis=1).tolist()

    return labels


def predict(docs):
    chunks = []
    chunk_sizes = []
    
    for doc in docs:
        doc_chunks = list(text_iter(doc))
        chunk_sizes.append(len(doc_chunks))
        chunks += doc_chunks
    
    chunks_labels = []
    for b in range(0, len(chunks), BATCHSIZE):
        current_batch = chunks[b:b + BATCHSIZE]
        chunks_labels += get_predictions(current_batch)

    i = 0
    doc_labels = []
    for s in chunk_sizes:
        doc_labels.append((1 if 1 in chunks_labels[i:i+s] else 0))
        i += s

    return doc_labels

class queryList(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('texts', required=False, type=str, action='append', default=[])
        parser.add_argument('outputs', required=False)
        parser.add_argument('event_sentences', required=False)
        # Parse the arguments into an object
        args = parser.parse_args()
        args["outputs"] = predict(args['texts'])
        args["event_sentences"] = list()
        for i,output in enumerate(args["outputs"]):
           args["event_sentences"].append(sent_tokenize(args['texts'][i]))

        return args, 201

def get_args():
    '''
    This function parses and return arguments passed in
    '''
    parser = argparse.ArgumentParser(prog='classifier_batch_flask.py',
                                     description='Flask Server for Document Classification')
    parser.add_argument('--gpu_number', help="Insert the gpu count/number , if more than gpu will be allocated please use the following format 0,1,3,5, where 0,1,3,5 gpus will be allocated.\n or just type the number of required gpu, i.e 6 ",default="0,1")
    parser.add_argument('--batch_size', help="Document model batch size", type=int, default=10)
    args = parser.parse_args()

    return(args)

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

label_list = ["0", "1"]
max_seq_length = 512
num_labels = len(label_list)

bert_model = HOME+"/.pytorch_pretrained_bert/bert-base-uncased.tar.gz"
bert_vocab = HOME+"/.pytorch_pretrained_bert/bert-base-uncased-vocab.txt"
model_path = HOME+"/.pytorch_pretrained_bert/doc_model.pt"

tokenizer = BertTokenizer.from_pretrained(bert_vocab)
model = BertForSequenceClassification.from_pretrained(bert_model, PYTORCH_PRETRAINED_BERT_CACHE, num_labels=num_labels)

if torch.cuda.is_available():
    model.load_state_dict(torch.load(model_path))
    args = get_args()
    BATCHSIZE = args.batch_size
    gpu_range = args.gpu_number.split(",")
    if len(gpu_range) == 1:
        device = torch.device("cuda:{0}".format(int(gpu_range[0])))
    elif len(gpu_range) >= 2:
        device_ids = [int(x) for x in gpu_range]
        device = torch.device("cuda:{0}".format(int(device_ids[0])))
        model = torch.nn.DataParallel(model,device_ids=device_ids,output_device=device, dim=0)
else:
    model.load_state_dict(torch.load(model_path, map_location='cpu'))
    device = torch.device("cpu")

model.to(device)
model.eval()

api.add_resource(queryList, '/queries')
app.run(host='0.0.0.0', port=5000, debug=True)
