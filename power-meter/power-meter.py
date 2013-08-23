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
snapshot.add_argument("calibration", nargs='?',
                        default=CALIBRATION_FILE)

# monitor
monitor.set_defaults(action="monitor")
monitor.add_argument("mode", choices=MODE_OPTIONS)
monitor.add_argument("-f", "--fake", dest="fake",
                        action="store_true")
monitor.add_argument("-w", dest="number_waves", type=int,
                        required=True)
monitor.add_argument("calibration", nargs='?',
                        default=CALIBRATION_FILE)

# calibrate
calibrate.set_defaults(action="calibrate")

args = parser.parse_args()

if args.number_waves <= 0:
    parser.error("NUMBER_WAVES must be a positive value")

if hasattr(args, "number_cycles") and args.number_cycles <= 0:
    parser.error("NUMBER_CYCLES must be a positive value")

status = powermeter.run(**args.__dict__)
sys.exit(status)
