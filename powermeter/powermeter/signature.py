# coding: utf-8

from collections import deque
import subprocess
import time
import json
import sys

import numpy as np
import scipy.cluster.hierarchy as hcluster

from powermeter.command import Command
from powermeter.util import enum
from powermeter import qt

__all__ = ("Signature")

class Signature(Command):
    OPTIONS = ("new", "remove", "list", "show")
    ARGS = ("signature_file",)

    def __init__(self, **kwargs):
        option = kwargs.pop("option", None)
        super(Signature, self).__init__(option, self.OPTIONS)

        self.check_args(kwargs.keys(), self.ARGS)

        if option == "new":
            self.option = SignatureNewOption(**kwargs)
        elif option == "remove":
            self.option = SignatureRemoveOption(**kwargs)
        elif option == "list":
            self.option = SignatureListOption(**kwargs)
        else:
            self.option = SignatureShowOption(**kwargs)

    def run(self):
        self.option.run()

    def sigint_handler(self):
        self.option.sigint_handler()


class SignatureOption(object):
    WIN_SIZE = (1000, 600)
    STATUS = enum("INIT", "COLLECTING")
    POWER_SIZE_LEN = 20

    def __init__(self, **kwargs):
        self.status = self.STATUS.INIT

        try:
            with open(kwargs["signature_file"], 'r') as f:
                self.signatures = json.loads(f.read())
        except IOError:
            self.signatures = {}

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


class SignatureNewOption(SignatureOption):
    STATUS = enum("INIT", "WAIT", "COLLECTING")

    def status_init(self):
        super(SignatureNewOption, self).init()
        self.build_gui()

        self.x_range = 0
        self.y_range = 0

        self.status = self.STATUS.WAIT

    def sigint_handler(self):
        if self.monitor is not None:
            self.monitor.terminate()

    def status_wait(self):
        time.sleep(0.05)

    def status_collecting(self):
        data = self.unpack_line(self.monitor.stdout.readline())

        self.real_power_data.append(data[3])
        self.reac_power_data.append(data[4])
        l = len(self.real_power_data)

        self.power_scatter.setData(
                    self.real_power_data, self.reac_power_data)

        if data[3] > self.x_range:
            self.x_range = data[3]
            self.power_plot.setXRange(0, self.x_range)
        if data[4] > self.y_range:
            self.y_range = data[4]
            self.power_plot.setYRange(0, self.y_range)

        self.process_data(data[3], data[4])

    def build_gui(self):
        self.power_plot = self.build_plot("VAr", "W",
            title=u"Potência real vs potência reativa")
        self.power_scatter = qt.scatter(unicolor=True)
        self.power_plot.addItem(self.power_scatter)

        self.reac_power_data = deque()
        self.real_power_data = deque()

        # Config window
        self.button_start = qt.button(text=u"Iniciar")
        self.button_start.clicked.connect(self.button_start_clicked)

        self.button_stop = qt.button(text=u"Parar")
        self.button_stop.clicked.connect(self.button_stop_clicked)
        self.button_stop.setEnabled(False)

        self.button_cluster = qt.button(text=u"Cluster")
        self.button_cluster.clicked.connect(
                                    self.button_cluster_clicked)
        self.button_cluster.setEnabled(False)
        self.spinbox_cluster = qt.spinbox()

        self.button_tag = qt.button(text=u"Taggear")
        self.button_tag.clicked.connect(self.button_tag_clicked)
        self.button_tag.setEnabled(False)

        self.button_save = qt.button(text=u"Salvar")
        self.button_save.clicked.connect(self.button_save_clicked)
        self.button_save.setEnabled(False)

        self.cfgwin = qt.build_widget()
        self.cfgwin.layout().addWidget(self.button_start, 0, 0, 1, 2)
        self.cfgwin.layout().addWidget(self.button_stop, 1, 0, 1, 2)
        self.cfgwin.layout().addWidget(self.button_cluster, 2, 0)
        self.cfgwin.layout().addWidget(self.spinbox_cluster, 2, 1)
        self.cfgwin.layout().addWidget(self.button_tag, 3, 0, 1, 2)
        self.cfgwin.layout().addWidget(self.button_save, 4, 0, 1, 2)
        self.cfgwin.show()

    def process_data(self, real, reac):
        pass

    def button_start_clicked(self):
        self.button_start.setEnabled(False)
        self.button_stop.setEnabled(True)

        self.monitor = subprocess.Popen("./monitor agregate 60",
                            stdout=subprocess.PIPE, shell=True)

        self.status = self.STATUS.COLLECTING

    def button_stop_clicked(self):
        if self.monitor is not None:
            self.monitor.terminate()
        
        self.button_stop.setEnabled(False)
        self.button_cluster.setEnabled(True)

        self.status = self.STATUS.WAIT

    def button_cluster_clicked(self):
        self.clusterize()

    def clusterize(self):
        X = np.ndarray((len(self.real_power_data), 2))
        X[:, 0] = self.real_power_data
        X[:, 1] = self.reac_power_data

        clusters = hcluster.fclusterdata(X,
            self.spinbox_cluster.value(),
            criterion="maxclust",
            metric="euclidean",
            depth=1,
            method="single"
        )

        for n in xrange(X.shape[0]):
            print X[n, :], clusters[n]

        self.plot_clusterized(clusters)

    def plot_clusterized(self, clusters):
        self.power_scatter.setData(
                    self.real_power_data, self.reac_power_data,
                    brush=qt.mk_colored_brushes(150, clusters))

    def button_tag_clicked(self):
        pass

    def button_save_clicked(self):
        pass
