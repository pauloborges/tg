#!/usr/bin/env python
# coding: utf-8

import sys
sys.path.append("..")

import matplotlib.pyplot as plt
import utils

# Configuração do experimento
NUM_SAMPLES = 128
MAX_SAMPLE  = 1023
IMG_SIZE    = (18, 10)

BAUD_RATE = "115200"
arduino = utils.init_arduino(BAUD_RATE)

voltages = []
idx = 0
while idx < NUM_SAMPLES:
    try:
        voltages.append(int(arduino.readline()))
        idx += 1
    except ValueError:
        pass

arduino.close()

# Desenha o gráfico
plt.figure(figsize=IMG_SIZE)
plt.title("Voltage reading")
plt.xlabel("# sample")
plt.ylabel("Voltage")

plt.plot(voltages, "-o")
plt.plot(voltages)
plt.ylim(0, MAX_SAMPLE)
plt.xlim(0, NUM_SAMPLES)
plt.grid(True)

plt.show()
