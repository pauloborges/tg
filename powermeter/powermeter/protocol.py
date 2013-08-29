# coding: utf-8

import struct

from powermeter.util import bundle, enum

__all__ = (
    "REQUEST",
    "MODE",
    "RESPONSE",
    "RESPONSE_SIZE",
    "enc_stop_request",
    "enc_monitor_request",
    "dec_message",
)

REQUEST = enum(
    STOP=0x01,
    MONITOR=0x02,
)

MODE = enum(
    RAW=0x00,
    INST=0x01,
    AGRE=0x02,
)

RESPONSE = enum(
    OK=0x50,
    NO=0x51,
    RAW=0x52,
    INST=0x53,
    AGRE=0x54,
)

RESPONSE_SIZE = {
    RESPONSE.OK: 1,
    RESPONSE.NO: 1,
    RESPONSE.RAW: 9,
    RESPONSE.INST: 13,
    RESPONSE.AGRE: 13,
}

def enc_stop_request():
    return struct.pack("<B", REQUEST.STOP)

def enc_monitor_request(mode, fake, quantity, phasecal,
                        voltage_offset, current_offset):
    options = (fake << 7) | mode
    return struct.pack("<BBHfff", REQUEST.MONITOR, options,
                        quantity, phasecal, voltage_offset,
                        current_offset)

def dec_message(message):
    opcode, message = ord(message[0]), message[1:]

    if opcode in (RESPONSE.OK, RESPONSE.NO):
        return opcode, None
    elif opcode == RESPONSE.RAW:
        return opcode, dec_raw_response(message)
    elif opcode == RESPONSE.INST:
        return opcode, dec_inst_response(message)
    elif opcode == RESPONSE.AGRE:
        return opcode, dec_agre_response(message)
    else:
        raise IOError("Unexpected opcode 0x%02d" % opcode)

def dec_raw_response(message):
    v, i = struct.unpack("<ff", message)
    return bundle(voltage=v, current=i)

def dec_inst_response(message):
    e, v, i = struct.unpack("<fff", message)
    return bundle(elapsed=e, voltage=v, current=i)

def dec_agre_response(message):
    rms_v, rms_i, rp = struct.unpack("<fff", message)
    return bundle(rms_voltage=rms_v, rms_current=rms_i, real_power=rp)
