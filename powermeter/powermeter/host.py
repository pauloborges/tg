# coding: utf-8

import signal

from powermeter import qt
from powermeter.monitor import Monitor
from powermeter.calibrate import Calibrate

__all__ = ("PowerMeter", "quit")


def build_command(command, **kwargs):
    command = command.capitalize()

    if command not in globals():
        raise ValueError("Command '%s' not found" % command)

    return globals()[command](**kwargs)


class PowerMeter(object):
    def __init__(self):
        self.already_quit = False

    @classmethod
    def initialize(cls, **kwargs):
        try:
            command = kwargs.pop("command")
        except KeyError:
            raise ValueError("Missing 'command' argument")

        global powermeter
        powermeter = PowerMeter()
        powermeter.command = build_command(command, **kwargs)
        signal.signal(signal.SIGINT, powermeter.sigint_handler)

        return powermeter

    def exec_(self):
        self.app = qt.initialize()
        qt.idle_loop(self.run)

        return self.app.exec_()

    def quit(self):
        if self.already_quit:
            return

        self.already_quit = True
        self.command.sigint_handler()
        self.app.quit()

    def run(self):
        try:
            self.command.run()
        except Exception, e:
            print "Exception raised:", e
            self.quit()

    def sigint_handler(self, *args):
        print "\ninterrupting gracefully..."
        self.quit()


def quit():
    global powermeter
    powermeter.quit()
