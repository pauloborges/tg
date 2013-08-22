#include "Arduino.h"
#include "debug.h"
#include "firmware.h"
#include "protocol.h"

#define IS_BINARY(number) (0 <= number && number <= 1)
#define IS_MODE(c)                                          \
    (c == INSTANTANEOUS_MODE || c == AGREGATE_MODE)

char message_buffer[CONF_BUFFER_LEN];

void setup_protocol(void)
{
    Serial.begin(CONF_SERIAL_BAUD);

    // while (!Serial);
    DEBUG_INIT(); DEBUG_END("serial initialized");

    Serial.setTimeout(CONF_SERIAL_TIMEOUT);
}

static int parse_int(char *buf, size_t len)
{
    int result = 0;
    int tmp;

    for (size_t i = 0; i < len; i++) {
        tmp = buf[i];
        if (tmp == '\0')
            return -1;
        result = result * 10 + (tmp - '0'); 
    }

    return result;
}

void send_simple_response(char opcode) {
    if (opcode == RES_OK)
        Serial.println("OK");
    else if (opcode == RES_NO)
        Serial.println("NO");
}

static void handle_req_stop_message(void)
{
    change_state(STATE_STOPPED);
    send_simple_response(RES_OK);
}

static void handle_req_snapshot_message(void)
{
    int fake;
    char mode;
    int waves;
    int cycles;

    if (current_state != STATE_STOPPED) {
        DEBUG_INIT();
        DEBUG_END("arduino busy");
        send_simple_response(RES_NO);
        return;
    }

    // Message format:
    // 'P' Fake Mode NumWaves NumCycles
    //  1   1    1      3         3

    fake = parse_int(message_buffer + 1, 1);
    mode = message_buffer[2];
    waves = parse_int(message_buffer + 3, 3);
    cycles = parse_int(message_buffer + 6, 3);

    if (!IS_BINARY(fake)) {
        DEBUG_INIT();
        DEBUG("invalid fake option: ");
        DEBUG_END(fake);
        goto error;
    }

    if (!IS_MODE(mode)) {
        DEBUG_INIT();
        DEBUG("invalid mode: ");
        DEBUG_END(mode > ' ' ? mode : (int) mode);
        goto error;
    }

    if (waves <= 0) {
        DEBUG_INIT();
        DEBUG("invalid number of waves: ");
        DEBUG_END(waves);
        goto error;
    }

    if (cycles <= 0) {
        DEBUG_INIT();
        DEBUG("invalid number of cycles: ");
        DEBUG_END(cycles);
        goto error;
    }

    DEBUG_INIT(); DEBUG_END("SNAPSHOT params:");
    DEBUG_INIT(); DEBUG("fake: "); DEBUG_END(fake);
    DEBUG_INIT(); DEBUG("mode: "); DEBUG_END(mode);
    DEBUG_INIT(); DEBUG("num waves: "); DEBUG_END(waves);
    DEBUG_INIT(); DEBUG("num cycles: "); DEBUG_END(cycles);

    powermeter.fake = fake;
    powermeter.mode = mode;
    powermeter.num_waves = waves;
    powermeter.num_cycles = cycles;

    change_state(STATE_SNAPSHOT);
    send_simple_response(RES_OK);
    return;

error:
    send_simple_response(RES_NO);
}

static void handle_req_monitor_message(void)
{
    unsigned short int fake;
    unsigned short int mode;
    unsigned short int waves;

    if (current_state != STATE_STOPPED) {
        DEBUG_INIT();
        DEBUG_END("arduino busy");
        send_simple_response(RES_NO);
        return;
    }

    // Message format:
    // 'M' Fake Mode NumWaves
    //  1   1    1      3

    fake = parse_int(message_buffer + 1, 1);
    mode = message_buffer[2];
    waves = parse_int(message_buffer + 3, 3);

    if (!IS_BINARY(fake)) {
        DEBUG_INIT();
        DEBUG("invalid fake option: ");
        DEBUG_END(fake);
        goto error;
    }

    if (!IS_MODE(mode)) {
        DEBUG_INIT();
        DEBUG("invalid mode: ");
        DEBUG_END(mode > ' ' ? mode : (int) mode);
        goto error;
    }

    if (waves <= 0) {
        DEBUG_INIT();
        DEBUG("invalid number of waves: ");
        DEBUG_END(waves);
        goto error;
    }

    DEBUG_INIT(); DEBUG_END("MONITOR params:");
    DEBUG_INIT(); DEBUG("fake: "); DEBUG_END(fake);
    DEBUG_INIT(); DEBUG("mode: "); DEBUG_END(mode);
    DEBUG_INIT(); DEBUG("num waves: "); DEBUG_END(waves);

    change_state(STATE_MONITOR);
    send_simple_response(RES_OK);
    return;

error:
    send_simple_response(RES_NO);
}

static void handle_message(void)
{
    DEBUG_INIT();
    DEBUG("incoming message '");
    DEBUG(message_buffer);
    DEBUG_END("'");

    switch(message_buffer[0]) {
    case REQ_STOP:
        handle_req_stop_message();
        break;
    case REQ_SNAPSHOT:
        handle_req_snapshot_message();
        break;
    case REQ_MONITOR:
        handle_req_monitor_message();
        break;
    }
}

static char is_valid_opcode(char opcode)
{
    return opcode == REQ_STOP ||
           opcode == REQ_SNAPSHOT ||
           opcode == REQ_MONITOR;
}

void new_incoming_data(void)
{
    int len = Serial.readBytesUntil(CONF_MESSAGE_END,
                            message_buffer, CONF_BUFFER_LEN);

    if (!len) {
        DEBUG_INIT();
        DEBUG("broken message with size ");
        DEBUG_END(len);
        return;
    }

    if (!is_valid_opcode(message_buffer[0])) {
        DEBUG_INIT();
        DEBUG("invalid opcode ");
        DEBUG_END(message_buffer[0]);
        return;
    }

    message_buffer[len] = '\0';
    handle_message();
}
