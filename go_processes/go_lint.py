import subprocess
import logging
import re

logging.basicConfig(level="DEBUG")
LOGGER = logging.getLogger(__name__)


class GoLint:

    LINT_SCRIPT = "golint src/{0}/..."

    REGEX_PACKAGE_PATTERN = "{0}(\/[a-zA-Z0-9\/]+)?.go"
    REGEX_FILE_PATTERN = "\/[a-zA-Z0-9]+.go"

    def __init__(self, config):
        self.config = config
        
    def go_lint(self, package, has_error):
        """Run golint on all packages.

        Ignores packages listed under config.golint.ignored_packages

        :param package: string
        :param has_error: bool
        :return: bool
        """
        output = ""

        out, error_output = self._run_script(package)

        package_pattern = re.compile(self.REGEX_PACKAGE_PATTERN.format(package))
        file_pattern = re.compile(self.REGEX_FILE_PATTERN)

        lines = out.split('\n')
        for line in lines:
            package = re.search(package_pattern, line)

            if package is None:
                continue

            package = package.group(0)
            package = re.sub(file_pattern, '', package)

            if package in self.config.golint.ignored_packages:
                continue

            has_error = True
            output += "{0}\n".format(line)

        self._log_results(has_error, out)

        return has_error

    def _run_script(self, package):
        """Run GoLang script for linting.

        :param package: string
        :return: (stdout, stderr)
        """
        p = subprocess.Popen(
            [self.LINT_SCRIPT.format(package)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True)

        return p.communicate()

    def _log_results(self, has_error, out):
        """Log result from linting.

        :param has_error: bool
        :param out: string
        :return:
        """
        LOGGER.info("GOLINT: FAIL") if has_error else LOGGER.info("GOLINT: PASS")
        if has_error:
            LOGGER.info(out)