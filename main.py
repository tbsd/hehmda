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

from utils import validate_session, push_to_db


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
    db = client['db']
    users = db['users']
    chats = db['chats']
    # global
    # client = pymongo.MongoClient("mongodb+srv://testing-repo:testing-repo@testing-repo-4xvfr.mongodb.net/admin?retryWrites=true&w=majority")

    # 404 error handler
    @app.errorhandler(404)
    def not_found(error):
        return render_template('error.html')

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
        user = validate_session(users, request)
        if user:
            info = users.find_one({'id': user['id']},
                                  {'_id': 0, 'id': 1, 'contacts': 1})
            return json_util.dumps(info)
        return render_template('error.html')

    # get all chats
    @app.route('/api/v1/users/chats')
    def get_all_chats():
        user = validate_session(users, request)
        if user:
            chats_id = user['chat_list']
            info = chats.find({'id': {'$in': chats_id}}, {'_id': 0})
            return json_util.dumps(info)
        return render_template('error.html')

    # adds contact to current user by given id
    @app.route('/api/v1/users/addcontact', methods=['POST'])
    def add_contact():
        user = validate_session(users, request)
        data = request.get_json(force=True)
        print('\n\n\n')
        new_contact = users.find_one({'id': data['id']},
                                     {'_id': 0, 'id': 1, 'nickname': 1})
        new_contact_json = json_util.dumps(new_contact)
        if new_contact:
            push_to_db(users, user['id'], 'contacts', new_contact_json)
        return new_contact_json

    # add user to chat
    @app.route('/api/v1/users/addtochat', methods=['POST'])
    def add_to_chat():
        user = validate_session(users, request)
        data = request.get_json(force=True)
        chat_id = data['chat_id']
        new_user_id = data['new_user_id']
        # only if user is member of this chat
        if (chat_id in user['chat_list']):
            new_user = users.find_one({'id': new_user_id},
                                  {'_id': 0, 'id': 1, 'chat_list': 1})
            if (new_user and chat_id not in new_user['chat_list']):
                push_to_db(chats, chat_id, 'users', new_user_id)
                push_to_db(users, new_user_id, 'chat_list', chat_id)
        updated_chat_users = json_util.dumps(
                chats.find_one({'id': chat_id},
                               {'_id': 0, 'id': 1, 'users': 1}))
        return updated_chat_users

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app = create_app()
    app.run(host="0.0.0.0", port=port)

