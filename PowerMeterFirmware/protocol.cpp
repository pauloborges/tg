#include "Arduino.h"
#include "debug.h"
#include "firmware.h"
#include "protocol.h"

uint8_t buffer[CONF_BUFFER_LEN];

#define IS_BINARY(n) (0 <= n && n <= 1)
#define IS_MODE(m)                                          \
    (m == MODE_RAW || m == MODE_INST || m == MODE_AGRE)

void setup_protocol(void)
{
    Serial.begin(CONF_SERIAL_BAUD);

    // while (!Serial);
    // Serial.setTimeout(CONF_SERIAL_TIMEOUT);
}

void send_simple_response(uint8_t opcode) {
    Serial.write(opcode);
}

static void handle_stop_request(void)
{
    change_state(STATE_STOPPED);
    send_simple_response(RESPONSE_OK);
}

static void handle_monitor_request(void)
{
    uint8_t options;
    uint8_t fake;
    uint8_t mode;
    uint16_t quantity;
    float_t phase;
    float_t v_offset;
    float_t i_offset;

    if (current_state != STATE_STOPPED) {
        DEBUG_INIT();
        DEBUG_END("arduino busy");
        send_simple_response(RESPONSE_NO);
        return;
    }

    // Message format:
    // OPCODE OPTIONS QUANTITY PHASE_C V_OFFSET I_OFFSET
    //   1       1       2        4        4        4

    options = Serial.read();
    mode = options & 0x03;
    fake = (options & 0x80) >> 7;

    quantity = Serial.read();
    quantity |= Serial.read() << 8;
    
    Serial.readBytes((char *) phase.b, 4);
    Serial.readBytes((char *) v_offset.b, 4);
    Serial.readBytes((char *) i_offset.b, 4);

    if (!IS_BINARY(fake)) {
        DEBUG_INIT();
        DEBUG("invalid fake option: ");
        DEBUG_END(fake);
        goto error;
    }

    if (!IS_MODE(mode)) {
        DEBUG_INIT();
        DEBUG("invalid mode: ");
        DEBUG_END(mode);
        goto error;
    }

    if (quantity <= 0) {
        DEBUG_INIT();
        DEBUG("invalid quantity: ");
        DEBUG_END(quantity);
        goto error;
    }

    DEBUG_INIT(); DEBUG("fake: ");             DEBUG_END(fake);
    DEBUG_INIT(); DEBUG("mode: ");             DEBUG_END(mode);
    DEBUG_INIT(); DEBUG("quantity: ");         DEBUG_END(quantity);
    DEBUG_INIT(); DEBUG("phase correction: "); DEBUG_END(phase.n);
    DEBUG_INIT(); DEBUG("v offset: ");         DEBUG_END(v_offset.n);
    DEBUG_INIT(); DEBUG("i offset: ");         DEBUG_END(i_offset.n);

    FAKE             = fake;
    MODE             = mode;
    QUANTITY         = quantity;
    PHASE_CORRECTION = phase.n;
    VOLTAGE_OFFSET   = v_offset.n;
    CURRENT_OFFSET   = i_offset.n;

    change_state(STATE_MONITOR);
    send_simple_response(RESPONSE_OK);

    return;

error:
    send_simple_response(RESPONSE_NO);
}

static void handle_message(uint8_t opcode)
{
    switch(opcode) {
    case REQUEST_STOP:
        handle_stop_request();
        break;
    case REQUEST_MONITOR:
        handle_monitor_request();
        break;
    }
}

static uint8_t is_valid_opcode(uint8_t opcode)
{
    return opcode == REQUEST_STOP ||
           opcode == REQUEST_MONITOR;
}

void handle_incoming_data(void)
{
    uint8_t opcode = Serial.read();

    if (!is_valid_opcode(opcode)) {
        DEBUG_INIT();
        DEBUG("invalid opcode ");
        DEBUG_END(opcode);
        return;
    }

    handle_message(opcode);
}
