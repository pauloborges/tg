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

static void snapshot(void)
{
    char inst_mode = powermeter.mode == INSTANTANEOUS_MODE;
    num_waves_remaining = powermeter.num_waves;

    RESET_ACCUMULATORS();

    unsigned long t = micros();
    int num_samples = 0;

    while (num_waves_remaining) {
        num_samples++;

        REFRESH_ELAPSED_TIME();
        sample();

        if (inst_mode)
            SEND_INSTANTANEOUS_EVENT(ELAPSED_TIME(),
                                        voltage, current);

        if (NEW_WAVE_STARTING())
            num_waves_remaining--;
    }

    if (!inst_mode) {
        rms_voltage = sqrt(sum_rms_voltage / num_samples);
        rms_current = sqrt(sum_rms_current / num_samples);
        real_power = sum_real_power / num_samples;

        SEND_AGREGATED_EVENT(ELAPSED_TIME(),
                    rms_voltage, rms_current, real_power);

        // t = (micros() - t) / num_samples;
        // DEBUG_INIT();
        // DEBUG("num_samples: "); DEBUG(num_samples);
        // DEBUG(" us/sample: "); DEBUG_END(t);
    }

    num_cycles_remaining--;
    if (!num_cycles_remaining) {
        send_simple_response(RES_OK);
        change_state(STATE_STOPPED);
    }
}

static void snapshot_enter(void)
{
    num_cycles_remaining = powermeter.num_cycles;
    
    update_sample_function();
    reset_powermeter();
}

static void snapshot_exit(void)
{
}

// ----------------------------------------------------------

static void monitor(void)
{
    // TODO
}

static void monitor_enter(void)
{
    num_cycles_remaining = powermeter.num_cycles;

    update_sample_function();
    reset_powermeter();
}

static void monitor_exit(void)
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
        snapshot_exit();
        break;
    case STATE_MONITOR:
        monitor_exit();
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
        snapshot_enter();
        current_state_func = snapshot;
        break;
    case STATE_MONITOR:
        DEBUG_INIT();
        DEBUG_END("MONITOR");
        monitor_enter();
        current_state_func = monitor;
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

    DEBUG_INIT();
    DEBUG_END("initializing firmware");

    pinMode(LED_PIN, OUTPUT);

    change_state(STATE_STOPPED);
}

void serialEventRun(void)
{
    if (Serial.available() > 0) {
        handle_incoming_data();
    }
}
