import subprocess
import re
import logging

logging.basicConfig(level="DEBUG")
LOGGER = logging.getLogger(__name__)


class GoVet:

    VET_SCRIPT = "go vet {0}/..."

    REGEX_PACKAGE = "{0}(\/[a-zA-Z0-9\/]+)?.go"
    REGEX_FILE_PATTERN = "\/[a-zA-Z0-9]+.go"

    def __init__(self, config):
        self.config = config
        
    def go_vet(self, package, has_error):
        output = ""

        out, err_output = self._run_script(package)

        package_pattern = re.compile(self.REGEX_PACKAGE.format(package))
        file_pattern = re.compile(self.REGEX_FILE_PATTERN)

        lines = err_output.split('\n')
        for line in lines:
            package = re.search(package_pattern, line)

            if package is None:
                continue

            package = package.group(0)
            package = re.sub(file_pattern, '', package)

            if package in self.config.go_vet.ignored_packages:
                continue

            has_error = True
            output += line + "\n"

        self._log_results(output, has_error)

        return has_error

    def _run_script(self, package):
        """Run go vet script.

        :param package: string
        :return: (stdout, stderr)
        """
        p = subprocess.Popen(
            [self.VET_SCRIPT.format(package)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True)

        return p.communicate()

    def _log_results(self, output, err):
        LOGGER.info("GO VET: FAIL") if err else LOGGER.info("GO VET: PASS")
        if err:
            LOGGER.info(output)

