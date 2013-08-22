# coding: utf-8

from powermeter.arduino import Arduino

modes = {
    "inst":  "I",
    "agreg": "A",
}


def snapshot(mode, waves, cycles, fake):
    with Arduino() as arduino:
        mode = modes[mode]
        ok = arduino.snapshot(mode, waves, cycles, fake)

        if not ok:
            raise IOError("Arduino refused to snapshot")

        print ("Collecting samples from %d cycles of %d waves"
                                            % (cycles, waves))

        for sample in arduino.samples():
            print sample


def monitor(mode, waves, fake):
    with Arduino() as arduino:
        mode = modes[mode]
        ok = arduino.monitor(mode, waves, fake)

        if not ok:
            raise IOError(u"Arduino refused to monitor")

        print "Collecting samples... Press ^C to interrupt"

        try:
            for sample in arduino.samples():
                # TODO: utilizar o sample
                pass

        except KeyboardInterrupt:
            pass
