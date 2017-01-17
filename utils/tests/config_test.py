import os
import unittest

from mock import patch, Mock
from ddt import ddt, data, unpack

from utils.config import Config, get_config


@ddt
class TestConfig(unittest.TestCase):

    def test_get_config(self):
        config = get_config(
            os.path.abspath("utils/tests/test_config.yaml"))
        self.assertEqual(config, self._get_valid_config())

    @patch('utils.config.Config.__init__', Mock(return_value=None))
    def test_validate_config_returns_valid(self):
        self.assertTrue(Config().validate_config(self._get_valid_config()))

    @data({"test_config": {}},
          {"test_config": {"code_coverage": {},
                           "golint": {},
                           "go_vet": {},
                           "all": {}}},
          {"test_config": {"code_coverage": {},
                           "golint": {},
                           "go_vet": {},
                           "all": {"packages": [],
                                   "project_type": "",
                                   "ignored_commands": []}}},
          {"test_config": {"code_coverage": {},
                           "golint": {},
                           "go_vet": {"ignored_packages": []},
                           "all": {"packages": [],
                                   "project_type": "",
                                   "ignored_commands": []}}},
          {"test_config": {"code_coverage": {},
                           "golint": {"ignored_packages": []},
                           "go_vet": {"ignored_packages": []},
                           "all": {"packages": [],
                                   "project_type": "",
                                   "ignored_commands": []}}},
          )
    @unpack
    @patch('utils.config.Config.__init__', Mock(return_value=None))
    def test_validation_config_returns_invalid(self, test_config):
        self.assertFalse(Config().validate_config(test_config))

    @staticmethod
    def _get_valid_config():
        return {
            'code_coverage':
                {
                    'ignored_packages':
                        ['your_cool_package/neat_inner_package'],
                    'threshold': 80.0
                },
            'golint': {'ignored_packages': []},
            'go_vet': {'ignored_packages': []},
            'all': {
                'packages': ['your_cool_package'],
                'project_type': 'gb', 'ignored_commands': []
                   },
        }
