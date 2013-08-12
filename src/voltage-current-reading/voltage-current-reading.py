#!/usr/bin/env python
# coding: utf-8

import sys
sys.path.append("..")

import matplotlib.pyplot as plt
import numpy as np
import utils

NUM_SAMPLES = 300
MAX_SAMPLE  = 1023
IMG_SIZE    = (18, 10)

BAUD_RATE = "115200"
arduino = utils.init_arduino(BAUD_RATE)

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

arduino.close()

# Desenha o gráfico
plt.figure(figsize=IMG_SIZE)
plt.title("Voltage and current reading")
plt.xlabel("# sample")
plt.ylabel("Voltage")

plt.plot(voltage, "-sk")
plt.plot(current, "-or")

# plt.ylim(0, MAX_SAMPLE)
plt.xlim(0, NUM_SAMPLES)
plt.grid(True)

plt.show()
