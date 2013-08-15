#!/usr/bin/env python
# coding: utf-8

import sys
sys.path.append("..")

import matplotlib.pyplot as plt
import numpy as np
import utils

NUM_IGNORED_SAMPLES = 1500
NUM_SAMPLES = 100
MAX_SAMPLE  = 1023
IMG_SIZE    = (25, 15)

BAUD_RATE = "115200"
arduino = utils.init_arduino(BAUD_RATE)

# Ignora samples iniciais da estabilização do HFP
for i in xrange(NUM_IGNORED_SAMPLES):
    try:
        arduino.readline()
    except:
        pass

voltage = []
current = []
idx = 0

while idx < NUM_SAMPLES:
    try:
        v, c = (float(x) for x in arduino.readline().split('#'))

        voltage.append(v)
        current.append(c)

        idx += 1
    except ValueError:
        pass

# Desenha o gráfico
plt.figure(figsize=IMG_SIZE)
plt.title("Voltage and current reading")
plt.xlabel("# sample")
plt.ylabel("Voltage")

plt.plot(voltage, "-sk")
plt.plot(current, "-or")
plt.legend([u"tensão", u"corrente"], loc="best")

# plt.ylim(0, MAX_SAMPLE)
plt.xlim(0, NUM_SAMPLES)
plt.grid(True)

plt.show()

arduino.close()
print
