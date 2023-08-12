import logging.config

import yaml


def configure_logger(config_path):
    with open(config_path, "r") as stream:
        config = yaml.safe_load(stream)
        logging.config.dictConfig(config)
