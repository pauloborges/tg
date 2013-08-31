# coding: utf-8

import ConfigParser
import os.path

CALIB = "calibration"


class Config(object):
    def __init__(self, filename, create=True):
        self.parser = ConfigParser.SafeConfigParser()
        self.filename = filename

        try:
            with open(filename, 'r') as f:
                self.parser.readfp(f)
        except IOError, e:
            if not create:
                raise e
            self.build_default_config()

    def build_default_config(self):
        self.parser.add_section(CALIB)

        self.parser.set(CALIB, "phase", str(1.0))
        self.parser.set(CALIB, "voltage_offset", str(0.0))
        self.parser.set(CALIB, "current_offset", str(0.0))
        self.parser.set(CALIB, "voltage_gain", str(1.0))
        self.parser.set(CALIB, "current_gain", str(1.0))
        self.parser.set(CALIB, "real_power_gain", str(1.0))

        self.save()

    def save(self):
        with open(self.filename, 'w') as f:
            self.parser.write(f)

    def calibration(self, attr, value=None):
        if value:
            self.parser.set(CALIB, attr, str(value))
        else:
            return float(self.parser.get(CALIB, attr))
