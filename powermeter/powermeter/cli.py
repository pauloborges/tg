# coding: utf-8

import argparse
import os.path
import sys

DEFAULT_CONFIG_FILE = os.path.join(os.path.expanduser('~'),
                                        ".powermeter")

parser = argparse.ArgumentParser(prog=u"powermeter")
parsers = parser.add_subparsers()

###########################################################
# Monitor parser
###########################################################

MONITOR = "monitor"
MONITOR_OPTION_CHOICES = ("raw", "instantaneous", "agregate")

monitor = parsers.add_parser(MONITOR, help="real time monitoring "
                                    "of energy-related features")
monitor.set_defaults(command=MONITOR)

# ---------------------------------------------------------

monitor.add_argument(
    "option",
    choices=MONITOR_OPTION_CHOICES
)

monitor.add_argument(
    "quantity",
    type=int,
    help="number of waves for agregate option"
)

monitor.add_argument(
    "-f", "--fake",
    dest="fake_samples",
    action="store_true",
    help="use fake samples"
)

monitor.add_argument(
    "-d", "--debug",
    dest="debug",
    action="store_true",
    help="print debug to stderr")

monitor.add_argument(
    "-c", "--calibration",
    dest="calibration_filename",
    metavar="file",
    default=DEFAULT_CONFIG_FILE
)

monitor.add_argument(
    "-o", "--output",
    dest="output_fd",
    metavar="file",
    type=argparse.FileType('w'),
    default=sys.stdout
)

###########################################################
# Calibrate parser
###########################################################

CALIBRATE = "calibrate"
CALIBRATE_OPTION_CHOICES = ("offset", "gain", "phase")

calibrate = parsers.add_parser(CALIBRATE, help="calibrate "
                    "powermeter to accurately measure features")
calibrate.set_defaults(command=CALIBRATE)

calibrate.add_argument(
    "option",
    choices=CALIBRATE_OPTION_CHOICES
)

calibrate.add_argument(
    '-f', "--fake",
    dest="fake_samples",
    action="store_true",
    help="use fake samples"
)

calibrate.add_argument(
    "-o", "--output",
    dest="calibration_filename",
    metavar="file",
    default=DEFAULT_CONFIG_FILE
)

###########################################################
# Visualize parser
###########################################################

VISUALIZE = "visualize"

visualize = parsers.add_parser(VISUALIZE, help="show energy"
                    "-related graphs")
visualize.set_defaults(command=VISUALIZE)

visualize.add_argument(
    "option",
    choices=("raw", "instantaneous", "agregate")
)

visualize.add_argument(
    "input_fd",
    metavar="input",
    type=argparse.FileType('r'),
    default=sys.stdin,
    nargs='?'
)

###########################################################
# External API
###########################################################

def parse_args():
    args = parser.parse_args()
    return args.__dict__
