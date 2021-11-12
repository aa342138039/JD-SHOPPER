import os
import configparser

class Config(object):
    def __init__(self, config_file='config.ini'):
        self.rootPath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._path = self.rootPath + "/Config/" + config_file
        if not os.path.exists(self._path):
            raise FileNotFoundError("No such file: config.ini")
        self._config = configparser.ConfigParser()
        self._config.read(self._path, encoding='utf-8-sig')
        self._configRaw = configparser.RawConfigParser()
        self._configRaw.read(self._path, encoding='utf-8-sig')

    def settings(self, section, name):
        return eval(self._config.get(section, name))

    def raw(self, section, name):
        return self._configRaw.get(section, name)

    def path(self):
        return self.rootPath


config = Config()
