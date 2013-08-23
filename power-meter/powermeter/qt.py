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
