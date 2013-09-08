# coding: utf-8

import json
from collections import deque

from powermeter.command import Command
from powermeter.util import enum
from powermeter import qt

import subprocess
import time


__all__ = ("Disaggregate")

class Disaggregate(Command):
    ARGS = ("signature_file",)

    def __init__(self, **kwargs):
        self.check_args(kwargs.keys(), self.ARGS)
        self.option = DisaggregateOption(**kwargs)

    def run(self):
        self.option.run()

    def sigint_handler(self):
        self.option.sigint_handler()


class DisaggregateOption(object):
    WIN_SIZE = (1000, 600)
    STATUS = enum("INIT", "OFF_COLLECTING", "COLLECTING")
    POWER_SIZE_LEN = 10

    def __init__(self, **kwargs):
        self.status = self.STATUS.INIT
        self.signature_file = kwargs["signature_file"]

    def init(self):
        self.win = qt.gui(self.WIN_SIZE)

    def run(self):
        getattr(self, "status_"
                + self.STATUS.reverse[self.status].lower())()

    def build_plot(self, y_unit=None, x_unit=None,
                    y_range=None, x_range=None, **kwargs):
        plot = self.win.addPlot(**kwargs)

        plot.hideButtons()
        plot.setMenuEnabled(False)
        plot.showGrid(True, True, 0.2)

        if y_unit:
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

    def sigint_handler(self):
        if self.monitor is not None:
            self.monitor.terminate()

    def build_gui(self):
        self.power_plot = self.build_plot("VAr", "W",
            title=u"Potência real vs potência reativa")
        self.power_scatter = qt.scatter(unicolor=True)
        self.power_plot.addItem(self.power_scatter)

        self.reac_power_data = deque(maxlen=self.POWER_SIZE_LEN)
        self.real_power_data = deque(maxlen=self.POWER_SIZE_LEN)

        self.power_scatter_brushes = qt.mk_brushes(
                            self.POWER_SIZE_LEN, 255, 255, 255)

        self.status_text = qt.text("", anchor=(0.0, 1.0))
        self.status_text.setPos(0, 0)
        self.power_plot.addItem(self.status_text)

    def update_status_text(self):
        self.status_text.setText(
            "\n".join([name + ": " + status
                    for name, status
                        in self.current_status.iteritems()])
        )

    def status_init(self):
        self.init()
        self.build_gui()

        with open(self.signature_file, 'r') as f:
            self.signatures = json.loads(f.read())

        self.monitor = subprocess.Popen("./monitor agregate 30",
                            stdout=subprocess.PIPE, shell=True)

        self.current_status = {
            appliance: "OFF" for appliance in self.signatures.keys()
        }
        self.update_status_text()

        self.status = self.STATUS.OFF_COLLECTING

    def status_off_collecting(self):
        text = qt.text("inicializando", anchor=(0.5, 0))
        text.setPos(0.5, 0.5)
        self.power_plot.addItem(text)
        qt.update_gui()

        for i in xrange(5):
            self.monitor.stdout.readline()

        data = self.unpack_line(self.monitor.stdout.readline())
        self.curr_real = data[3]
        self.curr_reac = data[4]

        self.power_plot.removeItem(text)
        self.status = self.STATUS.COLLECTING

    def status_collecting(self):
        data = self.unpack_line(self.monitor.stdout.readline())
        
        self.real_power_data.append(data[3])
        self.reac_power_data.append(data[4])
        l = len(self.real_power_data)

        self.power_scatter.setData(
                    self.real_power_data, self.reac_power_data,
                    brush=self.power_scatter_brushes[-l:])

        self.power_plot.setXRange(0, max(self.real_power_data))
        self.power_plot.setYRange(0, max(self.reac_power_data))

        new_real = data[3]
        new_reac = data[4]

        print "New: %s Current: %s" % (
            (new_real, new_reac), (self.curr_real, self.curr_reac))

        if self.new_transition(new_real, new_reac):
            self.update_status_text()

    def new_transition(self, real, reac):
        WINDOW = 5

        v_real = real - self.curr_real
        v_reac = reac - self.curr_reac

        x_margin, y_margin = self.calc_margin(WINDOW,
                                self.curr_real, self.curr_reac)

        print "    Var: (%.2f, %.2f) [margin: (%.2f, %.2f)]" % (
            v_real, v_reac, x_margin, y_margin)

        if abs(v_real) < x_margin and abs(v_reac) < y_margin:
            return False

        print "    Transition detected"

        found = False
        for appliance, data in self.signatures.iteritems():
            possible_transitions = [
                t for t in data["transitions"]
                if t[0] == self.current_status[appliance]
                or t[1] == self.current_status[appliance]
            ]

            for signature in possible_transitions:
                if self.match_signature(WINDOW,
                                    v_real, v_reac, *signature[2]):
                    self.print_transition(appliance,
                                    signature[0], signature[1])
                    self.current_status[appliance] = signature[1]
                    found = True
                    break
                elif self.match_signature(WINDOW,
                                    -v_real, -v_reac, *signature[2]):
                    self.print_transition(appliance,
                                    signature[1], signature[0])
                    self.current_status[appliance] = signature[0]
                    found = True
                    break

            if found:
                break

        if found:
            self.curr_real = real
            self.curr_reac = reac
            return True

        print "    Unknown transition"
        return False

    def match_signature(self, w, x1, y1, x2, y2):
        x_margin, y_margin = self.calc_margin(w, x2, y2)

        if abs(x1 - x2) < x_margin and abs(y1 - y2) < y_margin:
            return True
        return False

    def print_transition(self, appliance, old_state, new_state):
        print "    %s: %s --> %s" % (appliance, old_state, new_state)

    def calc_margin(self, w, x, y):
        x_margin = abs(x * 0.01)
        y_margin = abs(y * 0.01)

        if x_margin < w:
            x_margin = w

        if y_margin < w:
            y_margin = w

        return x_margin, y_margin