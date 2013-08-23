# coding: utf-8

from powermeter.arduino import Arduino, ArduinoError
from powermeter.util import Bundle, lazyfunc
from collections import deque
import powermeter.qt as qt
import traceback
import functools
import math
import sys

REQUEST_STOP          = 'S'
REQUEST_SNAPSHOT      = 'P'
REQUEST_MONITOR       = 'M'
RESPONSE_OK           = 'O'
RESPONSE_NO           = 'N'
RESPONSE_INST_SAMPLE  = 'I'
RESPONSE_AGREG_SAMPLE = 'A'

MODE_INST  = "inst"
MODE_AGREG = "agreg"

MODE_OPTIONS = {
    MODE_INST:  'I',
    MODE_AGREG: 'A',
}

STATUS_INIT                    = 0
STATUS_STOPPED                 = 2
STATUS_WAIT_SAMPLE_RESP        = 3
STATUS_SAMPLING                = 4
STATUS_END                     = 6

lazy = functools.partial(lazyfunc, sys.modules[__name__])

status_functions = {
    STATUS_INIT:             lazy("init_func"),
    STATUS_STOPPED:          lazy("stopped_func"),
    STATUS_WAIT_SAMPLE_RESP: lazy("wait_sample_resp_func"),
    STATUS_SAMPLING:         lazy("sampling_func"),
    STATUS_END:              lazy("end_func"),
}

WIN_SIZE = (1000, 600)

TIMEOUT         = 200 # msec
arduino = Arduino(TIMEOUT)

current_status  = None
DATA_SIZE_LEN   = 100 # samples

config = Bundle()


def run(**kwargs):
    app, win = qt.init(WIN_SIZE)

    config.update(kwargs)
    config.win = win

    tmr = qt.timer(loop)
    tmr.start(0)

    update_status(STATUS_INIT)

    return app.exec_()


def loop():
    try:
        status_functions[current_status]()
    except KeyboardInterrupt:
        print ""
        arduino.send_message(enc_stop_request())
        arduino.close()
        qt.quit()
    except:
        print traceback.format_exc()
        try:
            arduino.send_message(enc_stop_request())
            arduino.close()
        except:
            pass
        qt.quit()


def init_func():
    arduino.start()
    arduino.send_message(enc_stop_request())
    update_status(STATUS_STOPPED)


def stopped_func():
    message = arduino.read_message()
    opcode, data = dec_message(message)

    if opcode != RESPONSE_OK:
        raise ArduinoError("Expecting OK, got %s" % opcode)

    action = config.action
    if action == "snapshot":
        fake = config.fake
        mode = config.mode
        waves = config.number_waves
        cycles = config.number_cycles
        arduino.send_message(
                enc_snapshot_request(fake, mode, waves, cycles))
    elif action == "monitor":
        fake = config.fake
        mode = config.mode
        waves = config.number_waves
        arduino.send_message(
                enc_monitor_request(fake, mode, waves))
    else:
        raise ValueError("Invalid action '%s'" % action)

    update_status(STATUS_WAIT_SAMPLE_RESP)


def wait_sample_resp_func():
    message = arduino.read_message()
    opcode, data = dec_message(message)

    if opcode != RESPONSE_OK:
        raise ArduinoError("Expecting OK, got %s" % opcode)

    mode = config.mode
    if mode == MODE_INST:
        ui_init_inst()
    elif mode == MODE_AGREG:
        ui_init_agreg()

    update_status(STATUS_SAMPLING)


def sampling_func():
    message = arduino.read_message()
    opcode, data = dec_message(message)

    if opcode == RESPONSE_OK:
        arduino.send_message(enc_stop_request())
        update_status(STATUS_END)
        return

    mode = config.mode

    if opcode == RESPONSE_INST_SAMPLE and mode == MODE_INST:
        update_inst(data)
    elif opcode == RESPONSE_AGREG_SAMPLE and mode == MODE_AGREG:
        update_agreg(data)
    else:
        raise ArduinoError("Expecting OK, INST_SAMPLE, AGREG_SAMPLE "
            "got %s" % opcode)


def end_func():
    # Don't do nothing
    pass


def build_plot(win, title, unit, y_range=None, x_range=None,
                                                        colspan=1):
    plot = win.addPlot(colspan=colspan, title=title)
    plot.setLabel("left", units=unit)
    plot.setLabel("bottom", units="s")
    plot.hideButtons()
    plot.setMenuEnabled(False)
    plot.showGrid(True, True, 0.2)

    if y_range:
        plot.setYRange(*y_range)
    if x_range:
        plot.setXRange(*x_range)

    return plot

def ui_init_inst():
    win = config.win

    voltage_plot = build_plot(win, u"Tensão", "V")
    voltage_curve = voltage_plot.plot()
    voltage_data = deque(maxlen=DATA_SIZE_LEN)

    current_plot = build_plot(win, u"Corrente", "A")
    current_curve = current_plot.plot()
    current_data = deque(maxlen=DATA_SIZE_LEN)

    win.nextRow()

    real_power_plot = build_plot(win, u"Potência real", "W",
                                                colspan=2)
    real_power_curve = real_power_plot.plot()
    real_power_data = deque(maxlen=DATA_SIZE_LEN)

    config.voltage = Bundle(**{
        "plot": voltage_plot,
        "curve": voltage_curve,
        "data": voltage_data,
    })

    config.current = Bundle(**{
        "plot": current_plot,
        "curve": current_curve,
        "data": current_data,
    })

    config.real_power = Bundle(**{
        "plot": real_power_plot,
        "curve": real_power_curve,
        "data": real_power_data,
    })

    config.elapsed = deque(maxlen=DATA_SIZE_LEN)


