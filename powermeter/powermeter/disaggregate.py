# coding: utf-8

import math
import json
from collections import deque

from powermeter.command import Command
from powermeter.util import enum
from powermeter import qt

import subprocess
import time

from sklearn.neighbors import KNeighborsClassifier


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

    EV_THRESHOLD = 0.03
    EV_THRESHOLD_MIN = 5.0

    THRESHOLD = 0.5
    THRESHOLD_MIN = 5.0

    def __init__(self, **kwargs):
        self.status = self.STATUS.INIT
        self.signature_file = kwargs["signature_file"]

        self.first_transition_sample = True

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
        self.sign_plot = self.build_plot("VAr", "W",
            title=u"Possíveis transições")
        self.sign_scatter = qt.scatter(unicolor=True)
        self.sign_plot.addItem(self.sign_scatter)

        self.next_row()

        self.power_plot = self.build_plot("VAr", "W",
            title=u"Tempo real")
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

        self.monitor = subprocess.Popen("./monitor agregate 60",
                            stdout=subprocess.PIPE, shell=True)

        self.current_status = {
            appliance: "OFF" for appliance in self.signatures.keys()
        }
        self.update_status_text()
        self.update_classifier()

        self.status = self.STATUS.OFF_COLLECTING

    def status_off_collecting(self):
        print "inicializando..."
        for i in xrange(2, 0, -1):
            print i
            self.monitor.stdout.readline()

        data = self.unpack_line(self.monitor.stdout.readline())
        self.curr_real = data[3]
        self.curr_reac = data[4]

        self.status = self.STATUS.COLLECTING

    def status_collecting(self):
        data = self.unpack_line(self.monitor.stdout.readline())

        new_real = data[3]
        new_reac = data[4]

        v_real = new_real - self.curr_real
        v_reac = new_reac - self.curr_reac

        print "C: (%.3f, %.3f) N: (%.3f, %.3f) V: (%.3f, %.3f)" % (
            self.curr_real, self.curr_reac,
            new_real, new_reac,
            v_real, v_reac)

        # if self.new_transition(new_real, new_reac):
        if self.process_new_transition(v_real, v_reac):
            self.curr_real = new_real
            self.curr_reac = new_reac

            self.update_status_text()
            self.update_classifier()

        print ''

        # Plot power scatter
        self.real_power_data.append(new_real)
        self.reac_power_data.append(new_reac)

        l = len(self.real_power_data)

        self.power_scatter.setData(
                    self.real_power_data, self.reac_power_data,
                    brush=self.power_scatter_brushes[-l:])

        self.power_plot.setXRange(0, max(self.real_power_data))
        self.power_plot.setYRange(0, max(self.reac_power_data))

        
        # Plot signature scatter
        sign_real, sign_reac = zip(*self.classifier_instances)

        min_real, max_real = min(sign_real), max(sign_real)
        min_reac, max_reac = min(sign_reac), max(sign_reac)

        min_real = min(min_real, v_real)
        max_real = max(max_real, v_real)
        min_reac = min(min_reac, v_reac)
        max_reac = max(max_reac, v_reac)

        self.sign_plot.clear()
        self.sign_plot.addItem(self.sign_scatter)
        self.sign_scatter.setData(
                    pos=self.classifier_instances,
                    brush=qt.brush(255, 255, 255, 255),
                    size=5)
        for text in self.classifier_texts:
            self.sign_plot.addItem(text)
        self.sign_scatter.addPoints(pos=[[v_real, v_reac]],
                    brush=qt.brush(255, 0, 0, 255),
                    size=5)
        self.sign_plot.setXRange(min_real, max_real)
        self.sign_plot.setYRange(min_reac, max_reac)

    def process_new_transition(self, vreal, vreac):
        ev_th_real, ev_th_reac = self.calc_ev_threshold()

        print "  Event threshold: (%.3f, %.3f)" % (
            ev_th_real, ev_th_reac)

        if abs(vreal) < ev_th_real and (
                            abs(vreac) < ev_th_reac):
            return False

        if self.first_transition_sample:
            self.first_transition_sample = False
            return False
        self.first_transition_sample = True

        dist, ind = self.classifier.kneighbors([vreal, vreac],
                                        return_distance=True)
        appliance, state = self.classifier_labels[ind]

        print "  New event detected"
        print "  Nearest signature: %s/%s [%.3f]" % (
                                    appliance, state, dist[0, 0])

        var_threshold = self.calc_var_threshold(
                                vreal, vreac)
        if dist > var_threshold:
            print "  Dist > threshold: %s" % var_threshold
            return False

        print "  %s: %s --> %s" % (
                    appliance, self.current_status[appliance],
                    state)

        self.current_status[appliance] = state

        return True


    def calc_ev_threshold(self):
        t_real = abs(self.curr_real * self.EV_THRESHOLD)
        t_reac = abs(self.curr_reac * self.EV_THRESHOLD)

        if t_real < self.EV_THRESHOLD_MIN:
            t_real = self.EV_THRESHOLD_MIN
        if t_reac < self.EV_THRESHOLD_MIN:
            t_reac = self.EV_THRESHOLD_MIN

        return t_real, t_reac

    def calc_var_threshold(self, var_real, var_reac):
        t_real = abs(var_real * self.THRESHOLD)
        t_reac = abs(var_reac * self.THRESHOLD)

        if t_real < self.THRESHOLD_MIN:
            t_real = self.THRESHOLD_MIN
        if t_reac < self.THRESHOLD_MIN:
            t_reac = self.THRESHOLD_MIN
            print t_reac

        return math.sqrt(t_real**2 + t_reac**2)

    def new_transition(self, real, reac):
        # dist, ind = self.classifier.kneighbors([real, reac],
        #                             return_distance=True)

        # print dist, ind

        # threshold = self.calc_margin(5, self.curr_real,
        #                                 self.curr_reac)
        # if dist > threshold:
        #     return False
        
        # appliance, state = self.classifier_labels[ind]
        # self.current_status[appliance] = state

        # self.curr_real = real
        # self.curr_reac = reac

        # return True
        return False

        # WINDOW = 5

        # v_real = real - self.curr_real
        # v_reac = reac - self.curr_reac

        # x_margin, y_margin = self.calc_margin(WINDOW,
        #                         self.curr_real, self.curr_reac)

        # print "    Var: (%.2f, %.2f) [margin: (%.2f, %.2f)]" % (
        #     v_real, v_reac, x_margin, y_margin)

        # if abs(v_real) < x_margin and abs(v_reac) < y_margin:
        #     return False

        # print "    Transition detected"

        # found = False
        # for appliance, data in self.signatures.iteritems():
        #     possible_transitions = [
        #         t for t in data["transitions"]
        #         if t[0] == self.current_status[appliance]
        #         or t[1] == self.current_status[appliance]
        #     ]

        #     for signature in possible_transitions:
        #         if self.match_signature(WINDOW,
        #                             v_real, v_reac, *signature[2]):
        #             self.print_transition(appliance,
        #                             signature[0], signature[1])
        #             self.current_status[appliance] = signature[1]
        #             found = True
        #             break
        #         elif self.match_signature(WINDOW,
        #                             -v_real, -v_reac, *signature[2]):
        #             self.print_transition(appliance,
        #                             signature[1], signature[0])
        #             self.current_status[appliance] = signature[0]
        #             found = True
        #             break

        #     if found:
        #         break

        # if found:
        #     self.curr_real = real
        #     self.curr_reac = reac
        #     return True

        # print "    Unknown transition"
        # return False

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

        # return x_margin, y_margin
        return math.sqrt(x_margin**2 + y_margin**2)

    def update_classifier(self):
        self.classifier_instances = []
        self.classifier_labels = []
        self.classifier_texts = []

        for appliance, data in self.signatures.iteritems():
            self.classifier_instances.extend([
                t[2] if t[0] == self.current_status[appliance]
                else [-t[2][0], -t[2][1]]
                for t in data["transitions"]
                if t[0] == self.current_status[appliance]
                or t[1] == self.current_status[appliance]
            ])

            self.classifier_labels.extend([
                (appliance,
                t[0] if t[1] == self.current_status[appliance]
                else t[1])
                for t in data["transitions"]
                if t[0] == self.current_status[appliance]
                or t[1] == self.current_status[appliance]
            ])

            self.classifier_texts.extend([
                qt.text(appliance + '/' + label, anchor=(0, 0.5))
                for app, label in self.classifier_labels
                if app == appliance
            ])

        for i, text in enumerate(self.classifier_texts):
            text.setPos(*self.classifier_instances[i])

        self.classifier_classes = range(
                                len(self.classifier_instances))

        self.classifier = KNeighborsClassifier(n_neighbors=1)
        self.classifier.fit(self.classifier_instances,
                            self.classifier_classes)
