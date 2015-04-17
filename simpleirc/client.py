from .config import ClientConfig, BotConfig
from .connection import Connection


class Client(object):
    def __init__(self):
        self.config = ClientConfig()
        self.connection = None


class Bot(Client):
    def __init__(self):
        super(Bot, self).__init__()
        self.config = BotConfig(parent=self.config)

