from unittest.mock import mock_open, patch

import pytest


@pytest.fixture(autouse=True)
def mock_logging_config():
    with patch("builtins.open", mock_open()):
        with patch("yaml.safe_load", return_value={}):
            with patch("logging.config.dictConfig"):
                yield
