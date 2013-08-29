#ifndef PROTOCOL_H
#define PROTOCOL_H

#include "config.h"
#include "powermeter.h"

#ifndef CONF_SERIAL_BAUD
#define CONF_SERIAL_BAUD 115200
#endif

#ifndef CONF_BUFFER_LEN
#define CONF_BUFFER_LEN 32
#endif

/* Request opcodes */
#define REQUEST_STOP    0x01
#define REQUEST_MONITOR 0x02

/* Response opcodes */
#define RESPONSE_OK     0x50
#define RESPONSE_NO     0x51
#define RESPONSE_RAW    0x52
#define RESPONSE_INST   0x53
#define RESPONSE_AGRE   0x54

/* Monitor modes */
#define MODE_RAW  0x00
#define MODE_INST 0x01
#define MODE_AGRE 0x02

void setup_protocol(void);
void send_simple_response(uint8_t opcode);
void handle_incoming_data(void);

extern uint8_t buffer[CONF_BUFFER_LEN];

#define SEND_RAW_EVENT(voltage, current)                     \
    do {                                                     \
        Serial.write(RESPONSE_RAW);                          \
        Serial.write(voltage, 4);                            \
        Serial.write(current, 4);                            \
    } while (0)

#define SEND_INST_EVENT(elapsed, voltage, current)           \
    do {                                                     \
        Serial.write(RESPONSE_INST);                         \
        Serial.write(elapsed, 4);                            \
        Serial.write(voltage, 4);                            \
        Serial.write(current, 4);                            \
    } while (0)

#define SEND_AGRE_EVENT(vrms, irms, rpower)                  \
    do {                                                     \
        Serial.write(RESPONSE_AGRE);                         \
        Serial.write(vrms, 4);                               \
        Serial.write(irms, 4);                               \
        Serial.write(rpower, 4);                             \
    } while (0)

#endif
