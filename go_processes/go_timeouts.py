import subprocess
import logging
import re

logging.basicConfig(level="DEBUG")
LOGGER = logging.getLogger(__name__)


class GoTimeouts:

    TIMEOUT_SCRIPT = "grep '{0}' src -R -n"

    REGEX_FILE_PATTERN = "^([a-zA-Z0-9\/]+.go)\:([0-9]+)"

    PATTERNS = [
        "http.ListenAndServe(",
        "http.Get(",
        "http.Post(",
        "http.PostForm(",
        "http.Head("
    ]

    def validate_functions(self, has_error):
        """Run through all .go files to ensure default http lib functions aren't used.

        :param has_error: bool
        :return:
        """
        output = ""

        for pattern in self.PATTERNS:
            out, err_output = self._run_script(pattern)

            if out != '':
                lines = out.split('\n')
                file_pattern = re.compile(self.REGEX_FILE_PATTERN)

                for line in lines:
                    filename_match = re.match(file_pattern, line)

                    if filename_match is None:
                        continue

                    has_error = True
                    output += self._get_error_message_for_line(
                        filename_match, pattern)

        self._log_results(has_error, output)
        return has_error

    def _run_script(self, pattern):
        """Run GoLang script for timeouts.

        :param pattern: string
        :return: (stdout, stderr)
        """
        p = subprocess.Popen(
            [self.TIMEOUT_SCRIPT.format(pattern)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True)

        return p.communicate()

    def _get_error_message_for_line(self, match, pattern):
        return "{0} contains default http function {1} on line {2}\n" \
            .format(match.group(1), pattern, match.group(2))

    def _log_results(self, err, output):
        if err:
            LOGGER.info("GO TIMEOUTS: FAIL")
            LOGGER.info(output)

            hint = "For more info on why this is bad, please read {}"
            hint = hint.format("https://blog.cloudflare.com/the-complete-guide-to-golang-net-http-timeouts/")  # NOQA

            LOGGER.info(hint)
        else:
            LOGGER.info("GO TIMEOUTS: PASS")
