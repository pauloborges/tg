#!/usr/bin/env python
# coding: utf-8

"""
power-meter.py {snapshot, monitor, calibrate}

--> snapshot
power-meter.py snapshot {inst, agreg} -f -w 10 -c 20 [calibration]

If calibration isn't specified, use "./calibration"

--> monitor
power-meter.py monitor {inst, agreg} -f -w 10 [calibration]

If calibration isn't specified, use "./calibration"

--> calibrate
TODO
"""

import sys
import argparse
import powermeter

MODE_OPTIONS = powermeter.MODE_OPTIONS.keys()
BAUD_OPTIONS = ("300", "600", "1200", "2400", "4800", "9600",
                "14400", "19200", "28800", "38400", "57600",
                "115200")
CALIBRATE_OPTIONS = ("phase", "offset", "gain")
CALIBRATION_FILE = "calibration"

parser      = argparse.ArgumentParser()
subparsers  = parser.add_subparsers()
snapshot    = subparsers.add_parser("snapshot")
monitor     = subparsers.add_parser("monitor")
calibrate   = subparsers.add_parser("calibrate")

# snapshot
snapshot.set_defaults(action="snapshot")
snapshot.add_argument("mode", choices=MODE_OPTIONS)
snapshot.add_argument("-f", "--fake", dest="fake",
                        action="store_true")
snapshot.add_argument("-w", dest="number_waves", type=int,
                        required=True)
snapshot.add_argument("-c", dest="number_cycles",type=int,
                        required=True)
snapshot.add_argument("-b", dest="baud", choices=BAUD_OPTIONS,
                        default="115200", help="baud rate")
snapshot.add_argument("calibration", nargs='?',
                        default=CALIBRATION_FILE,
                        help="calibration file")

# monitor
monitor.set_defaults(action="monitor")
monitor.add_argument("mode", choices=MODE_OPTIONS)
monitor.add_argument("-f", "--fake", dest="fake",
                        action="store_true")
monitor.add_argument("-w", dest="number_waves", type=int,
                        required=True)
monitor.add_argument("-b", dest="baud", choices=BAUD_OPTIONS,
                        default="115200", help="baud rate")
monitor.add_argument("calibration", nargs='?',
                        default=CALIBRATION_FILE,
                        help="calibration file")

# calibrate
calibrate.set_defaults(action="calibrate")
calibrate.add_argument("-f", "--fake", dest="fake",
                        action="store_true")
calibrate.add_argument("mode", choices=CALIBRATE_OPTIONS)
calibrate.add_argument("file", default=CALIBRATION_FILE,
                        help="calibration file")
calibrate.add_argument("-b", dest="baud", choices=BAUD_OPTIONS,
                        default="115200", help="baud rate")

args = parser.parse_args()

if args.action != "calibrate":
    if args.number_waves <= 0:
        parser.error("NUMBER_WAVES must be a positive value")

    if hasattr(args, "number_cycles") and args.number_cycles <= 0:
        parser.error("NUMBER_CYCLES must be a positive value")

status = powermeter.run(**args.__dict__)
sys.exit(status)
