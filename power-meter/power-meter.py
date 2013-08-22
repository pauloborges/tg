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

parser = argparse.ArgumentParser()

parser.add_argument('-f', "--fake", action="store_true")
parser.add_argument('-m', "--mode", choices=["inst", "agreg"],
									required=True)
parser.add_argument('-w', "--waves", type=int, required=True)

subparsers = parser.add_subparsers()

snapshot_parser = subparsers.add_parser("snapshot")
snapshot_parser.set_defaults(action="snapshot")
snapshot_parser.add_argument("-c", "--cycles", type=int,
											required=True)

monitor_parser = subparsers.add_parser("monitor")
monitor_parser.set_defaults(action="monitor")

args = parser.parse_args()

if args.waves <= 0:
	parser.error("waves must be a positive value")

if hasattr(args, "cycles") and args.cycles <= 0:
	parser.error("cycles must be a positive value")

if args.action == "snapshot":
	powermeter.snapshot(args.mode, args.waves, args.cycles,
												args.fake)
elif args.action == "monitor":
	powermeter.monitor(args.mode, args.waves, args.fake)
