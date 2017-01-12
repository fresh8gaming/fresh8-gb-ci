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

import os
import subprocess
import re
import sys
import logging

from utils.config import get_config

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
    """

    Runs go test -cover, parses the output line by line

    Ignores packages listed under config.code_coverage.ignored_packages
    Threshold taken from config.code_coverage.threshold
        must be of type float (e.g 50.0)

    """
    global has_error

    err = False
    output = ""

    # E.G `GOPATH=${PWD}:${PWD}/vendor go test pipeline/... -cover`
    p = subprocess.Popen(
        ["GOPATH={0} go test {1}/... -cover".format(gopath, package)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True)

    out, err = p.communicate()

    if err is not None and not "\n":
        logger.error(err)
        has_error = True

    lines = out.split('\n')
    package_pattern = re.compile(package + r'(\/[a-zA-Z0-9\/]+)?')
    coverage_pattern = re.compile(r'[0-9]{1,3}.[0-9]%')

    coverage_count = 0
    coverage_cum = 0.0

    for line in lines:
        package = re.search(package_pattern, line)

        if package is None:
            continue

        package = package.group(0)

        coverage = re.search(coverage_pattern, line)
        if coverage is not None:
            # Allow to be passed through as none
            # See `elif "[no test files]"`
            coverage = coverage.group(0)

        if package in CONFIG.code_coverage.ignored_packages:
            continue

        if coverage is not None:
            cv = float(coverage[:-1])

            if cv < CONFIG.code_coverage.threshold:
                err = True
                output += "{0} under coverage threshold at {1}\n".format(
                    package, coverage)

            coverage_cum += cv

        elif "[no test files]" in line:
            err = True
            output += "{0} has no tests.\n".format(package)

        coverage_count += 1

    if err and not has_error:
        has_error = err

    if coverage_count == 0:
        logger.info("No packages available for coverage calculation")
        return

    total_coverage = round(coverage_cum / coverage_count, 2)

    if err:
        logger.info("CODE COVERAGE: FAIL")
        logger.info("Current coverage: {0}%".format(str(total_coverage)))
        logger.info("Coverage threshold: {0}%"
                    .format(str(CONFIG.code_coverage.threshold)))
        logger.info(output)
    else:
        logger.info("CODE COVERAGE: PASS")
        logger.info("Current coverage: {0}%".format(str(total_coverage)))
        logger.info("Coverage threshold: {0}%"
                    .format(str(CONFIG.code_coverage.threshold)))


def go_lint(package):
    """

    Runs golint on all packages
    Ignores packages listed under config.golint.ignored_packages

    """
    global has_error

    err = False
    output = ""

    p = subprocess.Popen(
        ["golint src/{0}/...".format(package)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True)

    out, err_output = p.communicate()

    lines = out.split('\n')
    package_pattern = re.compile(package + r'(\/[a-zA-Z0-9\/]+)?.go')
    file_pattern = re.compile(r'\/[a-zA-Z0-9]+.go')

    for line in lines:
        package = re.search(package_pattern, line)

        if package is None:
            continue

        package = package.group(0)
        package = re.sub(file_pattern, '', package)

        if package in CONFIG.golint.ignored_packages:
            continue

        err = True
        output += line + "\n"

    if err and not has_error:
        has_error = err

    if err:
        logger.info("GOLINT: FAIL")
        logger.info(out)
    else:
        logger.info("GOLINT: PASS")


def go_timeouts():
    """

    Runs through all .go files and ensures default http lib functions
    are not used

    """

    def get_error_message_for_line(match, pattern):
        return "{0} contains default http function {1} on line {2}\n"\
            .format(match.group(1), pattern, match.group(2))

    global has_error

    err = False
    output = ""

    patterns = [
        "http.ListenAndServe(",
        "http.Get(",
        "http.Post(",
        "http.PostForm(",
        "http.Head("
    ]

    for pattern in patterns:
        p = subprocess.Popen(
            ["grep '{0}' src -R -n".format(pattern)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True)

        out, err_output = p.communicate()

        if out != '':
            lines = out.split('\n')
            file_pattern = re.compile('^([a-zA-Z0-9\/]+.go)\:([0-9]+)')

            for line in lines:
                filename_match = re.match(file_pattern, line)

                if filename_match is None:
                    continue

                err = True
                output += get_error_message_for_line(filename_match, pattern)

    if err and not has_error:
        has_error = err

    if err:
        logger.info("GO TIMEOUTS: FAIL")
        logger.info(output)

        hint = "For more info on why this is bad, please read {}"
        hint = hint.format("https://blog.cloudflare.com/the-complete-guide-to-golang-net-http-timeouts/")  # noqa

        logger.info(hint)
    else:
        logger.info("GO TIMEOUTS: PASS")


def go_vet(package):
    """

    Runs go vet on all packages with all flags enabled
    Ignores packages listed under config.go_vet.ignored_packages

    """
    global has_error

    err = False
    output = ""

    p = subprocess.Popen(
        ["go vet {0}/...".format(package)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True)

    out, err_output = p.communicate()

    lines = err_output.split('\n')
    package_pattern = re.compile(package + r'(\/[a-zA-Z0-9\/]+)?.go')
    file_pattern = re.compile(r'\/[a-zA-Z0-9]+.go')

    for line in lines:
        package = re.search(package_pattern, line)

        if package is None:
            continue

        package = package.group(0)
        package = re.sub(file_pattern, '', package)

        if package in CONFIG.go_vet.ignored_packages:
            continue

        err = True
        output += line + "\n"

    if err and not has_error:
        has_error = err

    if err:
        logger.info("GO VET: FAIL")
        logger.info(output)
    else:
        logger.info("GO VET: PASS")


# Pulled from config.py in the same dir
if CONFIG.all.project_type not in ["gb", "glide"]:
    logger.critical("Non gb/glide projects unsupported: {0}"
                    .format(CONFIG.all.project_type))
    sys.exit(0)

if len(CONFIG.all.packages) == 0:
    logger.critical("No packages listed to test")
    sys.exit(1)

# set `gopath` depending on gb or glide
gopath = "{0}:{0}/vendor".format(os.getcwd()) \
    if CONFIG.all.project_type == "gb" else os.getcwd()

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
