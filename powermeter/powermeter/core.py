#!/usr/bin/env python
# coding: utf-8

import sys

from powermeter.cli import parse_args
from powermeter.host import PowerMeter


def initialize(kwargs):
    return PowerMeter.initialize(**kwargs)


def main():
    "Main entrypoint for powermeter utility."
    kwargs     = parse_args()
    powermeter = initialize(kwargs)

    return powermeter.exec_()


if __name__ == "__main__":
    sys.exit(main())
