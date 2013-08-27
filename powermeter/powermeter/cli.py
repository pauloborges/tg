# coding: utf-8

import argparse
import sys
import os.path

DEFAULT_CALIBRATION_FILE = os.path.join(os.path.expanduser('~'),
                                        ".powermeter_calibration")

parser = argparse.ArgumentParser(prog=u"powermeter")
parsers = parser.add_subparsers()

###########################################################
# Helpers
###########################################################

def add_argument_fake(parser):
    parser.add_argument(
        '-f', "--fake",
        dest="fake_samples",
        action="store_true",
        help="use fake samples"
    )

def add_argument_calibration_file(parser, flag, name, mode):
    parser.add_argument(
        flag, name,
        dest="calibration_fd",
        metavar="calibration_file",
        type=argparse.FileType(mode),
        default=DEFAULT_CALIBRATION_FILE
    )

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
    help="number of waves (instantaneous or agregate option) "
            "or number of samples (raw option)"
)

add_argument_fake(monitor)
add_argument_calibration_file(monitor, '-c', "--calibration", 'r')

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

add_argument_fake(calibrate)
add_argument_calibration_file(calibrate, '-o', "--output", 'w')

###########################################################
# Disagregate parser
###########################################################



###########################################################
# External API
###########################################################

def parse_args():
    args = parser.parse_args()
    return args.__dict__
