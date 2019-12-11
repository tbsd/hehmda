import random
import string


# return ifnoramtion about user or empty document if no such token in base
def validate_session(users, request):
    if 'session' in request.cookies:
        session = request.cookies['session']
        user = users.find_one({'session': session})
    return user


# adds obj to array field in document with id in collection
def push_to_db(collection, ide, field, obj):
    collection.find_one_and_update({'id': ide}, {'$push': {field: obj}})


# return string of random letters and digits
def random_string(string_length=20):
    letters_and_digits = string.ascii_letters + string.digits
    return ''.join(random.choice(letters_and_digits) for i in range(string_length))
