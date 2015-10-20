from rpc import Client, Server, DynamicObject
from const import USER_DB_FILE
from util import load_config
# needs to be imported for client constructor
# to register itself
from logsink import LogSinkClient

class UserStoreBase(object):
    NAME = "userstore"
    LOG_RPC = True

class UserStoreServer(UserStoreBase, Server):

    def server_init(self):
        self.users = {}
        self.credit = {}
        self.log = LogSinkClient()
        self._init_user_db()

    def _add_user(self, user_dict, credit):
        self.users[user_dict['username']] = user_dict
        self.log.info("Added user: %s with credit %s" % (
            str(user_dict), credit))
        self.set_credit(user_dict['username'], credit)

    def _init_user_db(self, filename=USER_DB_FILE):
        raw_user_list = load_config(filename)['users']
        for raw_user in raw_user_list:
            username, password, credit = raw_user
            self._add_user(
                dict(username=username,
                    password=password),
                credit)

    def get_user(self, username=None):
        return self.users.get(username, {})

    def set_credit(self, username=None, credit=None):
        if username is None or credit is None:
            return False
        self.credit[username] = credit
        self.log.info("Credit for %s set to %s" % (
            username, credit))
        return True

    def increment_credit(self, username=None, increment_by=0):
        if username is None or username not in self.credit:
            return False
        self.credit[username] += increment_by
        self.log.info("Credit for %s incremented %s yielding %s" % (
            username, increment_by, self.credit[username]))
        return self.credit[username]

    def get_credit(self, username=None):
        return self.credit.get(username)

# class User is used by the client
class User(DynamicObject):
    pass

class UserStoreClient(UserStoreBase, Client):

    # runs in the client process
    def get_user(self, username):
        return User(**self.call('get_user', {
            'username': username}))

    def get_credit(self, username):
        return self.call('get_credit', {
            'username': username})

    def increment_credit(self, username, increment_by=0):
        return self.call('increment_credit', {
            'username': username,
            'increment_by': increment_by})
