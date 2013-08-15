# coding: utf-8

from powermeter.arduino import Arduino
import struct


def snapshot(size, fake):
    with Arduino() as arduino:
        ok = arduino.snapshot(size, fake)

        if not ok:
            raise IOError(u"Arduino rejeitou a conexão")

        print u"Coletando %d amostras..." % size

        while True:
            print arduino.descriptor.readline(),

        # for sample in arduino.samples():
        #     pass


def monitor(fake,):
    with Arduino() as arduino:
        ok = arduino.monitor(fake)

        if not ok:
            raise IOError(u"")

        print u"Coletando amostras... para interromper pressione ^C."

        try:
            for sample in arduino.samples():
                # TODO: utilizar o sample
                pass

        except KeyboardInterrupt:
            # O __exit__ do ContextManager irá enviar um STOP request
            pass
