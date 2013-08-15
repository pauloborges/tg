# coding: utf-8

import collections
import functools
import signal
import struct
import serial
import sys
import os


# Packet opcodes
RESPONSE = {
    "OK":       '0',
    "NO":       'N',
    "SAMPLE":   'S',
    "END":      'E',
}

REQUEST = {
    "STOP":     'S',
    "SNAPSHOT": 'A',
    "MONITOR":  'M',
}


def enc_stop_packet():
    return struct.pack("c", REQUEST["STOP"])


def enc_snapshot_packet(fake, size):
    return struct.pack("c?H", REQUEST["SNAPSHOT"], fake, size)


def enc_monitor_packet(fake):
    return struct.pack("c?", REQUEST["SNAPSHOT"], fake)


def dec_response_packet(packet):
    answer = struct.unpack("c", packet)
    if answer in (RESPONSE["OK"], RESPONSE["NO"]):
        return answer == RESPONSE["OK"]

    raise RuntimeError(u"Pacote não esperado: '%s'" % packet)


def dec_sample_packet(packet):
    pass


def timeout(seconds=1):
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise IOError(u"Arduino não respondeu")

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
            raise IOError(u"Comunicação já estabelecida")

        if not device:
            devices = os.listdir("/dev")
            device = next(dev for dev in devices if dev.startswith("ttyACM"))
            device = os.path.join("/dev", device)

        print "Comunicação serial para '%s' com %s bps" % (device, baud)
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
        return self.request(enc_stop_packet())

    def snapshot(self, size, fake):
        return self.request(enc_snapshot_packet(size, fake))

    def monitor(self, fake):
        return self.request(enc_monitor_packet(fake))

    @timeout(1)
    def request(self, packet):
        l = self.descriptor.write(packet)

        if l < len(packet):
            print "Corrigir..."

        return dec_response_packet(self.descriptor.read())

    def samples(self):
        pass


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
