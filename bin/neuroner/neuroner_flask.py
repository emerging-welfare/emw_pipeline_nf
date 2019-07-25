#!/usr/bin/env python3
from neuroner import neuromodel
# Import the framework
from flask import Flask
from flask_restful import Resource, Api, reqparse
# Create an instance of Flask
app = Flask(__name__)

# Create the API
api = Api(app)

@app.route("/")
def index():
    if nn is not None :
        return "<html><body><p>neuroner is loaded</p></body></html>"
    else :
        return "<html><body><p>neuroner is not loaded</p></body></html>"

class queryList(Resource):
    def post(self):
        parser = reqparse.RequestParser()

        parser.add_argument('tokens', required=False, type=str, action='append', default=[])
        parser.add_argument('output', required=False)
        args = parser.parse_args()
        tokens = args["tokens"]
        text = "\n".join(tokens)

        lengths = [len(token) + 1 for token in tokens]
        offsets = [sum(lengths[:i]) for i,a in enumerate(lengths)]
        output = ["O"] * len(tokens)

        preds = nn.predict(text)
        for pred in preds:
            try:
                output[offsets.index(int(pred["start"]))] = pred["type"]
            except: # combatants -> non-combatants
                offsets.append(pred["start"])
                output[sorted(offsets).index(pred["start"]) - 1] = pred["type"]
                offsets.pop()

        args["output"] = output

        # parser.add_argument('text', required=True)
        # parser.add_argument('output', required=False)
        # args = parser.parse_args()
        # args["output"] = nn.predict(args["text"])

        return args, 201

nn=neuromodel.NeuroNER(train_model=False,
                        use_pretrained_model=True,
                        pretrained_model_folder="/emw_pipeline_nf/bin/neuroner/model",
                        dataset_text_folder="/emw_pipeline_nf/bin/neuroner/test_folder",
                        tagging_format="bio",output_scores=False)

api.add_resource(queryList, '/queries')
app.run(host='0.0.0.0', port=4996, debug=True)
