import unittest

from mock import patch, Mock
from ddt import ddt

from go_processes.code_coverage import CodeCoverage


@ddt
class TestCodeCoverage(unittest.TestCase):

    @patch('go_processes.code_coverage.CodeCoverage._run_tests')
    @patch('go_processes.code_coverage.CodeCoverage._log_results')
    def test_get_coverage_fail(self, log_results_patch, run_tests_patch):
        run_tests_patch.return_value = (self._get_test_output_fail(), "Stuff")

        cc = CodeCoverage(self._mock_config())
        err = cc.get_coverage("./f8-jeeves", False)

        self.assertTrue(err)
        log_results_patch\
            .assert_called_with(True, 25.0,
                                '/f8-jeeves has no tests.\n/f8-jeeves/environment has no tests.\n/f8-jeeves/service under coverage threshold at 0.0%\n/f8-jeeves/mypackage FAILED')  # NOQA

    @patch('go_processes.code_coverage.CodeCoverage._run_tests')
    @patch('go_processes.code_coverage.CodeCoverage._log_results')
    def test_get_coverage_pass(self, log_results_patch, run_tests_patch):
        run_tests_patch.return_value = (self._get_test_output_pass(), "Stuff")

        cc = CodeCoverage(self._mock_config())
        err = cc.get_coverage("./f8-jeeves", False)

        self.assertFalse(err)
        log_results_patch.assert_called_with(False, 100.0, "")

    def _mock_config(self):
        mock_coverage = Mock()
        mock_project_type = Mock()
        mock_project_type.project_type = "glide"

        mock_coverage.ignored_packages = []
        mock_coverage.threshold = 90.00

        mock_config = Mock()
        mock_config.code_coverage = mock_coverage
        mock_config.all = mock_project_type
        return mock_config

    def _get_test_output_fail(self):
        return "?   	fresh8.co/f8-jeeves	[no test files]\n?   	fresh8.co/f8-jeeves/environment	[no test files]\nok  	fresh8.co/f8-jeeves/service	0.019s	coverage: 0.0% of statements\nFAIL  	fresh8.co/f8-jeeves/mypackage	0.019s\nok  	fresh8.co/f8-jeeves/service/apierrors	0.022s	coverage: 100.0% of statements"  # NOQA

    def _get_test_output_pass(self):
        return "ok  	fresh8.co/f8-jeeves/service/apierrors" \
               "	0.022s	coverage: 100.0% of statements"


if __name__ == '__main__':
    unittest.main()
