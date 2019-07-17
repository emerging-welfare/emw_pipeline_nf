#!/usr/bin/env python3
import markdown
import os
import shelve
import json
from sutime import SUTime

# Import the framework
from flask import Flask, g
from flask_restful import Resource, Api, reqparse
import pickle
# Create an instance of Flask
app = Flask(__name__)

# Create the API
api = Api(app)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = shelve.open("tt.db")
    return db

@app.teardown_appcontext
def teardown_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route("/")
def index():
    # Open the README file
    #with open(os.path.dirname(app.root_path) + '/README.md', 'r') as markdown_file:
    # Read the content of the file
    #content = str("\n ".join(main(file)))

    # Convert to HTML
    return markdown.markdown("TT is loaded")

def startJVM():
    jar_files = os.path.join(os.path.dirname(__file__), 'jars')
    sutime = SUTime(jars=jar_files, mark_time_ranges=True)
    return sutime

class queryList(Resource):
    def get(self):
        shelf = get_db()
        keys = list(shelf.keys())

        queries = []

        for key in keys:
            queries.append(shelf[key])

        return  queries, 200

    def post(self):
        parser = reqparse.RequestParser()

        parser.add_argument('identifier', required=True)
        #parser.add_argument('text', required=True)
        parser.add_argument('temporaltaggers', required=False)
        parser.add_argument('eventSenteces', required=True)
        # Parse the arguments into an object
        args = parser.parse_args()
        args["temporaltaggers"]=json.loads(json.dumps(sutime.parse(args["eventSenteces"])))
        shelf = get_db()
        shelf[args['identifier']] = args
        #return {'message': 'Query registered', 'data': args,'output':a_str }, 201
        return args, 201


class Device(Resource):
    def get(self, identifier):
        shelf = get_db()

        # If the key does not exist in the data store, return a 404 error.
        if not (identifier in shelf):
            return {'message': 'Device not found', 'data': {}}, 404

        return {'message': 'Device found', 'data': shelf[identifier]}, 200

    def delete(self, identifier):
        shelf = get_db()

        # If the key does not exist in the data store, return a 404 error.
        if not (identifier in shelf):
            return {'message': 'Device not found', 'data': {}}, 404

        del shelf[identifier]
        return '', 204


global sutime
sutime=startJVM()
api.add_resource(queryList, '/tts')
api.add_resource(Device, '/tt/<string:identifier>')
app.run(host='0.0.0.0', port=4999, debug=True)
