#!/usr/bin/env python3
"""
Documentation

See also https://www.python-boilerplate.com/flask
"""
import os
import json
import pymongo
import dns

from flask import Flask, jsonify, render_template, send_from_directory, request, make_response
from flask_cors import CORS
from pymongo import MongoClient
from bson import json_util

from utils import is_valid_session


def create_app(config=None):
    app = Flask(__name__)

    # See http://flask.pocoo.org/docs/latest/config/
    app.config.update(dict(DEBUG=True))
    app.config.update(config or {})

    # Setup cors headers to allow all domains
    # https://flask-cors.readthedocs.io/en/latest/
    CORS(app)

    # Definition of the routes. Put them into their own file. See also
    # Flask Blueprints: http://flask.pocoo.org/docs/latest/blueprints

    # MongoDB client
    # local
    client = MongoClient('localhost', 27017)
    # global
    # client = pymongo.MongoClient("mongodb+srv://testing-repo:testing-repo@testing-repo-4xvfr.mongodb.net/admin?retryWrites=true&w=majority")

    # main page
    @app.route("/")
    def hello_world():
        return render_template('index.html')

    # used for loading js to page
    @app.route('/js/<path:path>')
    def get_js(path):
        return send_from_directory('js', path)

    # get user contacts
    @app.route('/api/v1/users/contacts')
    def get_contacts():
        db = client['db']
        users = db['users']
        if is_valid_session(users, request):
            user_id = request.cookies['id']
            info = users.find_one({'id': user_id},
                                  {'_id': 0, 'id': 1, 'contacts': 1})
            return json_util.dumps(info)
        return ''

    # get all chats
    @app.route('/api/v1/users/chats')
    def get_all_chats():
        db = client['db']
        users = db['users']
        chats = db['chats']
        if is_valid_session(users, request):
            user_id = request.cookies['id']
            chats_id = users.find_one({'id': user_id}, 
                                      {'chat_list': 1})['chat_list']
            info = chats.find({'id': {'$in': chats_id}}, {'_id': 0})
            return json_util.dumps(info)
        return ''

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app = create_app()
    app.run(host="0.0.0.0", port=port)

