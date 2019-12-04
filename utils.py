# return ifnoramtion about user or empty document if no such token in base
def validate_session(users, request):
    if 'session' in request.cookies:
        session = request.cookies['session']
        user = users.find_one({'session': session})
    return user


# adds obj to array field in document with id in collection
def push_to_db(collection, id, field, obj):
    collection.find_one_and_update({'id': id}, {'$push': {field: obj}})