def ui_init_agreg():
    win = config.win

    rms_voltage_plot = build_plot(win, u"Tensão RMS", "V")
    rms_voltage_curve = rms_voltage_plot.plot()
    rms_voltage_data = deque(maxlen=DATA_SIZE_LEN)

    rms_current_plot = build_plot(win, u"Corrente RMS", "A")
    rms_current_curve = rms_current_plot.plot()
    rms_current_data = deque(maxlen=DATA_SIZE_LEN)

    power_factor_plot = build_plot(win, u"Fator de potência", None,
                                    y_range=(0.0, 1.0))
    power_factor_curve = power_factor_plot.plot()
    power_factor_data = deque(maxlen=DATA_SIZE_LEN)

    win.nextRow()

    real_power_plot = build_plot(win, u"Potência real", "W")
    real_power_curve = real_power_plot.plot()
    real_power_data = deque(maxlen=DATA_SIZE_LEN)

    reac_power_plot = build_plot(win, u"Potência reativa", "VAr")
    reac_power_curve = reac_power_plot.plot()
    reac_power_data = deque(maxlen=DATA_SIZE_LEN)

    total_power_plot = build_plot(win, u"Potência aparente", "VA")
    total_power_curve = total_power_plot.plot()
    total_power_data = deque(maxlen=DATA_SIZE_LEN)

    config.rms_voltage = Bundle(**{
        "plot": rms_voltage_plot,
        "curve": rms_voltage_curve,
        "data": rms_voltage_data,
    })

    config.power_factor = Bundle(**{
        "plot": power_factor_plot,
        "curve": power_factor_curve,
        "data": power_factor_data,
    })

    config.rms_current = Bundle(**{
        "plot": rms_current_plot,
        "curve": rms_current_curve,
        "data": rms_current_data,
    })

    config.real_power = Bundle(**{
        "plot": real_power_plot,
        "curve": real_power_curve,
        "data": real_power_data,
    })

    config.reac_power = Bundle(**{
        "plot": reac_power_plot,
        "curve": reac_power_curve,
        "data": reac_power_data,
    })

    config.total_power = Bundle(**{
        "plot": total_power_plot,
        "curve": total_power_curve,
        "data": total_power_data,
    })

    config.elapsed = deque(maxlen=DATA_SIZE_LEN)


def update_inst(data):
    voltage = config.voltage
    current = config.current
    real_power = config.real_power

    elapsed = config.elapsed
    elapsed.append(data.elapsed)

    voltage.data.append(data.voltage)
    current.data.append(data.current)
    real_power.data.append(data.voltage * data.current)

    voltage.curve.setData(elapsed, voltage.data)
    current.curve.setData(elapsed, current.data)
    real_power.curve.setData(elapsed, real_power.data)


def update_agreg(data):
    rms_voltage  = config.rms_voltage
    rms_current  = config.rms_current
    power_factor = config.power_factor
    real_power   = config.real_power
    reac_power   = config.reac_power
    total_power  = config.total_power

    elapsed = config.elapsed
    elapsed.append(data.elapsed)

    total_power_value = data.rms_voltage * data.rms_current

    if total_power_value < data.real_power:
        print "WARNING! total_power - real_power = %s" % (
            total_power_value - data.real_power)
        total_power_value = data.real_power

    reac_power_value = math.sqrt(
        total_power_value**2 - data.real_power**2)
    power_factor_value = data.real_power / total_power_value


    rms_voltage.data.append(data.rms_voltage)
    rms_current.data.append(data.rms_current)
    power_factor.data.append(power_factor_value)
    real_power.data.append(data.real_power)
    reac_power.data.append(reac_power_value)
    total_power.data.append(total_power_value)

    rms_voltage.curve.setData(elapsed, rms_voltage.data)
    rms_current.curve.setData(elapsed, rms_current.data)
    power_factor.curve.setData(elapsed, power_factor.data)
    real_power.curve.setData(elapsed, real_power.data)
    reac_power.curve.setData(elapsed, reac_power.data)
    total_power.curve.setData(elapsed, total_power.data)


def update_status(status):
    global current_status
    current_status = status


def enc_stop_request():
    return "S"


def enc_snapshot_request(fake, mode, waves, cycles):
    message = REQUEST_SNAPSHOT
    message += '1' if fake else '0'
    message += MODE_OPTIONS[mode]
    message += "%03d" % waves
    message += "%03d" % cycles
    return message


def enc_monitor_request(fake, mode, waves):
    message = REQUEST_MONITOR
    message += '1' if fake else '0'
    message += MODE_OPTIONS[mode]
    message += "%03d" % waves
    return message


def dec_message(message):
    opcode = message[0]

    if opcode in (RESPONSE_OK, RESPONSE_NO):
        return opcode, None
    elif opcode == RESPONSE_INST_SAMPLE:
        data = dec_inst_sample_response()
    elif opcode == RESPONSE_AGREG_SAMPLE:
        data = dec_agreg_sample_response()
    else:
        raise ArduinoError("Invalid message opcode: %s" % opcode)

    return opcode, data


def dec_inst_sample_response():
    data = Bundle()

    message = arduino.read_message()
    data.elapsed = float(message)

    message = arduino.read_message()
    data.voltage = float(message)

    message = arduino.read_message()
    data.current = float(message)

    return data


def dec_agreg_sample_response():
    data = Bundle()

    message = arduino.read_message()
    data.elapsed = float(message)

    message = arduino.read_message()
    data.rms_voltage = float(message)

    message = arduino.read_message()
    data.rms_current = float(message)

    message = arduino.read_message()
    data.real_power = float(message)

    return data
