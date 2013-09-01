# coding: utf-8

from collections import deque
import subprocess
import time

from powermeter.command import Command
from powermeter.util import enum
from powermeter import qt

__all__ = ("Visualizer")

class Visualize(Command):
    OPTIONS = ("raw", "instantaneous", "agregate")
    ARGS = ("input_fd",)

    def __init__(self, **kwargs):
        option = kwargs.pop("option", None)
        super(Visualize, self).__init__(option, self.OPTIONS)

        self.check_args(kwargs.keys(), self.ARGS)

        if option == "raw":
            self.option = VisualizeRaw(**kwargs)
        elif option == "instantaneous":
            self.option = VisualizeInstantaneous(**kwargs)
        else:
            self.option = VisualizeAgregate(**kwargs)

    def run(self):
        self.option.run()

    def sigint_handler(self):
        self.option.sigint_handler()


class VisualizeOption(object):
    WIN_SIZE = (1000, 600)
    STATUS = enum("INIT", "DRAWING")
    DATA_SIZE_LEN = 100

    VOLTAGE_RANGE = (-400, 400)
    CURRENT_RANGE = (-30, 30)
    REAL_POWER_RANGE = (0, 7000)

    RMS_VOLTAGE_RANGE = (160, 300)
    RMS_CURRENT_RANGE = (0, 5)

    TOTAL_POWER_RANGE = (0, 7000)
    REAC_POWER_RANGE = (0, 7000)
    POWER_FACTOR_RANGE = (0.0, 1.0)

    def __init__(self, **kwargs):
        self.status = self.STATUS.INIT
        self.input_file = kwargs["input_fd"]

    def init(self):
        self.win = qt.gui(self.WIN_SIZE)

    def run(self):
        """Run the function with same name as current status."""
        getattr(self, "status_"
                + self.STATUS.reverse[self.status].lower())()

    def sigint_handler(self):
        self.input_file.close()

    def build_plot(self, title, y_unit, x_unit=None,
                    y_range=None, x_range=None, col=1):
        plot = self.win.addPlot(colspan=col, title=title)

        plot.hideButtons()
        plot.setMenuEnabled(False)
        plot.showGrid(True, True, 0.2)

        plot.setLabel("left", units=y_unit)
        if x_unit:
            plot.setLabel("bottom", units=x_unit)
        if y_range:
            plot.setYRange(*y_range)
        if x_range:
            plot.setXRange(*x_range)

        return plot

    def next_row(self):
        self.win.nextRow()

    def unpack_line(self, line):
        return tuple(float(x) for x in line.split())


class VisualizeRaw(VisualizeOption):
    def status_init(self):
        super(VisualizeRaw, self).init()
        self.build_gui()

        # self.subproc = subprocess.Popen("python -m "
        #     "powermeter.core monitor raw 60".split(),
        #     stdout=subprocess.PIPE
        # )

        self.status = self.STATUS.DRAWING

    def status_drawing(self):
        data = self.unpack_line(self.input_file.readline())
        
        if self.samples:
            self.samples.append(self.samples[-1]+1)
        else:
            self.samples.append(1)

        self.voltage_data.append(data[0])
        self.current_data.append(data[1])
        self.real_power_data.append(data[2])

        self.voltage_curve.setData(self.samples, self.voltage_data)
        self.current_curve.setData(self.samples, self.current_data)
        self.real_power_curve.setData(self.samples,
                                        self.real_power_data)

    def build_gui(self):
        self.voltage_plot = self.build_plot(u"Tensão", "V",
                            y_range=self.VOLTAGE_RANGE)
        self.voltage_curve = self.voltage_plot.plot()
        self.voltage_data = deque(maxlen=self.DATA_SIZE_LEN)

        self.next_row()

        self.current_plot = self.build_plot(u"Corrente", "A",
                            )#y_range=self.CURRENT_RANGE)
        self.current_curve = self.current_plot.plot()
        self.current_data = deque(maxlen=self.DATA_SIZE_LEN)

        self.next_row()

        self.real_power_plot = self.build_plot(u"Potência real", "W"
                            )#, y_range=self.REAL_POWER_RANGE)
        self.real_power_curve = self.real_power_plot.plot()
        self.real_power_data = deque(maxlen=self.DATA_SIZE_LEN)

        self.samples = deque(maxlen=self.DATA_SIZE_LEN)


class VisualizeInstantaneous(VisualizeOption):
    def status_init(self):
        super(VisualizeInstantaneous, self).init()
        self.build_gui()
        self.status = self.STATUS.DRAWING

    def status_drawing(self):
        data = self.unpack_line(self.input_file.readline())
        
        self.elapsed.append(data[0])
        self.voltage_data.append(data[1])
        self.current_data.append(data[2])
        self.real_power_data.append(data[3])

        self.voltage_curve.setData(self.elapsed, self.voltage_data)
        self.current_curve.setData(self.elapsed, self.current_data)
        self.real_power_curve.setData(self.elapsed,
                                        self.real_power_data)

    def build_gui(self):
        self.voltage_plot = self.build_plot(u"Tensão", "V", "s",
                            y_range=self.VOLTAGE_RANGE)
        self.voltage_curve = self.voltage_plot.plot()
        self.voltage_data = deque(maxlen=self.DATA_SIZE_LEN)

        self.next_row()

        self.current_plot = self.build_plot(u"Corrente", "A", "s",
                            )#y_range=self.CURRENT_RANGE)
        self.current_curve = self.current_plot.plot()
        self.current_data = deque(maxlen=self.DATA_SIZE_LEN)

        self.next_row()

        self.real_power_plot = self.build_plot(u"Potência real", "W",
                            "s")#, y_range=self.REAL_POWER_RANGE)
        self.real_power_curve = self.real_power_plot.plot()
        self.real_power_data = deque(maxlen=self.DATA_SIZE_LEN)

        self.elapsed = deque(maxlen=self.DATA_SIZE_LEN)


class VisualizeAgregate(VisualizeOption):
    def status_init(self):
        super(VisualizeAgregate, self).init()
        self.build_gui()
        self.status = self.STATUS.DRAWING

    def status_drawing(self):
        print self.input_file.readline(),

    def build_gui(self):
        self.rms_voltage_plot = self.build_plot(
            u"Tensão RMS", "V", "s", y_range=self.RMS_VOLTAGE_RANGE)
        self.rms_voltage_curve = self.rms_voltage_plot.plot()
        self.rms_voltage_data = deque(maxlen=self.DATA_SIZE_LEN)

        self.next_row()

        self.rms_current_plot = self.build_plot(
            u"Corrente RMS", "A", "s", y_range=self.RMS_CURRENT_RANGE)
        self.rms_current_curve = self.rms_current_plot.plot()
        self.current_data = deque(maxlen=self.DATA_SIZE_LEN)

        # TODO....
