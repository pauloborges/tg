# coding: utf-8

from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
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
