#!/usr/bin/env python
# coding: utf-8

import os
import serial
import numpy as np
import matplotlib.pyplot as plt

# Configuração do experimento
NUM_SAMPLES = 2000
MAX_SAMPLE  = 1023
IMG_SIZE    = (18, 10)

# Configuração da comunicação serial
BAUD_RATE = "115200"

devices = os.listdir("/dev")
device = next(dev for dev in devices if dev.startswith("ttyACM"))
SERIAL_PORT = os.path.join("/dev", device)

print "Comunicação serial para %s com %s bps" % (SERIAL_PORT, BAUD_RATE)

# Realiza o experimento
arduino = serial.Serial(SERIAL_PORT, BAUD_RATE)

samples = np.zeros(NUM_SAMPLES)
idx = 0
while idx < NUM_SAMPLES:
    try:
        samples[idx] = int(arduino.readline())
        idx += 1
    except ValueError:
        pass

arduino.close()

print "Valor máximo: %d" % samples.max()
print "Valor mínimo: %d" % samples.min()
print "Valor pico-a-pico: %d" % (samples.max() - samples.min())
print "Valor médio:  %f" % samples.mean()
print "RMS: %f" % np.sqrt(np.mean(samples ** 2))

# Desenha o gráfico
plt.figure(figsize=IMG_SIZE)
plt.title("ADC")
plt.xlabel("amostras")
plt.ylabel("leitura")

plt.plot(samples)
plt.grid(True)

plt.show()
