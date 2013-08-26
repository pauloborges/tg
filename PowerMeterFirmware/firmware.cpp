#include "Arduino.h"
#include "config.h"
#include "debug.h"
#include "timer.h"
#include "protocol.h"
#include "powermeter.h"
#include "firmware.h"

current_state_func_t current_state_func;

char current_state;

unsigned int num_waves_remaining;
unsigned int num_cycles_remaining;

unsigned int num_samples;

// ----------------------------------------------------------

static void stopped(void)
{
    static unsigned char counter = 0;
    
    if (counter == 7)
        digitalWrite(LED_PIN, HIGH);
    else if (counter == 9)
        digitalWrite(LED_PIN, LOW);

    delay(100);
    counter = (counter + 1) % 10;
}

static void stopped_enter(void)
{
}

static void stopped_exit(void)
{
}

// ----------------------------------------------------------

static void sampling(void)
{
    char inst_mode = powermeter.mode == INSTANTANEOUS_MODE;
    num_waves_remaining = powermeter.num_waves;

    RESET_ACCUMULATORS();
    num_samples = 0;

    while (num_waves_remaining) {
        num_samples++;

        REFRESH_ELAPSED_TIME();
        sample();

        if (inst_mode)
            SEND_INSTANTANEOUS_EVENT(ELAPSED_TIME().bytes,
                                    voltage.bytes, current.bytes);

        if (NEW_WAVE_STARTING()) {
            num_waves_remaining--;
        }
    }

    if (!inst_mode) {
        rms_voltage.number = sqrt(sum_rms_voltage / num_samples);
        rms_current.number = sqrt(sum_rms_current / num_samples);
        real_power.number = sum_real_power / num_samples;

        SEND_AGREGATED_EVENT(rms_voltage.bytes, rms_current.bytes,
                                real_power.bytes);

        // DEBUG_INIT(); DEBUG_END(num_samples);
    }

    num_cycles_remaining--;
    if (powermeter.action == STATE_SNAPSHOT
                                        && !num_cycles_remaining) {
        send_simple_response(RES_OK);
        change_state(STATE_STOPPED);
    }
}

static void sampling_enter(void)
{
    num_cycles_remaining = powermeter.num_cycles;
    
    update_sample_function();
    reset_powermeter(1);
}

static void sampling_exit(void)
{
}

// ----------------------------------------------------------

static void raw(void)
{
    RESET_ACCUMULATORS();

    for (uint16_t i = powermeter.num_samples; i; i--) {
        REFRESH_ELAPSED_TIME();
        sample();

        SEND_INSTANTANEOUS_EVENT(ELAPSED_TIME().bytes,
                                voltage.bytes, current.bytes);
    }

    send_simple_response(RES_OK);
    change_state(STATE_STOPPED);
}

static void raw_enter(void)
{
    update_sample_function();
    reset_powermeter(0);
}

static void raw_exit(void)
{
}

// ----------------------------------------------------------

void change_state(char new_state)
{
    switch (current_state) {
    case STATE_STOPPED:
        stopped_exit();
        break;
    case STATE_SNAPSHOT:
        sampling_exit();
        break;
    case STATE_MONITOR:
        sampling_exit();
        break;
    case STATE_RAW:
        raw_exit();
        break;
    }

    switch (new_state) {
    case STATE_STOPPED:
        DEBUG_INIT();
        DEBUG_END("STOPPED");
        stopped_enter();
        current_state_func = stopped;
        break;
    case STATE_SNAPSHOT:
        DEBUG_INIT();
        DEBUG_END("SNAPSHOT");
        sampling_enter();
        current_state_func = sampling;
        break;
    case STATE_MONITOR:
        DEBUG_INIT();
        DEBUG_END("MONITOR");
        sampling_enter();
        current_state_func = sampling;
        break;
    case STATE_RAW:
        DEBUG_INIT();
        DEBUG_END("RAW");
        raw_enter();
        current_state_func = raw;
        break;
    default:
        return;
    }

    current_state = new_state;
}

void setup_firmware(void)
{
    setup_protocol();
    setup_powermeter();

    pinMode(LED_PIN, OUTPUT);

    DEBUG_INIT();
    DEBUG_END("firmware initialized");

    change_state(STATE_STOPPED);
}

void serialEventRun(void)
{
    if (Serial.available() > 0) {
        handle_incoming_data();
    }
}
