# coding: utf-8

import ConfigParser
import time
import sys

from powermeter.command import Command
from powermeter.arduino import Arduino
from powermeter.config import Config
from powermeter.protocol import *
from powermeter.util import enum
from powermeter.qt import quit

__all__ = ("Calibrate")

NO_PHASECAL = 1.0
NO_VOLTAGE_OFFSET = 0
NO_CURRENT_OFFSET = 0

###########################################################
# Calibrate Command
###########################################################

class Calibrate(Command):
    OPTIONS = ("phase", "gain", "offset")
    ARGS = ("fake_samples", "calibration_filename")

    def __init__(self, **kwargs):
        option = kwargs.pop("option", None)
        super(Calibrate, self).__init__(option, self.OPTIONS)

        self.check_args(kwargs.keys(), self.ARGS)

        if option == "phase":
            self.option = CalibratePhase(**kwargs)
        elif option == "gain":
            self.option = CalibrateGain(**kwargs)
        else:
            self.option = CalibrateOffset(**kwargs)

    def run(self):
        self.option.run()

    def sigint_handler(self):
        self.option.sigint_handler()

###########################################################
# Calibrate Option [super]
###########################################################

class CalibrateOption(object):
    STATUS = enum("INIT", "SAMPLING")

    def __init__(self, **kwargs):
        self.fake_samples = kwargs["fake_samples"]
        self.status = self.STATUS.INIT
        self.config = Config(kwargs["calibration_filename"])

    def init(self):
        """
        Do a handshake:
        1. Open a serial connection with Arduino.
        2. Send a STOP REQUEST.
        3. Wait for an OK RESPONSE.
        """
        self.arduino = Arduino(RESPONSE_SIZE, debug=False)
        self.arduino.start()

        self.arduino.send_message(enc_stop_request())
        message = self.arduino.read_message()
        opcode, data = dec_message(message)

        if opcode != RESPONSE.OK:
            raise IOError("Expecting OK, got %s"
                % RESPONSE.reverse[opcode])

    def run(self):
        """Run the function with same name as current status."""
        getattr(self, "status_" + self.STATUS.reverse[self.status].lower())()

    def sigint_handler(self):
        self.arduino.send_message(enc_stop_request())
        self.arduino.close()

###########################################################
# Calibrate Phase
###########################################################

class CalibratePhase(CalibrateOption):
    pass

###########################################################
# Calibrate Gain
###########################################################

class CalibrateGain(CalibrateOption):
    DIG_TO_ANA = 5.0 / 1023.0

    def __init__(self, **kwargs):
        super(CalibrateGain, self).__init__(**kwargs)
        self.number_of_samples = 10
        self.data = []

    def status_init(self):
        super(CalibrateGain, self).init()

        raw_input("Plug a device with known power "
                    "[press enter to continue]")

        self.mains_voltage = float(raw_input("Mains RMS voltage: "))
        self.device_power = float(raw_input("Device Real Power: "))

        print "Fetching %d samples" % self.number_of_samples

        self.arduino.send_message(enc_monitor_request(MODE.AGRE,
            self.fake_samples, 60,
            self.config.calibration("phase"),
            self.config.calibration("voltage_offset"),
            self.config.calibration("current_offset")))
        message = self.arduino.read_message()
        opcode, data = dec_message(message)

        if opcode != RESPONSE.OK:
            raise IOError("Expecting OK, got %s"
                % RESPONSE.reverse[opcode])

        self.status = self.STATUS.SAMPLING

    def status_sampling(self):
        message = self.arduino.read_message()
        opcode, data = dec_message(message)

        if opcode == RESPONSE.AGRE:
            self.data.append(self.extract_data(data))

            self.number_of_samples -= 1
            if self.number_of_samples == 0:
                self.arduino.send_message(enc_stop_request())
                self.process_data_and_quit()
            else:
                print self.number_of_samples

        else:
            raise IOError("Expecting AGRE, got %s"
                % RESPONSE.reverse[opcode])

    def extract_data(self, data):
        return (data.rms_voltage, data.rms_current, data.real_power)

    def process_data_and_quit(self):
        v, i, p = zip(*self.data)

        v_mean = sum(v) / len(v)
        i_mean = sum(i) / len(i)
        p_mean = sum(p) / len(p)

        v_gain = self.mains_voltage / v_mean
        p_gain = self.device_power / p_mean
        i_gain = p_gain / v_gain

        self.config.calibration("voltage_gain", v_gain)
        self.config.calibration("current_gain", i_gain)
        self.config.calibration("real_power_gain", p_gain)
        self.config.save()

        quit()

###########################################################
# Calibrate Offset
###########################################################

class CalibrateOffset(CalibrateOption):
    def __init__(self, **kwargs):
        super(CalibrateOffset, self).__init__(**kwargs)
        self.number_of_samples = 25000
        self.data = []

    def status_init(self):
        super(CalibrateOffset, self).init()

        print "Fetching %d samples" % self.number_of_samples

        self.arduino.send_message(enc_monitor_request(MODE.RAW,
            self.fake_samples, 60, NO_PHASECAL, NO_VOLTAGE_OFFSET,
            NO_CURRENT_OFFSET))
        message = self.arduino.read_message()
        opcode, data = dec_message(message)

        if opcode != RESPONSE.OK:
            raise IOError("Expecting OK, got %s"
                % RESPONSE.reverse[opcode])

        self.status = self.STATUS.SAMPLING

    def status_sampling(self):
        message = self.arduino.read_message()
        opcode, data = dec_message(message)

        if opcode == RESPONSE.RAW:
            self.number_of_samples -= 1

            if self.number_of_samples < 20000:
                self.data.append(self.extract_data(data))

            if self.number_of_samples == 0:
                self.arduino.send_message(enc_stop_request())
                self.process_data_and_quit()
            elif self.number_of_samples % 5000 == 0:
                print "%d" % self.number_of_samples

        else:
            raise IOError("Expecting RAW, got %s"
                % RESPONSE.reverse[opcode])

    def extract_data(self, data):
        return (data.voltage, data.current)

    def process_data_and_quit(self):
        v, i = zip(*self.data)

        v_offset = round(sum(v) / len(v))
        i_offset = round(sum(i) / len(i))

        self.config.calibration("voltage_offset", v_offset)
        self.config.calibration("current_offset", i_offset)
        self.config.save()

        quit()
