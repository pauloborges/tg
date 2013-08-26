#ifndef PROTOCOL_H
#define PROTOCOL_H

#include "config.h"
#include "powermeter.h"

#ifndef CONF_START_SERIAL_BAUD
#define CONF_START_SERIAL_BAUD 115200
#endif

#ifndef CONF_SERIAL_TIMEOUT
#define CONF_SERIAL_TIMEOUT 500
#endif

#ifndef CONF_MESSAGE_END
#define CONF_MESSAGE_END '\n'
#endif

#ifndef CONF_BUFFER_LEN
#define CONF_BUFFER_LEN 32
#endif

/* Message opcodes */
#define REQ_STOP     0x01
#define REQ_SNAPSHOT 0x02
#define REQ_MONITOR  0x03
#define RES_OK       0x51
#define RES_NO       0x52
#define RES_INST     0x53
#define RES_AGREG    0x54

void setup_protocol(void);
void send_simple_response(uint8_t opcode);
void handle_incoming_data(void);

extern uint8_t buffer[CONF_BUFFER_LEN];

#if CONF_ARDUINO_PLATFORM == ARM
#ifdef CONF_ARM_USB_ENABLED
#define SERIAL SerialUSB
#else
#define SERIAL Serial
#endif
#else
#define SERIAL Serial
#endif

#define SEND_INSTANTANEOUS_EVENT(elapsed, voltage, current)  \
    do {                                                     \
        SERIAL.write(RES_INST);                              \
        SERIAL.write(elapsed, 4);                            \
        SERIAL.write(voltage, 4);                            \
        SERIAL.write(current, 4);                            \
    } while (0)

#define SEND_AGREGATED_EVENT(vrms, irms, rpower)             \
    do {                                                     \
        SERIAL.write(RES_AGREG);                             \
        SERIAL.write(vrms, 4);                               \
        SERIAL.write(irms, 4);                               \
        SERIAL.write(rpower, 4);                             \
    } while (0)

#endif
