#!/usr/bin/env python
# coding: utf-8

"""
Esse programa funciona como um HOST para o medidor de energia.

Para funcionar corretamente, o computador deve estar conectado pelo USB
a um Arduino Due com o firmware './power-meter.ino'.
"""

import sys
sys.path.append("..")

import collections
import random
import utils

BAUD_RATE = "115200"
arduino = utils.init_arduino(BAUD_RATE)

WIN_SIZE = (1000, 600)
win = utils.init_win(*WIN_SIZE, title=u"Medidor de energia")

MAX_NUM_SAMPLES = 200

###############################################################################
# Gráficos
###############################################################################
RMS_V_MIN, RMS_V_MAX = 0, 400

rms_v_plt = win.addPlot()
rms_v_plt.showGrid(True, True)
rms_v_plt.setLabel("left", u"Tensão RMS", units='V')
rms_v_plt.setLabel("bottom", u"Amostra")
rms_v_plt.setYRange(RMS_V_MIN, RMS_V_MAX)
rms_v_plt.setXRange(0, MAX_NUM_SAMPLES-1)

rms_v_curve = rms_v_plt.plot()

# win.nextRow()

rms_v_data = collections.deque(maxlen=MAX_NUM_SAMPLES)

def update_power_meter():
    try:
        rms_v, rms_i, real_power = (float(x) for x in arduino.readline().split('#'))

        print rms_v
        rms_v_data.append(rms_v)
        rms_v_curve.setData(rms_v_data)

    except ValueError:
        pass

tmr = utils.init_timer(update_power_meter)
tmr.start(0)

if __name__ == '__main__':
    utils.init_app()
