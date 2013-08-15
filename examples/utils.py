# coding: utf-8

from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
import serial
import sys
import os

app = None

def init_arduino(baud):
	devices = os.listdir("/dev")
	device = next(dev for dev in devices if dev.startswith("ttyACM"))
	SERIAL_PORT = os.path.join("/dev", device)

	print "Comunicação serial para %s com %s bps" % (SERIAL_PORT, baud)
	return serial.Serial(SERIAL_PORT, baud)


def init_win(width, height, title=None):
	global app
	app = QtGui.QApplication([])

	win = pg.GraphicsWindow(title=title)
	win.resize(width, height)

	return win


def init_app():
	app.exec_()


def init_timer(func):
	tmr = QtCore.QTimer()
	tmr.timeout.connect(func)

	return tmr
