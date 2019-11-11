# return ifnoramtion about user or empty document if no such token in base
def validate_session(users, request):
    if 'session' in request.cookies:
        session = request.cookies['session']
        user = users.find_one({'session': session})
    return user
