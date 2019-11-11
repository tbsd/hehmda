def is_valid_session(users, request):
    if 'id' in request.cookies:
        user_id = request.cookies['id']
        if 'session' in request.cookies:
            session = request.cookies['session']
            actual_session = users.find_one({'id': user_id},
                                            {'session': 1})['session']
            if session == actual_session:
                return True
    return False
