#!/usr/bin/env python
# coding: utf-8

from .cli import parse_args


def main():
    "Main entrypoint for powermeter utility."
    
    args = parse_args()
    print args


if __name__ == "__main__":
    main()
