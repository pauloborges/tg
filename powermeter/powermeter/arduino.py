# coding: utf-8

import serial as pyserial
import os


class Arduino(object):
    def __init__(self, responses, debug=True):
        self.serial = None
        self.debug = debug
        self.responses = responses

    def start(self, device=None, baud="115200"):
        """
        Inicializa uma comunicação serial com o Arduino.
        """
        if self.serial is not None:
            raise IOError(u"Serial communication already "
                                "established")

        if not device:
            devices = os.listdir("/dev")
            device = next(dev for dev in devices
                            if dev.startswith("ttyACM"))
            device = os.path.join("/dev", device)

        if self.debug:
            print "Serial communication to '%s' with %s bps" % (
                device, baud)

        self.serial = pyserial.Serial(device, baud)
        self.serial.flushInput()
        self.serial.flushOutput()

    def close(self):
        """
        Encerra a conexão Serial com o Arduino.
        """
        self.serial.flushInput()
        self.serial.close()
        self.serial = None

    def send_message(self, message):
        l = self.serial.write(message)

        if l < len(message):
            if self.debug:
                print "<<< %s...%s [broken message]" % (
                    prettify(message[:l]), prettify(message[l+1:]))
            raise IOError("")

        if self.debug:
            print "<<< %s" % prettify(message)

    def read_message(self):
        message = self.serial.read()
        opcode = ord(message)

        if opcode not in self.responses and message != 'D':
            print ">>> ??? %s" % prettify(message)
            return
        elif message == 'D':
            message += self.serial.readline()
            print ">>> %s" % message,
            return self.read_message()
        
        if self.responses[opcode] > 0:
            message += self.serial.read(self.responses[opcode] - 1)

        if self.debug:
            print ">>> %s" % prettify(message)

        return message


def prettify(message):
    return ' '.join(hex(ord(c)) for c in message)
