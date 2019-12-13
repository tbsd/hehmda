#!/usr/bin/env python3
"""
Documentation

See also https://www.python-boilerplate.com/flask
"""
import os
import json
import pymongo
import dns
import time
import cgi

from flask import Flask, jsonify, render_template, send_from_directory, request, make_response, redirect, url_for
from flask_cors import CORS
from pymongo import MongoClient
from bson import json_util
from datetime import datetime
from utils import validate_session, push_to_db, random_string, random_id

# Cookies
from http import cookies


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
        new_contact = users.find_one({'id': data['id']},
                                     {'_id': 0, 'id': 1, 'nickname': 1})
        new_contact_json = json_util.dumps(new_contact)
        if new_contact:
            push_to_db(users, user['id'], 'contacts', new_contact)
        return new_contact_json

    # add user to chat
    @app.route('/api/v1/chats/addtochat', methods=['POST'])
    def add_to_chat():
        user = validate_session(users, request)
        data = request.get_json(force=True)
        chat_id = data['chat_id']
        new_user_id = data['new_user_id']
        # only if user is member of this chat
        if (user and chat_id in user['chat_list']):
            new_user = users.find_one({'id': new_user_id},
                                      {'_id': 0, 'id': 1, 'chat_list': 1})
            if (new_user and chat_id not in new_user['chat_list']):
                push_to_db(chats, chat_id, 'users', new_user_id)
                push_to_db(users, new_user_id, 'chat_list', chat_id)
        updated_chat_users = json_util.dumps(
            chats.find_one({'id': chat_id},
                           {'_id': 0, 'id': 1, 'users': 1}))
        return updated_chat_users

    # add message to chat
    @app.route('/api/v1/chats/send', methods=['POST'])
    def send():
        user = validate_session(users, request)
        data = request.get_json(force=True)
        chat_id = data['chat_id']
        # only if user is member of this chat
        if (user and chat_id in user['chat_list']):
            message_id = random_string()
            # timestamp in milliseconds
            timestamp = int(time.time()) * 1000
            content = data['content']
            # replace 'script' with its utf-8 code
            # to prevent malicious code execution
            content = content.replace('script',
                                      '&#x73;&#x63;&#x72;&#x69;&#x70;&#x74;')
            message = {'id': message_id,
                       'author': user['id'],
                       'time': timestamp,
                       'content': content}
            push_to_db(chats, chat_id, 'messages', message)
            return json_util.dumps(message)
        return json_util.dumps('')

    # get only new messages
    @app.route('/api/v1/chats/getnewmessages', methods=['POST'])
    def get_new_messages():
        user = validate_session(users, request)
        data = request.get_json(force=True)
        chat_id = data['chat_id']
        # only if user is member of this chat
        if (user and chat_id in user['chat_list']):
            last_id = data['last_id']
            chat = chats.find_one({'id': chat_id},
                                  {'_id': 0, 'id': 1, 'messages': 1})
            messages = chat['messages']
            last_index = 0
            for last_index in range(len(messages)):
                if last_id == messages[last_index]['id']:
                    break
            # if there is such id, send only new messages
            # else send all messages
            if (last_index + 1 != len(messages)):
                chat['messages'] = messages[last_index + 1: len(messages)]
            else:
                if last_id == messages[-1]['id']:
                    chat['messages'] = []
            return json_util.dumps(chat)
        return json_util.dumps('')

    # get members of the chat
    @app.route('/api/v1/chats/getusers', methods=['POST'])
    def get_users():
        user = validate_session(users, request)
        data = request.get_json(force=True)
        chat_id = data['chat_id']
        # only if user is member of this chat
        if (user and chat_id in user['chat_list']):
            chat = chats.find_one({'id': chat_id},
                                  {'_id': 0, 'id': 1, 'users': 1})
            return json_util.dumps(chat)
        return json_util.dumps('')

    # Login and password for registration

    @app.route('/api/v1/users/authorization', methods=['POST'])
    def authorization():
        # Считывание логина и пароля
        data = request.get_json(force=True)
        login = data['login']
        password = data['password']
        # Проверка, есть ли в базе данных эта личнасть
        if users.find({"login": login, "password_hash": password}).count() == 1:
            token = random_string(20)
            response = make_response()
            user = users.find_one({"login": login, "password_hash": password})
            users.find_one_and_update({'id': user['id']}, {'$set': {'session': token}})
            user = users.find_one({"login": login, "password_hash": password})
            response.set_cookie('session', user['session'])
            return response
        else:
            return json_util.dumps('')

    @app.route('/api/v1/users/registration', methods=['POST'])
    def registration():
        # Считывание логин, пароль, повтор пороля
        data = request.get_json(force=True)
        new_login = data['new_login']
        new_password = data['new_password']
        new_repeat_password = data['new_repeat_password']
        new_nickname = data['new_nickname']
        # Проверка, логина на дубляж и сравнение двух паролей.
        if users.find({"login": new_login}).count() == 0:
            new_id = random_id()
            while users.find_one({"id": new_id}):
                new_id = random_id()
            token = random_string()
            response = make_response()
            if new_password == new_repeat_password:
                users.insert_one({"id": new_id, "login": new_login,
                                  "password_hash": new_password,
                                  "nickname": new_nickname,
                                  "chat_list": [],
                                  "contacts": [], "session": token})
                response.set_cookie('session', token)
                return response
            return json_util.dumps('')
        return json_util.dumps('')

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app = create_app()
    app.run(host="0.0.0.0", port=port)
