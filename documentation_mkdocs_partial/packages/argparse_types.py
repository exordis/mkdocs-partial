import os
from argparse import ArgumentTypeError


def directory(value):
    if not os.path.isdir(value):
        raise ArgumentTypeError("Must be an existing directory")
    return value


def file(value):
    if not os.path.isfile(value):
        raise ArgumentTypeError("Must be an existing file")
    return value
