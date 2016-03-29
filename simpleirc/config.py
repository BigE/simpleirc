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
        if self._parent and item in self._parent.config:
            return self.__update__(self._parent.config, self.config)[item]
        return self.config[item]

    def __update__(self, orig_config, new_config):
        for k,v in iteritems(new_config):
            if k in orig_config and isinstance(orig_config[k], dict) and isinstance(new_config[k], dict):
                self.__update__(orig_config[k], new_config[k])
            else:
                orig_config[k] = new_config[k]
        return orig_config


class ConfigStructure(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self._structure = {}


class ConfigSection(ConfigStructure):
    __metaclass__ = abc.ABCMeta

    def __getattr__(self, key):
        if key.startswith('_'):
            return self.__dict__[key]
        return self._structure[key]

    def __setattr__(self, key, value):
        if key.startswith('_'):
            self.__dict__[key] = value
        else:
            self._structure[key] = value

    def attributes(self):
        return self._structure


class ConfigContainer(ConfigSection):
    __metaclass__ = abc.ABCMeta

    @classmethod
    @abc.abstractclassmethod
    def container(cls):
        raise NotImplementedError

    def __init__(self, **kwargs):
        super().__init__()
        self._structure = kwargs


class ServerSection(ConfigSection):
    def __init__(self):
        super().__init__()
        self.auto = ConfigPropertyBoolean(default=False)
        self.host = ConfigPropertyString(required=True)
        self.nick = ConfigPropertyString(required=True)
        self.password = ConfigPropertyString()
        self.port = ConfigPropertyInteger(required=True, default=6667)
        self.realname = ConfigPropertyString()
        self.username = ConfigPropertyString()


class ServerContainer(ConfigContainer):
    @classmethod
    def container(cls):
        return ServerSection


class ConfigProperty(object):
    def __init__(self, property_type, **kwargs):
        self.type = property_type
        self.default = kwargs.get('default', None)
        self.required = kwargs.get('required', False)

    def valid(self, value):
        if value is None and self.required and self.default:
            return self.default
        elif value is None and self.required:
            raise ValueError
        elif type(value) is not self.type and value is not None:
            raise TypeError
        return True


class ConfigPropertyBoolean(ConfigProperty):
    def __init__(self, **kwargs):
        super().__init__(bool, **kwargs)


class ConfigPropertyInteger(ConfigProperty):
    def __init__(self, **kwargs):
        super().__init__(int, **kwargs)


class ConfigPropertyString(ConfigProperty):
    def __init__(self, **kwargs):
        super().__init__(str, **kwargs)


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

    def validate(self, config):
        for section in config:
            name = section[0].upper() + section[1:] + 'Container'
            cls = globals()[name].container()
            logger.debug('validating section %s', section)
            for sub_section in config[section]:
                attributes = cls().attributes()
                sub_section_valid = True
                logger.debug('validating section %s.%s', section, sub_section)
                for item in attributes:
                    value = None
                    if item in config[section][sub_section]:
                        value = config[section][sub_section][item]
                    elif self._parent and section in self._parent.config:
                        parent = self._parent.config[section]
                        if sub_section in parent and item in parent[sub_section]:
                            # already passed validation
                            continue
                    try:
                        valid = attributes[item].valid(value)
                    except TypeError:
                        sub_section_valid = False
                        logger.error('%s.%s.%s is wrong type of %s expecting %s',
                                     section, sub_section, item, type(value), attributes[item].type)
                    except ValueError:
                        sub_section_valid = False
                        logger.critical('%s.%s.%s is a required value and must be defined', section, sub_section, item)
                    else:
                        if valid is not True:
                            config[section][sub_section][item] = valid
                if not sub_section_valid:
                    logger.error('%s.%s is not valid and being removed from the config', section, sub_section)
                    del config[section][sub_section]
        return config

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
            config = json.load(fp)
            self.config = self.validate(config)
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
                    'nick': 'simpleirc',
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
                    'auto': True
                }
            }
        }

