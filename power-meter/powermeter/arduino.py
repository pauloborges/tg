# coding: utf-8

import collections
import functools
import signal
import struct
import serial
import sys
import os


# message opcodes
RESPONSE = {
    "OK":       'O',
    "NO":       'N',
    "INST_EV":  'I',
    "AGREG_EV": 'A',
}

REQUEST = {
    "STOP":     'S',
    "SNAPSHOT": 'P',
    "MONITOR":  'M',
}


def enc_stop_message():
    return REQUEST["STOP"] + '\n'


def enc_snapshot_message(mode, waves, cycles, fake):
    message = REQUEST["SNAPSHOT"]
    message += '1' if fake else '0'
    message += mode
    message += "%03d" % waves
    message += "%03d" % cycles
    message += '\n'
    return message


def enc_monitor_message(fake):
    message = REQUEST["MONITOR"]
    message += '1' if fake else '0'
    message += mode
    message += "%03d" % waves
    message += '\n'
    return message


def dec_response_message(message):
    if message[0] in (RESPONSE["OK"], RESPONSE["NO"]):
        print ">>>", message
        return message[0] == RESPONSE["OK"]

    if message.startswith("DEBUG"):
        print ">>>", message[:-1]
        return

    raise RuntimeError(u"Unexpected message: '%s'"
                                                % message)


def dec_sample_message(message):
    pass


def timeout(seconds=1):
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise IOError(u"Timeout from Arduino")

        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result
        return functools.wraps(func)(wrapper)
    return decorator


class ArduinoImpl(object):
    def __init__(self):
        self.started = False
        self.descriptor = None
        self.in_buffer = collections.deque() # maxlen?

    def start(self, device=None, baud="115200"):
        """
        Inicializa uma comunicação serial com o Arduino e envia um STOP request
        para o mesmo. O STOP é enviado para forçar o Arduino ir para o estado
        inicial (STOPPED).
        """
        if self.descriptor:
            raise IOError(u"Link already established")

        if not device:
            devices = os.listdir("/dev")
            device = next(dev for dev in devices if dev.startswith("ttyACM"))
            device = os.path.join("/dev", device)

        print "Serial link to '%s' with %s bps" % (device, baud)
        self.descriptor = serial.Serial(device, baud)

        self.stop()

    def close(self):
        """
        Envia um STOP request para o Arduino e encerra a conexão Serial com o
        mesmo. O request é enviado para o Arduino entrar em um modo de
        "baixo processamento" (não utilizar ADC, Serial, etc).
        """
        self.stop()
        self.descriptor.close()
        self.descriptor = None

    def stop(self):
        """
        Leva o Arduino para seu estado inicial (possivelmente interrompendo um
        MONITOR request).
        """
        return self.request(enc_stop_message())

    def snapshot(self, mode, waves, cycles, fake):
        return self.request(
            enc_snapshot_message(mode, waves, cycles, fake))

    def monitor(self, mode, waves, fake):
        return self.request(
            enc_monitor_message(mode, waves, fake))

    @timeout(1)
    def request(self, message):
        print "<<<", message,
        l = self.descriptor.write(message)

        if l < len(message):
            raise IOError("Wrote %d bytes, expected %d bytes"
                                        % (l, len(message)))

        while True:
            resp = dec_response_message(
                                self.descriptor.readline())
            if resp is not None:
                return resp

    def samples(self):
        while True:
            line = self.descriptor.readline()
            if line.startswith("DEBUG"):
                print line
            elif line[0] == RESPONSE["INST_EV"]:
                yield self.inst_ev()
            elif line[0] == RESPONSE["AGREG_EV"]:
                yield self.agreg_ev()
            elif line[0] == RESPONSE["OK"]:
                return
            else:
                raise IOError("Unexpected message: '%s'"
                                                % message)

    def inst_ev(self):
        try:
            t = self.descriptor.readline()
            v = self.descriptor.readline()
            i = self.descriptor.readline()
            t, v, i = map(float, (t, v, i))
        except:
            raise IOError("Instantaneous event parsing "
                "failed: %s" % repr((t, v, i)))

        return t, v, i

    def agreg_ev(self):
        try:
            t = self.descriptor.readline()
            v = self.descriptor.readline()
            i = self.descriptor.readline()
            rp = self.descriptor.readline()
            t, v, i, rp = map(float, (t, v, i, rp))
        except:
            raise IOError("Instantaneous event parsing "
                "failed: %s" % repr((t, v, i, rp)))

        return t, v, i, rp

class Arduino(object):
    def __init__(self, *args, **kwargs):
        self.arduino = ArduinoImpl()
        self.args = args
        self.kwargs = kwargs

    def __enter__(self):
        self.arduino.start()
        return self.arduino

    def __exit__(self, exception_type, exception_val, trace):
        self.arduino.close()

        if not exception_type:
            return True
