# coding: utf-8

import time

from powermeter.command import Command
from powermeter.arduino import Arduino
from powermeter.protocol import *
from powermeter.util import enum

__all__ = ("Monitor")

NO_PHASECAL = 1.0
NO_VOLTAGE_OFFSET = 0
NO_CURRENT_OFFSET = 0

class Monitor(Command):
    OPTIONS = ("raw", "instantaneous", "agregate")
    ARGS = ("fake_samples", "quantity", "calibration_fd")

    def __init__(self, **kwargs):
        option = kwargs.pop("option", None)
        super(Monitor, self).__init__(option, self.OPTIONS)

        self.check_args(kwargs.keys(), self.ARGS)

        if option == "raw":
            self.option = MonitorRaw(**kwargs)
        elif option == "instantaneous":
            self.option = MonitorInstantaneous(**kwargs)
        else:
            self.option = MonitorAgregate(**kwargs)

    def run(self):
        self.option.run()

    def sigint_handler(self):
        self.option.sigint_handler()


class MonitorOption(object):
    STATUS = enum("INIT", "SAMPLING")

    def __init__(self, fake_samples, quantity, **kwargs):
        if quantity <= 0:
            raise ValueError("'quantity' must be a positive integer")

        self.fake_samples = fake_samples
        self.quantity = quantity

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

    def send_monitor_request(self, mode):
        self.arduino.send_message(enc_monitor_request(mode,
            self.fake_samples, self.quantity, NO_PHASECAL,
            NO_VOLTAGE_OFFSET, NO_CURRENT_OFFSET))


class MonitorRaw(MonitorOption):
    STATUS = enum("INIT", "SAMPLING")

    def status_init(self):
        super(MonitorRaw, self).init()

        self.send_monitor_request(MODE.RAW)
        message = self.arduino.read_message()
        opcode, data = dec_message(message)

        if opcode != RESPONSE.OK:
            raise IOError("Expecting OK, got %s"
                % RESPONSE.reverse[opcode])

        self.status = self.STATUS.SAMPLING

    def status_sampling(self):
        """Continuous sampling."""
        message = self.arduino.read_message()
        opcode, data = dec_message(message)

        if opcode == RESPONSE.RAW:
            print data
        else:
            raise IOError("Expecting RAW, got %s"
                % RESPONSE.reverse[opcode])


class MonitorInstantaneous(MonitorOption):
    def status_init(self):
        super(MonitorInstantaneous, self).init()

        self.send_monitor_request(MODE.INST)
        message = self.arduino.read_message()
        opcode, data = dec_message(message)

        if opcode != RESPONSE.OK:
            raise IOError("Expecting OK, got %s"
                % RESPONSE.reverse[opcode])

        self.status = self.STATUS.SAMPLING

    def status_sampling(self):
        """Continuous sampling."""
        message = self.arduino.read_message()
        opcode, data = dec_message(message)

        if opcode == RESPONSE.INST:
            print data
        else:
            raise IOError("Expecting INST, got %s"
                % RESPONSE.reverse[opcode])


class MonitorAgregate(MonitorOption):
    def status_init(self):
        super(MonitorAgregate, self).init()

        self.send_monitor_request(MODE.AGRE)
        message = self.arduino.read_message()
        opcode, data = dec_message(message)

        if opcode != RESPONSE.OK:
            raise IOError("Expecting OK, got %s"
                % RESPONSE.reverse[opcode])

        self.status = self.STATUS.SAMPLING

    def status_sampling(self):
        """Continuous sampling."""
        message = self.arduino.read_message()
        opcode, data = dec_message(message)

        if opcode == RESPONSE.AGRE:
            print data
        else:
            raise IOError("Expecting AGRE, got %s"
                % RESPONSE.reverse[opcode])
