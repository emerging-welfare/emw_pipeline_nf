#!/usr/bin/env python3
import os
import numpy
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

# Not finished yet
class queryList(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('tokens', required=False, type=str, action='append', default=[])
        text = "\n".join(tokens)
        lengths = [len(token.encode("utf-8")) + 1 for token in tokens]
        offsets = [sum(lengths[:i]) for i,a in enumerate(lengths)]
        args = parser.parse_args()
        return nn.predict(text), 201

nn=neuromodel.NeuroNER(train_model=False,
                        use_pretrained_model=True,
                        pretrained_model_folder="/model",
                        dataset_text_folder="/test_folder",
                        tagging_format="bio",output_scores=False
                        )

api.add_resource(queryList, '/queries')
app.run(host='0.0.0.0', port=4997, debug=True)
