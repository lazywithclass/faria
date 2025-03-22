import configparser
import os


def project_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def get_conf(section, option):
    config = configparser.ConfigParser()
    config_path = os.path.join(project_root(), 'config.ini')
    config.read(config_path)
    if section == 'Paths':
        return os.path.join(project_root(), config.get(section, option))
    return config.get(section, option)