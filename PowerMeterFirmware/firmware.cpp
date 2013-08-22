#include "Arduino.h"
#include "config.h"
#include "debug.h"
#include "timer.h"
#include "protocol.h"
#include "powermeter.h"
#include "firmware.h"

current_state_func_t current_state_func;

char current_state;

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

    for (unsigned int i = powermeter.num_cycles;
                                                i > 0; i--) {
        REFRESH_ELAPSED_TIME();
        sample();

        // process

        if (inst_mode)
            SEND_INSTANTANEOUS_EVENT(ELAPSED_TIME(),
                                raw_voltage, raw_current);
    }

    // if (!inst_mode)
    //     SEND_AGREGATED_EVENT(ELAPSED_TIME(),
    //                 rms_voltage, rms_current, real_power);

    send_simple_response(RES_OK);
    change_state(STATE_STOPPED);
}

static void snapshot_enter(void)
{
    update_sample_function();
    reset_power_meter();
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
    update_sample_function();
    reset_power_meter();
}

static void monitor_exit(void)
{
    // send_simple_response(RES_END);
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

void handle_incoming_data(void)
{
    new_incoming_data();
}
