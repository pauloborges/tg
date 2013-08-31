# coding: utf-8

import time

from powermeter.command import Command
from powermeter.arduino import Arduino
from powermeter.protocol import *
from powermeter.util import enum
from powermeter.qt import quit

__all__ = ("Calibrate")

NO_PHASECAL = 1.0
NO_VOLTAGE_OFFSET = 0
NO_CURRENT_OFFSET = 0

class Calibrate(Command):
    OPTIONS = ("phase", "gain", "offset")
    ARGS = ("fake_samples", "calibration_fd")

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


class CalibrateOption(object):
    STATUS = enum("INIT", "SAMPLING")

    def __init__(self, fake_samples, **kwargs):
        self.fake_samples = fake_samples
        self.status = self.STATUS.INIT

    def init(self):
        """
        Do a handshake:
        1. Open a serial connection with Arduino.
        2. Send a STOP REQUEST.
        3. Wait for an OK RESPONSE.
        """
        self.arduino = Arduino(RESPONSE_SIZE)
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

    def send_monitor_request(self, mode, quantity):
        self.arduino.send_message(enc_monitor_request(mode,
            self.fake_samples, quantity, NO_PHASECAL,
            NO_VOLTAGE_OFFSET, NO_CURRENT_OFFSET))


class CalibratePhase(CalibrateOption):
    pass


class CalibrateGain(CalibrateOption):
    pass


class CalibrateOffset(CalibrateOption):
    def __init__(self, **kwargs):
        super(CalibrateOffset, self).__init__(**kwargs)
        self.number_of_samples = 1000
        self.samples = []

    def status_init(self):
        super(CalibrateOffset, self).init()

        self.send_monitor_request(MODE.INST, 20)
        message = self.arduino.read_message()
        opcode, data = dec_message(message)

        if opcode != RESPONSE.OK:
            raise IOError("Expecting OK, got %s"
                % RESPONSE.reverse[opcode])

        self.status = self.STATUS.SAMPLING

    def status_sampling(self):
        message = self.arduino.read_message()
        opcode, data = dec_message(message)

        if opcode == RESPONSE.INST:
            self.samples.append(data)

            self.number_of_samples -= 1
            if self.number_of_samples == 0:
                self.arduino.send_message(enc_stop_request())
                self.process_data_and_quit()

        else:
            raise IOError("Expecting RAW, got %s"
                % RESPONSE.reverse[opcode])

    def process_data_and_quit(self):
        print "len:", len(self.samples)
        quit()
