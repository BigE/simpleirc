import abc
from future.utils import iteritems
import json
import logging
import os


logger = logging.getLogger('simpleirc.config')


class Config(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, parent=None, **kwargs):
        self._parent = parent
        self.config = kwargs

    def __getitem__(self, item):
        if item.startswith('_'):
            return self.__dict__[item]
        elif self._parent and item in self._parent.config:
            return self.__update__(self._parent.config, self.config)[item]
        return self.config[item]

    def __update__(self, orig_config, new_config):
        for k,v in iteritems(new_config):
            if k in orig_config and isinstance(orig_config[k], dict) and isinstance(new_config[k], dict):
                self.__update__(orig_config[k], new_config[k])
            else:
                orig_config[k] = new_config[k]
        return orig_config


class ConfigFile(Config):
    __metaclass__ = abc.ABCMeta

    def __init__(self, filename, path='~/.simpleirc', **kwargs):
        self._path = path
        self._abs_path = os.path.abspath(os.path.expanduser(self._path))
        self._filename = filename
        self._full_path = os.path.join(self._path, self._filename)
        self._abs_full_path = os.path.join(self._abs_path, self._filename)
        self._loaded = False
        super(ConfigFile, self).__init__(**kwargs)
        if not os.path.isdir(self._abs_path):
            logger.info('creating configuration directory %s', self._abs_path)
            os.makedirs(self._abs_path, 0o700)
        if not os.path.isfile(self._abs_full_path):
            self._create_file()
        else:
            self.load()

    @abc.abstractmethod
    def load(self):
        raise NotImplementedError

    @abc.abstractmethod
    def write(self):
        raise NotImplementedError

    def _create_file(self):
        logger.info('creating log file %s and loading initial settings', self._filename)
        self._load_initial_data()
        self.write()

    @abc.abstractmethod
    def _load_initial_data(self):
        raise NotImplementedError


class ConfigFileJson(ConfigFile):
    __metaclass__ = abc.ABCMeta

    def load(self):
        logger.info('loading config file %s', self._filename)
        self.config = {}
        with open(self._abs_full_path, 'r') as fp:
            self.config = json.load(fp)
        self._loaded = True

    def write(self):
        logger.info('writing settings out to %s', self._filename)
        with open(self._abs_full_path, 'w') as fp:
            json.dump(self.config, fp, indent=4)

    @abc.abstractmethod
    def _load_initial_data(self):
        raise NotImplementedError


class ClientConfig(ConfigFileJson):
    def __init__(self, filename='client.json', **kwargs):
        super(ClientConfig, self).__init__(filename, **kwargs)

    def _load_initial_data(self):
        self.config = {
            'server': {
                'freenode': {
                    'auto': False,
                    'host': 'irc.freenode.net',
                    'nick': None,
                    'password': None,
                    'port': 6667,
                    'username': None,
                    'realname': None
                }
            }
        }


class BotConfig(ConfigFileJson):
    def __init__(self, filename='bot.json', **kwargs):
        super(BotConfig, self).__init__(filename, **kwargs)

    def _load_initial_data(self):
        self.config = {
            'server': {
                'freenode': {
                    'auto': True,
                    'nick': 'simpleirc'
                }
            }
        }

