import subprocess
import logging
import re
import os


logging.basicConfig(level="DEBUG")
LOGGER = logging.getLogger(__name__)


class CodeCoverage:

    ALLIDENTIFIER = "all"
    NOTESTFILES_IDENTIFIER = "[no test files]"

    REGEX_PATTERN_PACKAGE = "{0}((\/[a-zA-Z0-9\/-]+)?)"
    REGEX_PATTERN_COVERAGE = "[0-9]{1,3}.[0-9]%"
    REGEX_PATTERN_FAIL = "^FAIL"

    def __init__(self, config):
        self.config = config
        
    def get_coverage(self, base_package, has_error):
        """Run go test -cover, parses the output line by line.

        Ignores packages listed under config.code_coverage.ignored_packages
        Threshold taken from config.code_coverage.threshold
            must be of type float (e.g 50.0)

        :param base_package: string
        :param has_error: bool
        :return: bool
        """
        output = ""
        out, err = self._run_tests(base_package)

        if err is not None and not "\n":
            LOGGER.error(err)
            has_error = True

        package_pattern, coverage_pattern = self._get_regex_patterns(base_package)

        coverage_count = 0
        coverage_cum = 0.0

        lines = out.split('\n')
        for line in lines:

            package = re.search(package_pattern, line)

            if package is None:
                continue
            package = package.group()

            if re.match(self.REGEX_PATTERN_FAIL, line):
                output += "{0} FAILED".format(package)
                has_error = True
                continue

            if package in self.config.code_coverage.ignored_packages:
                continue

            coverage = re.search(coverage_pattern, line)

            if coverage:
                # Allow to be passed through as none
                # See `elif "[no test files]"`
                coverage = coverage.group(0)

                cv = float(coverage[:-1])

                if cv <= self.config.code_coverage.threshold:
                    has_error = True
                    output += "{0} under coverage threshold at {1}\n".format(
                        package, coverage)

                coverage_cum += cv

            elif self.NOTESTFILES_IDENTIFIER in line:
                has_error = True
                output += "{0} has no tests.\n".format(package)

            coverage_count += 1

        if coverage_count == 0:
            LOGGER.info("No packages available for coverage calculation")
            return

        total_coverage = round(coverage_cum / coverage_count, 2)

        self._log_results(has_error, total_coverage, output)

        return has_error

    def _get_regex_patterns(self, base_package):
        """Return compiled regex patterns.

        Sets package to the cwd, if base_package is set to
        the ALLIDENTIFIER.

        Regex objects are then built and returned.

        :param base_package: string
        :return: (re, re)
        """
        if base_package == self.ALLIDENTIFIER:
            package = os.getcwd().rsplit('/', 1)[-1]
        else:
            # Remove starting `.` if present as it breaks the regex.
            package = base_package[1:] \
                if base_package.startswith('./') else base_package
        LOGGER.debug("Package in regex: {0}".format(package))
        package_pattern = re.compile(self.REGEX_PATTERN_PACKAGE.format(package))
        coverage_pattern = re.compile(self.REGEX_PATTERN_COVERAGE)

        return package_pattern, coverage_pattern

    def _run_tests(self, package):
        """Run the GoLang tests.

        A choice is made between which script to run,
        depending on whether or not the `ALLIDENTIFIER`
        is present. The `vendor` directory is automatically
        excluded.

        The script is then ran, and the results are
        returned.

        :param package: string
        :return: (stdout, stderr)
        """

        test_script = "go test `go list ./... | grep -v vendor` -cover".format(package) \
            if package == self.ALLIDENTIFIER else "go test {0}/... -cover".format(package)
        LOGGER.debug("Test script: {0}".format(test_script))

        p = subprocess.Popen(
            [test_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True)

        return p.communicate()

    def _log_results(self, err, total_coverage, output):
        """Log the coverage results.

        :param err: bool
        :param total_coverage: float
        :param output: string
        :return:
        """
        LOGGER.info("CODE COVERAGE: FAIL") if err else LOGGER.info("CODE COVERAGE: PASS")

        LOGGER.info("Current coverage: {0}%".format(str(total_coverage)))
        LOGGER.info("Coverage threshold: {0}%"
                    .format(str(self.config.code_coverage.threshold)))

        if err:
            LOGGER.info(output)

