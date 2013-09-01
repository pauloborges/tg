# coding: utf-8

from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
import functools

app = None

def init(size):
    global app
    app = QtGui.QApplication([])

    win = pg.GraphicsWindow()
    win.resize(*size)

    return app, win


def quit():
    app.quit()


def timer(func, **kwargs):
    foo = functools.partial(func, **kwargs)

    timer = QtCore.QTimer()
    timer.timeout.connect(foo)

    return timer


def single_shot(func, **kwargs):
    foo = functools.partial(func, **kwargs)
    QtCore.QTimer.singleShot(10, foo)



# --------------------------------------------------------

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


def gui(size):
    win = pg.GraphicsWindow()
    win.resize(*size)

    return win