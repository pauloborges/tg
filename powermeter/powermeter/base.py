# coding: utf-8

from powermeter.arduino import Arduino, ArduinoError
from powermeter.util import Bundle, lazyfunc
from collections import deque
import powermeter.qt as qt
import traceback
import functools
import struct
import time
import math
import sys

REQUEST_STOP     = 0x01
REQUEST_SNAPSHOT = 0x02
REQUEST_MONITOR  = 0x03
REQUEST_RAW      = 0x04
RESPONSE_OK      = 0x51
RESPONSE_NO      = 0x52
RESPONSE_INST    = 0x53
RESPONSE_AGREG   = 0x54

MODE_INST  = "inst"
MODE_AGREG = "agreg"

MODE_OPTIONS = {
    MODE_INST:  0x00,
    MODE_AGREG: 0x01,
}

STATUS_INIT             = 0
STATUS_STOPPED          = 2
STATUS_WAIT_SAMPLE_RESP = 3
STATUS_SAMPLING         = 4
STATUS_END              = 6
STATUS_CALIB_WAIT_RESP  = 7
STATUS_CALIB_PHASE      = 8
STATUS_CALIB_OFFSET     = 9
STATUS_CALIB_GAIN       = 10

lazy = functools.partial(lazyfunc, sys.modules[__name__])

status_functions = {
    STATUS_INIT:                lazy("init_func"),
    STATUS_STOPPED:             lazy("stopped_func"),
    STATUS_WAIT_SAMPLE_RESP:    lazy("wait_sample_resp_func"),
    STATUS_SAMPLING:            lazy("sampling_func"),
    STATUS_END:                 lazy("end_func"),
    STATUS_CALIB_WAIT_RESP:     lazy("calib_wait_resp_func"),
    STATUS_CALIB_PHASE:         lazy("calib_phase_func"),
    STATUS_CALIB_OFFSET:        lazy("calib_offset_func"),
    STATUS_CALIB_GAIN:          lazy("calib_gain_func"),
}

WIN_SIZE = (1000, 600)

arduino = Arduino(messages={
    RESPONSE_OK: 0,
    RESPONSE_NO: 0,
    RESPONSE_INST: 12,
    RESPONSE_AGREG: 12,
})

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
    arduino.start(baud=config.baud)
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
        arduino.send_message(enc_snapshot_request(MODE_OPTIONS[mode],
                                fake, waves, cycles, 1.0, 0.0, 0.0))
    elif action == "monitor":
        fake = config.fake
        mode = config.mode
        waves = config.number_waves
        arduino.send_message(enc_monitor_request(MODE_OPTIONS[mode],
                                        fake, waves, 1.0, 0.0, 0.0))
    elif action == "calibrate":
        handle_calibrate_action()
        return
    else:
        raise ValueError("Invalid action '%s'" % action)

    if config.mode == MODE_AGREG and not hasattr(config, "base"):
        config.base = time.time()

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

    if opcode == RESPONSE_INST and mode == MODE_INST:
        update_inst(data)
    elif opcode == RESPONSE_AGREG and mode == MODE_AGREG:
        update_agreg(data)
    else:
        print RESPONSE_OK, RESPONSE_AGREG, opcode, type(opcode)
        raise ArduinoError("Expecting OK, INST_SAMPLE, AGREG_SAMPLE "
            "got %s" % opcode)


def end_func():
    # Don't do nothing
    pass


CALIB_PHASE_OPTIONS = {
    "waves": 2,
    "cycles": 1,
    "phasecal": 1.0,
    "voff": 0.0,
    "ioff": 0.0,
}

CALIB_OFFSET_OPTIONS = {
    "samples": 1000,
}

CALIB_GAIN_OPTIONS = {
    "waves": 2,
    "cycles": 1,
    "phasecal": 1.0,
    "voff": 0.0,
    "ioff": 0.0,
}

def handle_calibrate_action():
    mode = config.mode
    fake = config.fake

    if mode == "phase":
        arduino.send_message(enc_snapshot_request(
            MODE_OPTIONS[MODE_INST], fake, **CALIB_PHASE_OPTIONS))
    elif mode == "offset":
        init_ui_calib_offset()
        update_status(STATUS_CALIB_OFFSET)
        return
    else:
        # TODO lê voff e ioff do arquivo
        arduino.send_message(enc_snapshot_request(
            MODE_OPTIONS[MODE_INST], fake, **CALIB_GAIN_OPTIONS))

    update_status(STATUS_CALIB_WAIT_RESP)


