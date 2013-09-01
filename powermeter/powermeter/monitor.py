# coding: utf-8

import math

from powermeter.command import Command
from powermeter.arduino import Arduino
from powermeter.config import Config
from powermeter.protocol import *
from powermeter.util import enum

__all__ = ("Monitor")

NO_PHASECAL = 1.0
NO_VOLTAGE_OFFSET = 0
NO_CURRENT_OFFSET = 0

class Monitor(Command):
    OPTIONS = ("raw", "instantaneous", "agregate")
    ARGS = ("fake_samples", "debug", "quantity",
            "calibration_filename", "output_fd")

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

    def __init__(self, quantity, **kwargs):
        if quantity <= 0:
            raise ValueError("'quantity' must be a positive integer")

        self.quantity = quantity
        self.fake_samples = kwargs["fake_samples"]
        self.debug = kwargs["debug"]
        self.output = kwargs["output_fd"]
        self.config = Config(kwargs["calibration_filename"], False)

        self.status = self.STATUS.INIT

    def init(self):
        """
        Do a handshake:
        1. Open a serial connection with Arduino.
        2. Send a STOP REQUEST.
        3. Wait for an OK RESPONSE.
        """
        self.arduino = Arduino(RESPONSE_SIZE, debug=self.debug)
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
            self.fake_samples, self.quantity,
            self.config.calibration("phase"),
            self.config.calibration("voltage_offset"),
            self.config.calibration("current_offset")))

    def print_data(self, data):
        data = self.unpack_data(data)
        self.output.write(' '.join("%f" % d for d in data) + '\n')


class MonitorRaw(MonitorOption):
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
        message = self.arduino.read_message()
        opcode, data = dec_message(message)

        if opcode == RESPONSE.RAW:
            self.print_data(data)
        else:
            raise IOError("Expecting RAW, got %s"
                % RESPONSE.reverse[opcode])

    def unpack_data(self, data):
        voltage = (data.voltage
                    * self.config.calibration("voltage_gain"))

        current = (data.current
                    * self.config.calibration("current_gain"))

        real_power = voltage * current

        return (
            voltage,
            current,
            real_power
        )


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
        message = self.arduino.read_message()
        opcode, data = dec_message(message)

        if opcode == RESPONSE.INST:
            self.print_data(data)
        else:
            raise IOError("Expecting INST, got %s"
                % RESPONSE.reverse[opcode])

    def unpack_data(self, data):
        return (
            data.elapsed,
            data.voltage * self.config.calibration("voltage_gain"),
            data.current * self.config.calibration("current_gain")
        )


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
        message = self.arduino.read_message()
        opcode, data = dec_message(message)

        if opcode == RESPONSE.AGRE:
            self.print_data(data)
        else:
            raise IOError("Expecting AGRE, got %s"
                % RESPONSE.reverse[opcode])

    def unpack_data(self, data):
        print "AAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        rms_voltage = (data.rms_voltage
                        * self.config.calibration("voltage_gain"))

        rms_current = (data.rms_current
                        * self.config.calibration("current_gain"))

        real_power = (data.real_power
                        * self.config.calibration("real_power_gain"))

        total_power = rms_voltage * rms_current

        if total_power < real_power:
            print "total_power < real_power"
            total_power = real_power

        reac_power = math.sqrt(total_power**2 - real_power**2)

        power_factor = real_power / total_power

        return (
            rms_voltage, rms_current,
            real_power, reac_power,
            total_power, power_factor
        )
