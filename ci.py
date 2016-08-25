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
from config import config

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


def error(*objs):
    """

    Outputs to stderr

    """
    print(*objs, file=sys.stderr)


def validate_config():
    """

    Validates the configuration file, checks it has required fields

    """
    # TODO implement function when config is finalized
    pass


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
        ["GOPATH=" + gopath + " go test " + package + "/... -cover"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True)

    out, err = p.communicate()

    if err is not None and not "\n":
        print(err)
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

        if package in config.code_coverage.ignored_packages:
            continue

        if coverage is not None:
            cv = float(coverage[:-1])

            if cv < config.code_coverage.threshold:
                err = True
                output += (
                    package + " under coverage threshold at " +
                    coverage + "\n")

            coverage_cum += cv

        elif "[no test files]" in line:
            err = True
            output += (package + " has no tests.\n")

        coverage_count += 1

    if err and not has_error:
        has_error = err

    total_coverage = round(coverage_cum / coverage_count, 2)

    if err:
        print("CODE COVERAGE: FAIL")
        print("Current coverage: " + str(total_coverage) + "%")
        print("Coverage threshold: " +
              str(config.code_coverage.threshold) + "%")
        print(output)
    else:
        print("CODE COVERAGE: PASS")
        print("Current coverage: " + str(total_coverage) + "%")
        print("Coverage threshold: " +
              str(config.code_coverage.threshold) + "%")


def go_lint(package):
    """

    Runs golint on all packages
    Ignores packages listed under config.golint.ignored_packages

    """
    global has_error

    err = False
    output = ""

    p = subprocess.Popen(
        ["golint src/" + package + "/..."],
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

        if package in config.golint.ignored_packages:
            continue

        err = True
        output += line + "\n"

    if err and not has_error:
        has_error = err

    if err:
        print("GOLINT: FAIL")
        print(out)
    else:
        print("GOLINT: PASS")


def go_timeouts():
    """

    Runs through all .go files and ensures default http lib functions
    are not used

    """

    def get_error_message_for_line(match, pattern):
        return filename_match.group(1) + " contains default http function `"
        + pattern + "` on line " + filename_match.group(2) + "\n"

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
            ["grep '" + pattern + "' src -R -n"],
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
        print("GO TIMEOUTS: FAIL")
        print(output)

        hint = "For more info on why this is bad, please read "
        + "https://blog.cloudflare.com"
        + "/the-complete-guide-to-golang-net-http-timeouts/"
        print(hint)
        print()
    else:
        print("GO TIMEOUTS: PASS")


def go_vet(package):
    """

    Runs go vet on all packages with all flags enabled
    Ignores packages listed under config.go_vet.ignored_packages

    """
    global has_error

    err = False
    output = ""

    p = subprocess.Popen(
        ["go vet " + package + "/..."],
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

        if package in config.go_vet.ignored_packages:
            continue

        err = True
        output += line + "\n"

    if err and not has_error:
        has_error = err

    if err:
        print("GO VET: FAIL")
        print(output)
    else:
        print("GO VET: PASS")


# Pulled from config.py in the same dir
if config.all.project_type != "gb":
    print(config.all.project_type)
    print("Non gb projects unsupported")
    sys.exit(0)

if len(config.all.packages) == 0:
    print("No packages listed to test")
    sys.exit(1)

gopath = "%s:%s/vendor" % (os.getcwd(), os.getcwd())
# used to track whether errors have occured accross the tests
has_error = False

for package in config.all.packages:
    print("BEGINNING TESTS FOR: " + package + "\n")

    # implement your ci tests here
    if "code_coverage" not in config.all.ignored_commands:
        code_coverage(package)
        print("")

    if "go_lint" not in config.all.ignored_commands:
        go_lint(package)
        print("")

    if "go_vet" not in config.all.ignored_commands:
        go_vet(package)
        print("")

    if "go_timeouts" not in config.all.ignored_commands:
        go_timeouts()
        print("")


if has_error:
    print("Please rectify the above errors.")
    print("Failure to comply will activate the trap door below your desk.")
    sys.exit(1)
else:
    print("No errors found, we're proud of you.")
