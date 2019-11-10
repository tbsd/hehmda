def is_valid_session(users, request):
    if 'id' in request.args:
        user_id = request.args['id']
        if 'session' in request.args:
            session = request.args['session']
            actual_session = users.find_one({'id': user_id},
                                            {'session': 1})['session']
            if session == actual_session:
                return True
    return False
