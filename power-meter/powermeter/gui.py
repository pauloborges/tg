# coding: utf-8

from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
import functools

app = None
win = None

def init(size, title=None):
	global app, win
	app = QtGui.QApplication([])
	win = pg.GraphicsWindow()
	win.resize(*size)
	win.setWindowTitle(title)
	return app, win

def timer(func, msec, **kwargs):
	foo = functools.partial(func, **kwargs)
	timer = QtCore.QTimer()
	timer.timeout.connect(foo)
	timer.start(msec)
	return timer

def single_shot(func, **kwargs):
	foo = functools.partial(func, **kwargs)
	QtCore.QTimer.singleShot(0, foo)
