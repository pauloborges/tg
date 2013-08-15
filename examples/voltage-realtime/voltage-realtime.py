#!/usr/bin/env python
# coding: utf-8

"""
Esse programa plota um gráfico em tempo real contendo a tensão atual.

Para funcionar corretamente, o computador deve estar conectado pelo USB
a um Arduino Due com o firmware './voltage-realtime.ino'.
"""

import sys
sys.path.append("..")

import collections
import random
import utils

BAUD_RATE = "115200"
arduino = utils.init_arduino(BAUD_RATE)

WIN_SIZE = (1000, 600)
win = utils.init_win(*WIN_SIZE)

Y_MAX = 4095
X_MAX = 100

###############################################################################
#	Gráficos
###############################################################################
rt_plt = win.addPlot()
rt_plt.setLabel("left", u"Tensão", units='V')
rt_plt.setLabel("bottom", u"Amostra")
rt_plt.setYRange(0, Y_MAX)
rt_plt.setXRange(0, X_MAX-1)

rt_curve = rt_plt.plot()

win.nextRow()

plt = win.addPlot()
plt.setLabel("left", u"Tensão", units='V')
plt.setLabel("bottom", u"Amostra")
plt.setYRange(0, Y_MAX)
plt.setXRange(0, X_MAX-1)

rt_data = collections.deque(maxlen=X_MAX)
rms_data = collections.deque(maxlen=X_MAX)
count = 0

def update_rms_voltage():
	pass

def update_rt_voltage():
	try:
		value = int(arduino.readline())
		rt_data.append(value)
		rt_curve.setData(rt_data)

		global count
		count = (count + 1) % X_MAX
		if not count:
			update_rms_voltage()

	except ValueError:
		pass

tmr = utils.init_timer(update_rt_voltage)
tmr.start(0)

if __name__ == '__main__':
	utils.init_app()
