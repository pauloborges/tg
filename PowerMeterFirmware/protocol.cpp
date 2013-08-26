#include "Arduino.h"
#include "debug.h"
#include "firmware.h"
#include "protocol.h"

uint8_t buffer[CONF_BUFFER_LEN];

#define IS_BINARY(number) (0 <= number && number <= 1)
#define IS_MODE(c)                                          \
    (c == INSTANTANEOUS_MODE || c == AGREGATE_MODE)

void setup_protocol(void)
{
    SERIAL.begin(CONF_START_SERIAL_BAUD);
    // while (!SERIAL);

    SERIAL.setTimeout(CONF_SERIAL_TIMEOUT);
}

// static int parse_int(char *buf, size_t len)
// {
//     int result = 0;
//     int tmp;

//     for (size_t i = 0; i < len; i++) {
//         tmp = buf[i];
//         if (tmp == '\0')
//             return -1;
//         result = result * 10 + (tmp - '0'); 
//     }

//     return result;
// }

void send_simple_response(uint8_t opcode) {
    SERIAL.write(opcode);
}

static void handle_req_stop_message(void)
{
    change_state(STATE_STOPPED);
    send_simple_response(RES_OK);
}

static void handle_req_snapshot_message(void)
{
    uint8_t tmp;

    uint8_t fake;
    uint8_t mode;
    uint16_t waves;
    uint16_t cycles;

    float_t phasecal;
    float_t v_offset;
    float_t i_offset;

    if (current_state != STATE_STOPPED) {
        DEBUG_INIT();
        DEBUG_END("arduino busy");
        send_simple_response(RES_NO);
        return;
    }

    // Message format:
    // OPCODE OPTIONS NUM_WAVES NUM_CYCLES PHASECAL V_OFFSET I_OFFSET
    //   1       1       2         2          4         4        4

    tmp = SERIAL.read();
    mode = tmp & 0x01;
    fake = tmp & 0x80 >> 7;

    waves = SERIAL.read();
    waves |= SERIAL.read() << 8;

    cycles = SERIAL.read();
    cycles |= SERIAL.read() << 8;
    
    SERIAL.readBytes((char *) phasecal.bytes, 4);
    SERIAL.readBytes((char *) v_offset.bytes, 4);
    SERIAL.readBytes((char *) i_offset.bytes, 4);

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
    DEBUG_INIT(); DEBUG("mode: "); DEBUG_END(mode);
    DEBUG_INIT(); DEBUG("fake: "); DEBUG_END(fake);
    DEBUG_INIT(); DEBUG("num waves: "); DEBUG_END(waves);
    DEBUG_INIT(); DEBUG("num cycles: "); DEBUG_END(cycles);
    DEBUG_INIT(); DEBUG("phasecal: "); DEBUG_END(phasecal.number);
    DEBUG_INIT(); DEBUG("v offset: "); DEBUG_END(v_offset.number);
    DEBUG_INIT(); DEBUG("i offset: "); DEBUG_END(i_offset.number);

    powermeter.action = STATE_SNAPSHOT;
    powermeter.fake = fake;
    powermeter.mode = mode;
    powermeter.num_waves = waves;
    powermeter.num_cycles = cycles;

    powermeter.phasecal = phasecal.number;
    powermeter.voltage_offset = v_offset.number;
    powermeter.current_offset = i_offset.number;

    change_state(STATE_SNAPSHOT);
    send_simple_response(RES_OK);
    return;

error:
    send_simple_response(RES_NO);
}

static void handle_req_monitor_message(void)
{
    uint8_t tmp;

    uint8_t fake;
    uint8_t mode;
    uint16_t waves;

    float_t phasecal;
    float_t v_offset;
    float_t i_offset;

    if (current_state != STATE_STOPPED) {
        DEBUG_INIT();
        DEBUG_END("arduino busy");
        send_simple_response(RES_NO);
        return;
    }

    // Message format:
    // OPCODE OPTIONS NUM_WAVES PHASECAL V_OFFSET I_OFFSET
    //   1       1       2         4         4        4

    tmp = SERIAL.read();
    mode = tmp & 0x01;
    fake = tmp & 0x80 >> 7;

    waves = SERIAL.read();
    waves |= SERIAL.read() << 8;
    
    SERIAL.readBytes((char *) phasecal.bytes, 4);
    SERIAL.readBytes((char *) v_offset.bytes, 4);
    SERIAL.readBytes((char *) i_offset.bytes, 4);

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
    DEBUG_INIT(); DEBUG("phasecal: "); DEBUG_END(phasecal.number);
    DEBUG_INIT(); DEBUG("v offset: "); DEBUG_END(v_offset.number);
    DEBUG_INIT(); DEBUG("i offset: "); DEBUG_END(i_offset.number);

    powermeter.action = STATE_MONITOR;
    powermeter.fake = fake;
    powermeter.mode = mode;
    powermeter.num_waves = waves;
    powermeter.num_cycles = 1;

    powermeter.phasecal = phasecal.number;
    powermeter.voltage_offset = v_offset.number;
    powermeter.current_offset = i_offset.number;

    change_state(STATE_MONITOR);
    send_simple_response(RES_OK);
    return;

error:
    send_simple_response(RES_NO);
}

static void handle_req_raw_message(void)
{
    uint8_t fake;
    uint16_t samples;

    if (current_state != STATE_STOPPED) {
        DEBUG_INIT();
        DEBUG_END("arduino busy");
        send_simple_response(RES_NO);
        return;
    }

    // Message format:
    // OPCODE FAKE NUM_SAMPLES
    //   1     1       2

    fake = SERIAL.read();

    samples = SERIAL.read();
    samples |= SERIAL.read() << 8;

    if (!IS_BINARY(fake)) {
        DEBUG_INIT();
        DEBUG("invalid fake option: ");
        DEBUG_END(fake);
        goto error;
    }

    if (samples <= 0) {
        DEBUG_INIT();
        DEBUG("invalid number of samples: ");
        DEBUG_END(samples);
        goto error;
    }

    DEBUG_INIT(); DEBUG_END("RAW params:");
    DEBUG_INIT(); DEBUG("fake: "); DEBUG_END(fake);
    DEBUG_INIT(); DEBUG("num samples: "); DEBUG_END(samples);

    powermeter.action = STATE_RAW;
    powermeter.fake = fake;
    powermeter.num_samples = samples;

    change_state(STATE_RAW);
    send_simple_response(RES_OK);
    return;

error:
    send_simple_response(RES_NO);
}

static void handle_message(uint8_t opcode)
{
    switch(opcode) {
    case REQ_STOP:
        handle_req_stop_message();
        break;
    case REQ_SNAPSHOT:
        handle_req_snapshot_message();
        break;
    case REQ_MONITOR:
        handle_req_monitor_message();
        break;
    case REQ_RAW:
        handle_req_raw_message();
        break;
    }
}

static char is_valid_opcode(uint8_t opcode)
{
    return opcode == REQ_STOP ||
           opcode == REQ_SNAPSHOT ||
           opcode == REQ_MONITOR ||
           opcode == REQ_RAW;
}

void handle_incoming_data(void)
{
    uint8_t opcode = SERIAL.read();

    if (!is_valid_opcode(opcode)) {
        DEBUG_INIT();
        DEBUG("invalid opcode ");
        DEBUG_END(opcode);
        return;
    }

    handle_message(opcode);
}
