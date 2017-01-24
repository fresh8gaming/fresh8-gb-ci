#!/usr/bin/env python
"""The main executable file, wraps a variety of cli tools to pass/fail builds.

Iterates through all packages listed in config.yaml and runs the associated
tools. Currently hardcoded to include all of them. Each tool will run as a
subprocess with the output piped into python. Regex is then used to determine
the necessary information.

Tracks whether an error has occured using a global variable `has_error`.

GOPATH is currently hardcoded, making it configurable is on the roadmap.

We're currently using the python3 style print, however a case may be made
to move it back to python2 style.
"""

from __future__ import print_function

import sys
import logging

from utils.config import get_config
from go_processes.code_coverage import CodeCoverage
from go_processes.go_lint import GoLint
from go_processes.go_timeouts import GoTimeouts
from go_processes.go_vet import GoVet


___author___ = "Jim Hill (github.com/jimah)"
___credits___ = ["Jim Hill (github.com/jimah)",
                 "Lee Archer (github.com/lbn)",
                 "Dom Udall (github.com/domudall)",
                 "Chris Mallon (github.com/JaegerBane)"]
___license___ = "MIT"
___version___ = "1.0"
___maintainer___ = "Jim Hill"
___email___ = "jimi2204@googlemail.com"
___status___ = "Development"

CONFIG = get_config()

logging.basicConfig(level="DEBUG")
logger = logging.getLogger(__name__)


def error(*objs):
    """

    Outputs to stderr

    """
    print(*objs, file=sys.stderr)


def code_coverage(package):
    """Perform code coverage checks.

    Utilising the CodeCoverage class, this will
    perform the coverage checks required.

    :param package: string
    :return:
    """
    global has_error
    has_error = CodeCoverage(CONFIG).get_coverage(package, has_error)


def go_lint(package):
    """

    Runs golint on all packages
    Ignores packages listed under config.golint.ignored_packages

    """
    global has_error
    has_error = GoLint(CONFIG).go_lint(package, has_error)


def go_timeouts():
    """Run through all .go files to ensure default http lib functions aren't used.

    :return:
    """
    global has_error
    has_error = GoTimeouts().validate_functions(has_error)


def go_vet(package):
    """Run go vet on all packages with all flags enabled.

    Ignores packages listed under config.go_vet.ignored_packages

    :param package: string
    """
    global has_error
    has_error = GoVet(CONFIG).go_vet(package, has_error)


# Pulled from config.py in the same dir
if CONFIG.all.project_type not in ["gb", "glide"]:
    logger.critical("Non gb/glide projects unsupported: {0}"
                    .format(CONFIG.all.project_type))
    sys.exit(0)

if len(CONFIG.all.packages) == 0:
    logger.critical("No packages listed to test")
    sys.exit(1)

# used to track whether errors have occured accross the tests
has_error = False

for package in CONFIG.all.packages:
    logger.info("BEGINNING TESTS FOR: {0}\n".format(package))

    # implement your ci tests here
    if "code_coverage" not in CONFIG.all.ignored_commands:
        code_coverage(package)
        logger.info("\n")

    if "go_lint" not in CONFIG.all.ignored_commands:
        go_lint(package)
        logger.info("\n")

    if "go_vet" not in CONFIG.all.ignored_commands:
        go_vet(package)
        logger.info("\n")

    if "go_timeouts" not in CONFIG.all.ignored_commands:
        go_timeouts()
        logger.info("\n")


if has_error:
    logger.info("Please rectify the above errors.")
    logger.info("Failure to comply will activate "
                "the trap door below your desk.")
    sys.exit(1)
else:
    logger.info("No errors found, we're proud of you.")
