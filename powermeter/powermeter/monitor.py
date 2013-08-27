# coding: utf-8

import time

from powermeter.command import Command
from powermeter.arduino import Arduino
from powermeter.protocol import *
from powermeter.util import enum

__all__ = ("Monitor")

NO_PHASECAL = 1.0
NO_VOLTAGE_OFFSET = 0.0
NO_CURRENT_OFFSET = 0.0

class Monitor(Command):
    OPTIONS = ("raw", "instantaneous", "agregate")
    ARGS = ("fake_samples", "quantity")

    def __init__(self, **kwargs):
        option = kwargs.pop("option", None)
        super(Monitor, self).__init__(option, self.OPTIONS)

        self.check_args(kwargs.keys(), self.ARGS)

        if option == "raw":
            self.option = MonitorRaw(**kwargs)
        elif option == "instantaneous":
            self.option = MonitorInstantaneous(**kwargs)
        else:
            sef.option = MonitorAgregate(**kwargs)

    def run(self):
        self.option.run()


class MonitorOption(object):
    def __init__(self, fake_samples, **kwargs):
        self.fake_samples = fake_samples

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


class MonitorRaw(MonitorOption):
    STATUS = enum("INIT", "SAMPLING", "END")

    def __init__(self, quantity, **kwargs):
        super(MonitorRaw, self).__init__(**kwargs)

        if quantity <= 0:
            raise ValueError("'quantity' must be a positive integer")

        self.quantity = quantity
        self.status = self.STATUS.INIT

    def run(self):
        """Run the function with same name as current status."""
        getattr(self, "status_" + self.STATUS.reverse[self.status].lower())()

    def status_init(self):
        super(MonitorRaw, self).init()

        self.arduino.send_message(enc_monitor_request(MODE.RAW,
                        self.fake_samples, self.quantity, NO_PHASECAL,
                        NO_VOLTAGE_OFFSET, NO_CURRENT_OFFSET))
        message = self.arduino.read_message()
        opcode, data = dec_message(message)

        if opcode != RESPONSE.OK:
            raise IOError("Expecting OK, got %s"
                % RESPONSE.reverse[opcode])

        self.current_quantity = 0
        self.status = self.STATUS.SAMPLING

    def status_sampling(self):
        """Continuous sampling."""
        message = self.arduino.read_message()
        opcode, data = dec_message(message)

        if opcode == RESPONSE.RAW:
            print data
            
            if self.current_quantity == self.quantity:
                self.arduino.send_message(enc_stop_request())
                self.arduino.close()
                return

            self.current_quantity += 1
        elif opcode == RESPONSE.OK:
            self.status = self.STATUS.END
        else:
            raise IOError("Expecting (RAW, OK), got %s"
                % RESPONSE.reverse[opcode])

    def status_end(self):
        time.sleep(0.1) # busy loop
        # FIXME stop the timer
