import socket


class Connection(object):
    family = socket.AF_INET

    def __init__(self, ipv6=False):
        self.connected = False
        if ipv6:
            self.family = socket.AF_INET6
        self.nickname = None
        self.port = 6667
        self.real_nickname = None
        self.server = None
        self.socket = None

    def connect(self, server, nickname, port=6667, username=None, password=None,
                real_name=None):
        self.server = server
        self.port = port
        self.socket = socket.socket(self.family, socket.SOCK_STREAM)
        self.socket.connect((server, port))
        if password:
            self.password(password)
        if username is None:
            username = nickname
        self.nick(nickname)
        self.user(username, real_name if real_name else username)

    def nick(self, nickname):
        self.real_nickname = nickname

    def password(self, password):
        pass

    def user(self, username, real_name=None):
        pass