def calib_phase_func():
    update_status(STATUS_END)


def calib_offset_func():
    count = 0

    voltage = config.voltage
    current = config.current

    arduino.send_message(enc_raw_request(config.fake,
                            **CALIB_OFFSET_OPTIONS))

    message = arduino.read_message()
    opcode, data = dec_message(message)

    if opcode != RESPONSE_OK:
            raise ArduinoError("Expecting OK, got %s" % opcode)

    while True:
        message = arduino.read_message()
        opcode, data = dec_message(message)

        if opcode == RESPONSE_OK:
            break
        elif opcode == RESPONSE_INST:
            voltage.data.append(data.voltage)
            current.data.append(data.current)
        else:
            raise ArduinoError("Expecting INST, got %s" % opcode)

    # Calcula o OFFSET da tensão
    V_OFFSET = float(sum(voltage.data)) / len(voltage.data)
    voltage.curve.setData(voltage.data)
    voltage.offset.setData([V_OFFSET] * len(voltage.data))

    # Calcula o OFFSET da corrente
    I_OFFSET = float(sum(current.data)) / len(current.data)
    current.curve.setData(current.data)
    current.offset.setData([I_OFFSET] * len(current.data))

    update_status(STATUS_END)


def calib_gain_func():
    update_status(STATUS_END)


def build_plot(win, title, unit, y_range=None, x_range=None, col=1):
    plot = win.addPlot(colspan=col, title=title)
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

    win.nextRow()

    current_plot = build_plot(win, u"Corrente", "A")
    current_curve = current_plot.plot()
    current_data = deque(maxlen=DATA_SIZE_LEN)

    win.nextRow()

    real_power_plot = build_plot(win, u"Potência real", "W")
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


def init_ui_calib_phase():
    pass


def init_ui_calib_offset():
    win = config.win

    voltage_plot = build_plot(win, u"Tensão", "V")
    voltage_curve = voltage_plot.plot()
    voltage_offset = voltage_plot.plot()
    voltage_data = deque()

    win.nextRow()

    current_plot = build_plot(win, u"Corrente", "A")
    current_curve = current_plot.plot()
    current_offset = current_plot.plot()
    current_data = deque()


    config.voltage = Bundle(**{
        "plot": voltage_plot,
        "curve": voltage_curve,
        "data": voltage_data,
        "offset": voltage_offset,
    })

    config.current = Bundle(**{
        "plot": current_plot,
        "curve": current_curve,
        "data": current_data,
        "offset": current_offset,
    })

    config.elapsed = deque()


def init_ui_calib_gain():
    pass


def update_inst(data):
    voltage = config.voltage
    current = config.current
    real_power = config.real_power

    elapsed = config.elapsed
    elapsed.append(data.elapsed)

    voltage_value = data.voltage
    current_value = data.current

    voltage.data.append(voltage_value)
    current.data.append(current_value)
    real_power.data.append(voltage_value * current_value)

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
    return struct.pack("<B", REQUEST_STOP)


def enc_snapshot_request(mode, fake, waves, cycles, phasecal,
                                                    voff, ioff):
    options = (fake << 7) | mode
    return struct.pack("<BBHHfff", REQUEST_SNAPSHOT, options,
        waves, cycles, phasecal, voff, ioff)


def enc_monitor_request(mode, fake, waves, phasecal, voff, ioff):
    return struct.pack("<BBH?", REQUEST_MONITOR,
                        mode, waves, fake)


def enc_raw_request(fake, samples):
    return struct.pack("<B?H", REQUEST_RAW, fake, samples)


def dec_message(message):
    opcode = ord(message[0])

    if opcode in (RESPONSE_OK, RESPONSE_NO):
        return opcode, None
    elif opcode == RESPONSE_INST:
        data = dec_inst_sample_response(message[1:])
    elif opcode == RESPONSE_AGREG:
        data = dec_agreg_sample_response(message[1:])

    return opcode, data


def dec_inst_sample_response(message):
    d = Bundle()

    d.elapsed, d.voltage, d.current = struct.unpack("<fff", message)

    return d


def dec_agreg_sample_response(message):
    d = Bundle()

    d.rms_voltage, d.rms_current, d.real_power = struct.unpack(
        "<fff", message)

    d.elapsed = time.time() - config.base

    return d
