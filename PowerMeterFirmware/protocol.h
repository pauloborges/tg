#ifndef PROTOCOL_H
#define PROTOCOL_H

#include "config.h"
#include "powermeter.h"

#ifndef CONF_SERIAL_BAUD
#define CONF_SERIAL_BAUD 115200
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
#define REQ_STOP     'S'
#define REQ_SNAPSHOT 'P'
#define REQ_MONITOR  'M'
#define RES_OK       'O'
#define RES_NO       'N'
#define RES_INST_EV  INSTANTANEOUS_MODE
#define RES_AGRE_EV  AGREGATE_MODE

extern char message_buffer[CONF_BUFFER_LEN];

void setup_protocol(void);
void send_simple_response(char opcode);
void handle_incoming_data(void);

#define SEND_INSTANTANEOUS_EVENT(elapsed, voltage, current)  \
    do {                                                     \
        Serial.println(RES_INST_EV);                         \
        Serial.println(1000 * elapsed);                      \
        Serial.println(voltage);                             \
        Serial.println(current);                             \
    } while (0)

#define SEND_AGREGATED_EVENT(elapsed, vrms, irms, rpower)    \
    do {                                                     \
        Serial.println(RES_AGRE_EV);                         \
        Serial.println(1000 * elapsed);                      \
        Serial.println(vrms);                                \
        Serial.println(irms);                                \
        Serial.println(rpower);                              \
    } while (0)

#endif
