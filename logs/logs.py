import logging.config

import yaml

from src.settings import Settings

settings = Settings()


def configure_logger(name):
    config_path = settings.CONFIG_LOGGER_PATH
    with open(config_path, "r") as stream:
        config = yaml.safe_load(stream)
    logging.config.dictConfig(config)
    return logging.getLogger(name)
