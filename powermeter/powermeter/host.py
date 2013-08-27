# coding: utf-8

from powermeter import qt
from powermeter.monitor import Monitor
#from powermeter.calibrate import Calibrate
#from powermeter.disagregate import Disagregate

__all__ = ("PowerMeter")


def build_command(command, **kwargs):
    command = command.capitalize()

    if command not in globals():
        raise ValueError("Command '%s' not found" % command)

    return globals()[command](**kwargs)


class PowerMeter(object):
    def __init__(self):
        pass

    @classmethod
    def initialize(cls, **kwargs):
        try:
            command = kwargs.pop("command")
        except KeyError:
            raise ValueError("Missing 'command' argument")

        powermeter = PowerMeter()
        powermeter.command = build_command(command, **kwargs)

        return powermeter

    def run(self):
        app = qt.initialize()
        qt.idle_loop(self.command.run)

        return app.exec_()
