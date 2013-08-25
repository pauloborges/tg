# coding: utf-8

import serial as pyserial
from time import sleep
import os


class ArduinoError(IOError):
    pass


class Arduino(object):
    def __init__(self, timeout, debug=True):
        self.serial = None

        self.timeout = timeout
        self.debug = debug

    def start(self, device=None, baud="115200"):
        """
        Inicializa uma comunicação serial com o Arduino.
        """

        if self.serial is not None:
            raise ArduinoError(u"Serial communication already "
                                "established")

        if not device:
            devices = os.listdir("/dev")
            device = next(dev for dev in devices
                            if dev.startswith("ttyACM"))
            device = os.path.join("/dev", device)

        if self.debug:
            print "Serial communication to '%s' with %s bps" % (
                device, baud)
        # self.serial = pyserial.Serial(device, baud,
        #             timeout=self.timeout, writeTimeout=self.timeout)
        self.serial = pyserial.Serial(device, baud)


    def close(self):
        """
        Encerra a conexão Serial com o Arduino.
        """
        self.serial.flushInput()
        self.serial.close()
        self.serial = None


    def send_message(self, message):
        try:
            l = self.serial.write(message + '\n')
        except pyserial.SerialTimeoutException:
            raise ArduinoError("")

        if l < len(message) + 1:
            if self.debug:
                print "<<< %s...%s [broken message]" % (
                                        message[:l], message[l+1:])
            raise ArduinoError("")

        if self.debug:
            print "<<< %s" % message


    def read_message(self):
        message = self.serial.readline()

        if message[-1] != '\n':
            if self.debug:
                print ">>> %s [broken message]" % message
            raise ArduinoError("")

        message = message[:-1]
        if self.debug:
            print ">>> %s" % message

        if message.startswith("DEBUG"):
            return self.read_message()
        else:
            return message
