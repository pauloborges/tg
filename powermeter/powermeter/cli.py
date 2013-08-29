# coding: utf-8

import argparse
import sys
import os.path

DEFAULT_CALIBRATION_FILE = os.path.join(os.path.expanduser('~'),
                                        ".powermeter_calibration")

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
    '-f', "--fake",
    dest="fake_samples",
    action="store_true",
    help="use fake samples"
)

parser.add_argument(
    "-c", "--calibration",
    dest="calibration_fd",
    metavar="file",
    type=argparse.FileType(mode),
    default=DEFAULT_CALIBRATION_FILE
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
    dest="calibration_fd",
    metavar="file",
    type=argparse.FileType(mode),
    default=DEFAULT_CALIBRATION_FILE
)

###########################################################
# External API
###########################################################

def parse_args():
    args = parser.parse_args()
    return args.__dict__
