# coding: utf-8

from collections import deque
import subprocess
import time
import json
import sys

import numpy as np
# import scipy.cluster.hierarchy as hcluster
from sklearn.cluster import MiniBatchKMeans
from collections import Counter

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
                    self.real_power_data, self.reac_power_data,
                    size=10)

        if data[3] > self.x_range:
            self.x_range = data[3]
            self.power_plot.setXRange(0, self.x_range)
        if data[4] > self.y_range:
            self.y_range = data[4]
            self.power_plot.setYRange(0, self.y_range)

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
        self.spinbox_cluster.setValue(1)

        self.button_tag = qt.button(text=u"Taggear")
        self.button_tag.clicked.connect(self.button_tag_clicked)
        self.button_tag.setEnabled(False)

        self.button_sign = qt.button(text=u"Assinaturas")
        self.button_sign.clicked.connect(self.button_sign_clicked)
        self.button_sign.setEnabled(False)

        self.button_save = qt.button(text=u"Salvar")
        self.button_save.clicked.connect(self.button_save_clicked)
        self.button_save.setEnabled(False)

        self.cfgwin = qt.build_widget()
        self.cfgwin.layout().addWidget(self.button_start, 0, 0, 1, 2)
        self.cfgwin.layout().addWidget(self.button_stop, 1, 0, 1, 2)
        self.cfgwin.layout().addWidget(self.button_cluster, 2, 0)
        self.cfgwin.layout().addWidget(self.spinbox_cluster, 2, 1)
        self.cfgwin.layout().addWidget(self.button_tag, 3, 0, 1, 2)
        self.cfgwin.layout().addWidget(self.button_sign, 4, 0, 1, 2)
        self.cfgwin.layout().addWidget(self.button_save, 5, 0, 1, 2)
        self.cfgwin.show()

    def button_start_clicked(self):
        self.button_start.setEnabled(False)
        self.button_stop.setEnabled(True)

        self.appliance_name = qt.input_dialog(
                                    "Nome do equipamento", "")
        self.power_plot.setTitle(self.appliance_name)

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
        self.button_tag.setEnabled(True)

    def clusterize(self):
        X = np.ndarray((len(self.real_power_data), 2))
        X[:, 0] = self.real_power_data
        X[:, 1] = self.reac_power_data

        clustering = MiniBatchKMeans(self.spinbox_cluster.value())
        clustering.fit(X)

        # Identifica os centróides dos clusteres
        centroids = clustering.cluster_centers_.tolist()

        # Conta quantos elementos cada cluster possui
        predictions = clustering.predict(X)
        occurrences = Counter(predictions)

        # Identifica os clusteres que possuem somente 1 elemento
        # (serão tratados como clusteres de transição)
        transition_clusters = [k for k, v in occurrences.iteritems()
                                if v < 2]

        # Remove os centróides de clusteres de transição
        centroids = [e for i, e in enumerate(centroids)
                        if i not in transition_clusters]

        predictions = [-1 if v in transition_clusters else v
                        for v in predictions]
        
        self.prototypes = centroids
        self.plot_clusterized(predictions)

    def plot_clusterized(self, predictions):
        self.power_scatter.setData(
                    self.real_power_data, self.reac_power_data,
                    brush=qt.mk_colored_brushes(100, predictions),
                    size=10)

        self.power_scatter.addPoints(pos=self.prototypes,
            brush=qt.brush(255, 255, 255, 255), size=7)

    def button_tag_clicked(self):
        self.labels = []

        arrow = qt.arrow(angle=-160, tipAngle=60,
                            headLen=40, tailLen=40, tailWidth=20,
                            pen={'color': 'w', 'width': 3})
        self.power_plot.addItem(arrow)

        try:
            for i, prototype in enumerate(self.prototypes):
                arrow.setPos(prototype[0]-0.2, prototype[1]+0.2)
                qt.update_gui()

                current_state = qt.input_dialog("Nome do estado", "")
                self.labels.append(current_state)

                text = qt.text(current_state, anchor=(0.5, 0))
                text.setPos(prototype[0], prototype[1]-0.5)
                self.power_plot.addItem(text)
        except qt.UserCancelError:
            return
        
        self.power_plot.removeItem(arrow)

        self.button_cluster.setEnabled(False)
        self.button_tag.setEnabled(False)
        self.button_sign.setEnabled(True)

    def button_sign_clicked(self):
        pass

    def button_save_clicked(self):
        self.button_save.setEnabled(False)
