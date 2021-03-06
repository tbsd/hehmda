#!/usr/bin/env python3

# Deletes everything from local db  and fills it with testing records
#  import os
import pymongo

from pymongo import MongoClient

client = MongoClient('localhost', 27017)
db = client['db']
users = db['users']
chats = db['chats']

client.drop_database('db')
users.insert_many([
    {
        'id': '1',
        'login': 'vasyan228',
        'password_hash': '1234',
        'nickname': 'xXxNagibatorxXx',
        'chat_list': ['1', '2'],
        'contacts': [{'2': 'kolyan322'}, {'3': 'johndoe'}],
        'session': '4321'
        },
    {
        'id': '2',
        'login': 'kolyan322',
        'password_hash': '1234',
        'nickname': 'pro100kolya',
        'chat_list': ['1'],
        'contacts': [{'1': 'vasyan228'}],
        'session': 'ohlol'
        },
    {
        'id': '3',
        'login': 'johndoe',
        'password_hash': 'letmein',
        'nickname': 'username',
        'chat_list': ['1', '2'],
        'contacts': [{'1': 'vasyan228'}],
        'session': 'randomtoken'
        }
    ])

chats.insert_many([
    # chant with 3 users
    {
        'id': '1',
        'users': ['1', '2', '3'],
        'messages': [
            {
                'id': '1',
                'author': '1',
                'time': '1575760830000',
                'content': 'what\'s up gamers'
                },
            {
                'id': '2',
                'author': '2',
                'time': '1575770830000',
                'content': 'hello there'
                },
            {
                'id': '3',
                'author': '3',
                'time': '1575780830000',
                'content': 'sup guys'
                }
            ]
        },
    {
        'id': '2',
        'users': ['1', '3'],
        'messages': [
            {
                'id': '4',
                'author': '1',
                'time': '1575860830000',
                'content': 'How do you do?'
                },
            {
                'id': '5',
                'author': '3',
                'time': '1575860930000',
                'content': 'Thank you, i\'m fine'
                },
            {
                'id': '6',
                'author': '3',
                'time': '1575960830000',
                'content': 'Also, London is a capital of great Britan'
                },
            {
                'id': '7',
                'author': '1',
                'time': '1575980830000',
                'content': 'My English is very well'
                }
            ]
        }
    ])
