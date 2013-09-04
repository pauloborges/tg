# coding: utf-8

from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
import numpy as np
import functools

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
    return pg.ScatterPlotItem(size=10, pen=pg.mkPen(None))#,
            #brush=pg.mkBrush(255, 255, 255, 120))

def mk_brushes(size, r, g, b):
    return [pg.mkBrush(r, g, b, int(a))
        for a in np.linspace(0, 255, size-1)] + [
            pg.mkBrush(255, 0, 0, 255)]
