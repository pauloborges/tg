#!/usr/bin/env python
# coding: utf-8

"""
Esse programa funciona como um HOST para o medidor de energia.

Para funcionar corretamente, o computador deve estar conectado pelo USB
a um Arduino Due com o firmware './power-meter.ino'.
"""

# import sys
# sys.path.append("..")

# import collections
# import random
# import utils

# BAUD_RATE = "115200"
# arduino = utils.init_arduino(BAUD_RATE)

# WIN_SIZE = (1000, 600)
# win = utils.init_win(*WIN_SIZE, title=u"Medidor de energia")

# MAX_NUM_SAMPLES = 200

# ###############################################################################
# # Tensão RMS
# ###############################################################################
# V_RMS_MIN, V_RMS_MAX = 0, 400

# v_rms_plt = win.addPlot()
# v_rms_plt.showGrid(True, True)
# v_rms_plt.setLabel("left", u"Tensão RMS", units='V')
# v_rms_plt.setLabel("bottom", u"Amostra")
# # v_rms_plt.setYRange(V_RMS_MIN, V_RMS_MAX)
# v_rms_plt.setXRange(0, MAX_NUM_SAMPLES-1)

# v_rms_curve = v_rms_plt.plot()
# v_rms_data = collections.deque(maxlen=MAX_NUM_SAMPLES)

# ###############################################################################
# # Corrente RMS
# ###############################################################################
# I_RMS_MIN, I_RMS_MAX = 0, 400

# i_rms_plt = win.addPlot()
# i_rms_plt.showGrid(True, True)
# i_rms_plt.setLabel("left", u"Corrente RMS", units='A')
# i_rms_plt.setLabel("bottom", u"Amostra")
# # i_rms_plt.setYRange(I_RMS_MIN, I_RMS_MAX)
# i_rms_plt.setXRange(0, MAX_NUM_SAMPLES-1)

# i_rms_curve = i_rms_plt.plot()
# i_rms_data = collections.deque(maxlen=MAX_NUM_SAMPLES)

# win.nextRow()
# ###############################################################################
# # Potência real
# ###############################################################################
# PR_MIN, PR_MAX = 0, 400

# pr_plt = win.addPlot()
# pr_plt.showGrid(True, True)
# pr_plt.setLabel("left", u"Potência Real", units='W')
# pr_plt.setLabel("bottom", u"Amostra")
# # pr_rms_plt.setYRange(PR_RMS_MIN, PR_RMS_MAX)
# pr_plt.setXRange(0, MAX_NUM_SAMPLES-1)

# pr_curve = pr_plt.plot()
# pr_data = collections.deque(maxlen=MAX_NUM_SAMPLES)

# def update_power_meter():
#     try:
#         v_rms, i_rms, real_power = (float(x) for x in arduino.readline().split('#'))

#         v_rms_data.append(v_rms)
#         v_rms_curve.setData(v_rms_data)

#         i_rms_data.append(i_rms)
#         i_rms_curve.setData(i_rms_data)

#         pr_data.append(real_power)
#         pr_curve.setData(pr_data)

#     except ValueError:
#         pass

# tmr = utils.init_timer(update_power_meter)
# tmr.start(0)

# if __name__ == '__main__':
#     utils.init_app()

import argparse
import powermeter

parser = argparse.ArgumentParser(description=u"TODO descrição aqui")
parser.add_argument("--only-samples", type=int, metavar="num_samples",
                                                        dest="num_samples")
parser.add_argument("--fake-samples", action="store_true",
                                                        dest="fake_samples")

args = parser.parse_args()

if args.num_samples:
    powermeter.snapshot(args.num_samples, args.fake_samples)
else:
    powermeter.monitor(args.fake_samples)
