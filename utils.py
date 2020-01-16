import random
import string


# return information about user or empty document if no such token in base
def validate_session(users, request):
    data = request.get_json(force=True)
    if 'session' in data:
        session = data['session']
        user = users.find_one({'session': session})
        return user
    return None


# adds obj to array field in document with id in collection
def push_to_db(collection, id, field, obj):
    collection.find_one_and_update({'id': id},
                                    {'$push': {
                                        field: {
                                            '$each': [obj],
                                            '$position': 0
                                            }
                                        }
                                    })


# return string of random letters and digits
def random_string(string_length=10):
    letters_and_digits = string.ascii_letters + string.digits
    return ''.join(random.choice(letters_and_digits) for i in range(string_length))


# return
def random_id():
    return ''.join(random.choice(string.digits) for i in range(5))
