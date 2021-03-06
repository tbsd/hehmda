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
import hashlib


import cgi

from flask import Flask, jsonify, render_template, send_from_directory, request, make_response, redirect, url_for
from flask_cors import CORS, cross_origin
from pymongo import MongoClient
from bson import json_util
from datetime import datetime
from utils import validate_session, push_to_db, random_string, random_id

# Cookies
from http import cookies


def create_app(config=None):
    app = Flask(__name__)
    CORS(app, support_credentials=True, resources={r"/*": {"origins": "*"}}, send_wildcard=True)
    app.config['CORS_HEADERS'] = 'Content-Type'
    # See http://flask.pocoo.org/docs/latest/config/
    app.config.update(dict(DEBUG=True))
    app.config.update(config or {})

    # Setup cors headers to allow all domains
    # https://flask-cors.readthedocs.io/en/latest/
    #  CORS(app, support_credentials=True)

    # Definition of the routes. Put them into their own file. See also
    # Flask Blueprints: http://flask.pocoo.org/docs/latest/blueprints

    # MongoDB client
    # global
    client = pymongo.MongoClient("mongodb+srv://testing-repo:testing-repo@testing-repo-4xvfr.mongodb.net/admin?retryWrites=true&w=majority")
    # local
    # client = MongoClient('localhost', 27017)
    db = client['db']
    users = db['users']
    chats = db['chats']

    
    # 404 error handler
    @app.errorhandler(404)
    def not_found(error):
        return json_util.dumps({'code': 404, 'status_msg': 'Не найдено.'})

    # main page
    @app.route("/")
    @cross_origin()
    def hello_world():
        return render_template('index.html')

    # used for loading js to page
    @app.route('/js/<path:path>')
    @cross_origin()
    def get_js(path):
        return send_from_directory('js', path)

    # get user contacts
    @app.route('/api/v1/users/contacts', methods=['POST'])
    @cross_origin()
    def get_contacts():
        user = validate_session(users, request)
        if user:
            info = users.find_one({'id': user['id']},
                                  {'_id': 0, 'id': 1, 'contacts': 1})
            return json_util.dumps(info)
        return json_util.dumps({'code': 401, 'status_msg': 'Вы не вы не авторизованы.'})

    # get all chats
    @app.route('/api/v1/users/chats', methods=['POST'])
    @cross_origin()
    def get_all_chats():
        user = validate_session(users, request)
        if user:
            chats_id = user['chat_list']
            info = list(chats.find({'id': {'$in': chats_id}}, {'_id': 0}))
            res = [dict for x in chats_id for dict in info if dict['id'] == x ]
            return json_util.dumps(res)
        return json_util.dumps({'code': 401, 'status_msg': 'Вы не вы не авторизованы.'})

    # adds contact to current user by given login
    @app.route('/api/v1/users/addcontactbylogin', methods=['POST'])
    @cross_origin()
    def add_contact_by_login():
        user = validate_session(users, request)
        data = request.get_json(force=True)
        new_contact = users.find_one({'login': data['login']},
                                     {'_id': 0, 'id': 1, 'nickname': 1, 'login': 1})
        new_contact_json = json_util.dumps(new_contact)
        if (new_contact not in user['contacts']):
            if new_contact:
                push_to_db(users, user['id'], 'contacts', new_contact)
                return new_contact_json
            else:
                return json_util.dumps({'code': 404,
                    'status_msg': 'Такого пользователя не существует.'})
        return json_util.dumps({'code': 409, 'status_msg': 'Этот контакт уже есть в списке пользователя.'})

    # adds contact to current user by given id
    @app.route('/api/v1/users/addcontact', methods=['POST'])
    @cross_origin()
    def add_contact():
        user = validate_session(users, request)
        data = request.get_json(force=True)
        new_contact = users.find_one({'id': data['id']},
                {'_id': 0, 'id': 1, 'nickname': 1})
        new_contact_json = json_util.dumps(new_contact)
        if (new_contact not in user['contacts']):
            if new_contact:
                push_to_db(users, user['id'], 'contacts', new_contact)
                return new_contact_json
            else:
                return json_util.dumps({'code': 404,
                    'status_msg': 'Такого пользователя не существует.'})
        return json_util.dumps({'code': 409, 'status_msg': 'Этот контакт уже есть в списке пользователя.'})

    # add user to chat
    @app.route('/api/v1/chats/addtochat', methods=['POST'])
    @cross_origin()
    def add_to_chat():
        user = validate_session(users, request)
        data = request.get_json(force=True)
        chat_id = data['chat_id']
        new_user_id = data['new_user_id']
        # if new chat created
        if (user and chat_id == ''):
            chat_id = random_string(30)
            chat = chats.find_one({'id': chat_id},
                                  {'_id': 0, 'id': 1, 'users': 1})
            while chat:
                chat_id = random_string(30)
                chat = chats.find_one({'id': chat_id},
                                      {'_id': 0, 'id': 1, 'users': 1})
            chats.insert_one({'id': chat_id,
                              'users': [user['id']],
                              'messages': []})
            push_to_db(users, user['id'], 'chat_list', chat_id)
            user['chat_list'].append(chat_id)
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
    @cross_origin()
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
            push_to_db(chats, chat_id, 'messages', message, False)
            return json_util.dumps(message)
        return json_util.dumps({'code': 401, 'status_msg': 'Вы не состоите в данном чате.'})

    # get only new messages
    @app.route('/api/v1/chats/getnewmessages', methods=['POST'])
    @cross_origin()
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
        return json_util.dumps({'code': 401, 'status_msg': 'Вы не состоите в данном чате.'})

    # get members of the chat
    @app.route('/api/v1/chats/getusers', methods=['POST'])
    @cross_origin()
    def get_users():
        user = validate_session(users, request)
        data = request.get_json(force=True)
        chat_id = data['chat_id']
        # only if user is member of this chat
        if (user and chat_id in user['chat_list']):
            chat = chats.find_one({'id': chat_id},
                                  {'_id': 0, 'id': 1, 'users': 1})
            return json_util.dumps(chat)
        return json_util.dumps({'code': 401, 'status_msg': 'Вы не состоите в данном чате.'})

    # Login and password for registration

    @app.route('/api/v1/users/authorization', methods=['POST'])
    @cross_origin()
    def authorization():
        # Считывание логина и пароля
        data = request.get_json(force=True)
        login = data['login']
        password = data['password']
        # Проверка, есть ли в базе данных эта личнасть
        password_hash = hashlib.md5(password.strip().encode('utf-8')).hexdigest()
        if users.find({"login": login, "password_hash": password_hash}).count() == 1:
            token = random_string()
            response = make_response()
            user = users.find_one({"login": login, "password_hash": password_hash})
            users.find_one_and_update({'id': user['id']}, {'$set': {'session': token}})
            user = users.find_one({"login": login, "password_hash": password_hash})
            response.set_cookie('session', user['session'])
            return json_util.dumps({'session': user['session']})
        else:
            return json_util.dumps({'code': 401, 'status_msg': 'Неверный логин или пароль.'})

    @app.route('/api/v1/users/registration', methods=['POST'])
    @cross_origin()
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
                password_hash = hashlib.md5(new_password.strip().encode('utf-8'))
                users.insert_one({"id": new_id, "login": new_login,
                                  "password_hash": password_hash.hexdigest(),
                                  "nickname": new_nickname,
                                  "chat_list": [],
                                  "contacts": [], "session": token})
                response.set_cookie('session', token)
                return json_util.dumps({'session': token})
            return json_util.dumps({'code': 400, 'status_msg': 'Пароли не совпадают.'})
        return json_util.dumps({'code': 400, 'status_msg': 'Такой логин уже занят.'})

    # get personal user inforamtion
    @app.route('/api/v1/users/personaldata', methods=['POST'])
    @cross_origin()
    def get_personal_data():
        user = validate_session(users, request)
        if user:
            info = users.find_one({'id': user['id']},
                                  {'_id': 0, 'id': 1, 'login': 1, 
                                   'nickname': 1, 'chat_list': 1, 
                                   'contacts': 1, 'session': 1})
            return json_util.dumps(info)
        return json_util.dumps({'code': 401, 'status_msg': 'Вы не вы не авторизованы.'})

    # get public user inforamtion
    @app.route('/api/v1/users/publicdata', methods=['POST'])
    @cross_origin()
    def get_public_data():
        data = request.get_json(force=True)
        other_id = data['id']
        info = users.find_one({'id': other_id},
                              {'_id': 0, 'id': 1, 'nickname': 1})
        if (len(info) != 0):
            return json_util.dumps(info)
        else: 
            return json_util.dumps({'code': 404,
                'status_msg': 'Пользователя с таким id не существует.'})

    return app

    # need for cookies to work propertly in case of reactjs frontend
    @app.after_request
    def middleware_for_response(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app = create_app()
    app.run(host="0.0.0.0", port=port)
