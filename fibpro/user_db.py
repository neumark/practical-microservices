from const import USER_DB_FILE
from util import load_config, log

USERS = {}

class User(object):
    def __init__(self, username, password, credit):
        self.username = username
        self.password = password
        self.credit = credit

def add_user(user_obj):
    USERS[user_obj.username] = user_obj
    log.info("Added user: %s" % str(user_obj.__dict__))

def init_user_db(filename=USER_DB_FILE):
    raw_user_list = load_config(filename)['users']
    for raw_user in raw_user_list:
        add_user(User(*raw_user))

def get_user(username):
    return USERS.get(username)
