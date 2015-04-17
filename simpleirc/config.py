import abc
from future.utils import iteritems
from builtins import str
import json
import logging
import os


logger = logging.getLogger('simpleirc.config')


class Config(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, parent=None, **kwargs):
        self._parent = parent
        self._sections = kwargs

    def __getattr__(self, item, default=None):
        if item.startswith('_'):
            return self.__dict__.get(item, default)
        if item not in self._sections and self._parent and item in self._parent:
            return getattr(self._parent, item)
        return self._sections[item]

    def __json__(self, recursive=True):
        ret = {}
        if recursive and self._parent:
            ret = self._parent.__json__(recursive)
        for (k, v) in iteritems(self._sections):
            ret[k] = v.__json__()
        return ret

    def __setattr__(self, key, value):
        if key.startswith('_'):
            self.__dict__[key] = value
            return
        elif key not in self._sections:
            raise KeyError
        self._sections[key] = value

    def __str__(self):
        return json.dumps(self.__json__())


    def add_section(self, section, **kwargs):
        if section in self._sections:
            raise KeyError('config section %s already exists' % (section, ))
        self._sections.setdefault(section, ConfigSection(section, **kwargs))


class ConfigSection(Config):
    __metaclass__ = abc.ABCMeta

    def __init__(self, name, **kwargs):
        self._name = name
        super(ConfigSection, self).__init__(**kwargs)

    def __setattr__(self, key, value):
        if not key.startswith('_'):
            if isinstance(value, ConfigProperty):
                self._sections[key] = value
                return
        super(ConfigSection, self).__setattr__(key, value)


class ConfigProperty(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, name, ptype, value):
        self.name = name
        self.type = ptype
        self._value = None
        self.value = value

    def __json__(self):
        return self.value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = self.type(value)


class ConfigPropertyBool(ConfigProperty):
    def __init__(self, name, value):
        super(ConfigPropertyBool, self).__init__(name, bool, value)


class ConfigPropertyFloat(ConfigProperty):
    def __init__(self, name, value):
        super(ConfigPropertyFloat, self).__init__(name, float, value)


class ConfigPropertyInteger(ConfigProperty):
    def __init__(self, name, value):
        super(ConfigPropertyInteger, self).__init__(name, int, value)


class ConfigPropertyString(ConfigProperty):
    def __init__(self, name, value):
        super(ConfigPropertyString, self).__init__(name, str, value)


class ConfigFileJson(Config):
    __metaclass__ = abc.ABCMeta

    def __init__(self, filename, path='~/.simpleirc', **kwargs):
        self._path = path
        self._abs_path = os.path.abspath(os.path.expanduser(self._path))
        self._filename = filename
        self._full_path = os.path.join(self._path, self._filename)
        self._abs_full_path = os.path.join(self._abs_path, self._filename)
        self._loaded = False
        super(ConfigFileJson, self).__init__(**kwargs)
        if not os.path.isdir(self._abs_path):
            logger.info('creating configuration directory %s', self._abs_path)
            os.makedirs(self._abs_path, 0o700)
        if not os.path.isfile(self._abs_full_path):
            self._create_file()
        else:
            self.load()

    def load(self, recursive=False):
        logger.info('loading config file %s', self._filename)
        self._sections = {}
        if recursive and self._parent:
            self._parent.load(recursive)
        with open(self._abs_full_path, 'r') as fp:
            sections = json.load(fp)
        self._load_section(self, **sections)
        self._loaded = True

    def write(self, recursive=False):
        logger.info('writing settings out to %s', self._filename)
        with open(self._abs_full_path, 'w') as fp:
            json.dump(self.__json__(False), fp, indent=4)
        if recursive and self._parent:
            self._parent.write()

    def _create_file(self):
        logger.info('creating log file %s and loading initial settings', self._filename)
        self._load_initial_data()
        self.write()

    @abc.abstractmethod
    def _load_initial_data(self):
        raise NotImplementedError

    def _load_section(self, obj, **sections):
        for (k, v) in iteritems(sections):
            if isinstance(v, str):
                setattr(obj, k, ConfigPropertyString(k, v))
            elif type(v) == int:
                setattr(obj, k, ConfigPropertyInteger(k, v))
            elif type(v) == float:
                setattr(obj, k, ConfigPropertyFloat(k, v))
            elif type(v) == bool:
                setattr(obj, k, ConfigPropertyBool(k, v))
            elif type(v) == dict:
                obj.add_section(k)
                self._load_section(getattr(obj, k), **v)
            else:
                logger.warning('failed to parse unknown type: %s type(%s)', k, v)


class ClientConfig(ConfigFileJson):
    def __init__(self, filename='client.json', **kwargs):
        super(ClientConfig, self).__init__(filename, **kwargs)

    def _load_initial_data(self):
        self.add_section('servers')
        self.servers.add_section('freenode')
        self.servers.freenode.host = ConfigPropertyString('host', 'irc.freenode.net')
        self.servers.freenode.nick = ConfigPropertyString('nick', 'simpleirc')
        self.servers.freenode.port = ConfigPropertyInteger('port', 6667)


class BotConfig(ConfigFileJson):
    def __init__(self, filename='bot.json', **kwargs):
        super(BotConfig, self).__init__(filename, **kwargs)

    def _load_initial_data(self):
        self.add_section('core')
        self.core.add_section('plugins')
        self.core.plugins.add_section('bot')
        self.core.plugins.bot.auto_load = ConfigPropertyBool('auto_load', True)

