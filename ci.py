#!/usr/bin/env python
"""Short description

Long informative description
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
        ['GOPATH=' + gopath + ' go test ' + package
            + '/... -cover'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True)

    out, err = p.communicate()

    if err is not None and not "\n":
        print(err)
        has_error = True

    lines = out.split('\n')
    package_pattern = re.compile(package + r'(\/[a-z\/]+)?')
    coverage_pattern = re.compile(r'[0-9]{1,3}.[0-9]%')

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

        elif "[no test files]" in line:
            err = True
            output += (package + " has no tests.\n")

    if err and not has_error:
        has_error = err

    if err:
        print("CODE COVERAGE: FAIL")
        print(output)
    else:
        print("CODE COVERAGE: PASS")


def go_lint(package):
    """

    Runs golint on all packages
    Ignores packages listed under config.golint.ignored_packages

    """
    global has_error

    err = False
    output = ""

    p = subprocess.Popen(
        ['golint src/' + package + '/...'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True)

    out, err_output = p.communicate()

    lines = out.split('\n')
    package_pattern = re.compile(package + r'(\/[a-z\/]+)?.go')
    file_pattern = re.compile(r'\/[a-z]+.go')

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


def go_vet(package):
    """

    Runs go vet on all packages with all flags enabled
    Ignores packages listed under config.go_vet.ignored_packages

    """
    global has_error

    err = False
    output = ""

    p = subprocess.Popen(
        ['go vet ' + package + '/...'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True)

    out, err_output = p.communicate()

    lines = err_output.split('\n')
    package_pattern = re.compile(package + r'(\/[a-z\/]+)?.go')
    file_pattern = re.compile(r'\/[a-z]+.go')

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
    code_coverage(package)
    go_lint(package)
    go_vet(package)


if has_error:
    print("Please rectify the above errors.")
    print("Failure to comply will activate the trap door below your desk.")
    sys.exit(1)
else:
    print("No errors found, we're proud of you.")
