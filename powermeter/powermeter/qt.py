# coding: utf-8

from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
import numpy as np
import functools
import random

def quit():
    global app
    app.quit()

def initialize():
    global app
    app = QtGui.QApplication([])
    QtCore.pyqtRemoveInputHook()
    return app


def idle_loop(function):
    global loop # must store a persistent reference to the timer
    loop = QtCore.QTimer()
    loop.timeout.connect(function)
    loop.start(0)

# def gui(size):
#     win = pg.GraphicsWindow()
#     win.resize(*size)

#     return win

def gui(size):
    global view, layout
    view = pg.GraphicsView()
    layout = pg.GraphicsLayout()

    view.setCentralItem(layout)
    view.resize(*size)

    view.show()

    return layout

def scatter(**kwargs):
    if "unicolor" in kwargs:
       return pg.ScatterPlotItem(size=10, pen=pg.mkPen(None),
            brush=pg.mkBrush(255, 255, 255, 50)) 

    return pg.ScatterPlotItem(size=10, pen=pg.mkPen(None))

def mk_brushes(size, r, g, b):
    return [pg.mkBrush(r, g, b, int(a))
        for a in np.linspace(0, 255, size-1)] + [
            pg.mkBrush(255, 0, 0, 255)]

def build_widget():
    w = QtGui.QWidget()
    layout = QtGui.QGridLayout()
    w.setLayout(layout)
    return w

def button(**kwargs):
    return QtGui.QPushButton(**kwargs)

def spinbox():
    return QtGui.QDoubleSpinBox()

def label(text):
    return QtGui.QLabel(text=text)

def mk_colored_brushes(alpha, colors):
    color_table = gen_colors(colors, alpha)
    return [color_table[c] for c in colors]

def gen_colors(indexes, alpha):
    indexes = set(indexes)

    return {
        i: pg.mkBrush(
            i == 0 and 255 or random.randint(0, 255),
            i == 0 and 255 or random.randint(0, 255),
            i == 0 and 255 or random.randint(0, 255),
            i == 0 and 50 or alpha
        ) 
        for i in indexes
    }

def brush(r, g, b, a):
    return pg.mkBrush(r, g, b, a)
