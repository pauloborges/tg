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

def add_argument_number_of_waves(parser):
    parser.add_argument(
        '-w', "--number-waves",
        dest="number_of_waves",
        metavar="number_of_waves",
        type=int,
        required=True
    )

###########################################################
# Monitor parser
###########################################################

MONITOR         = "monitor"
RAW             = "raw"
INSTANTANEOUS   = "instantaneous"
AGREGATE        = "agregate"

monitor = parsers.add_parser(MONITOR, help="real time monitoring "
                                    "of energy-related features")
monitor.set_defaults(command=MONITOR)
monitor_parsers = monitor.add_subparsers()

# ---------------------------------------------------------

raw = monitor_parsers.add_parser(RAW)
raw.set_defaults(option=RAW)

raw.add_argument(
    '-s', "--samples",
    dest="number_of_samples",
    metavar="number_of_samples",
    type=int,
    required=True,
)

add_argument_fake(raw)

# ---------------------------------------------------------

instantaneous = monitor_parsers.add_parser(INSTANTANEOUS)
instantaneous.set_defaults(option=INSTANTANEOUS)

add_argument_number_of_waves(instantaneous)
add_argument_fake(instantaneous)

# ---------------------------------------------------------

agregate = monitor_parsers.add_parser(AGREGATE)
agregate.set_defaults(option=AGREGATE)

agregate.add_argument(
    '-c', "--number-cycles",
    dest="number_of_cycles",
    metavar="number_of_cycles",
    type=int,
    required=True
)

add_argument_number_of_waves(agregate)
add_argument_fake(agregate)

###########################################################
# Calibrate parser
###########################################################

CALIBRATE   = "calibrate"
CALIBRATE_OPTION_CHOICES = ("offset", "gain", "phase")

calibrate = parsers.add_parser(CALIBRATE, help="calibrate "
                    "powermeter to accurately measure features")
calibrate.set_defaults(command=CALIBRATE)

calibrate_parsers = calibrate.add_argument(
    "option",
    choices=CALIBRATE_OPTION_CHOICES
)

calibrate.add_argument(
    '-o', "--output",
    dest="calibration_fd",
    metavar="calibration_file",
    type=argparse.FileType('w'),
    default=DEFAULT_CALIBRATION_FILE
)

add_argument_fake(calibrate)

###########################################################
# Disagregate parser
###########################################################



###########################################################
# External API
###########################################################

def parse_args():
    args = parser.parse_args()

    return args
