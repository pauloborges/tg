#include "Arduino.h"
#include "config.h"
#include "debug.h"
#include "timer.h"
#include "protocol.h"
#include "powermeter.h"
#include "firmware.h"

current_state_func_t current_state_func;

uint8_t current_state;
uint16_t num_samples;
uint16_t remaining_quantity;

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
    DEBUG_INIT(); DEBUG_END("");

    current_state_func = stopped;
}

static void stopped_exit(void)
{
    DEBUG_INIT();
    DEBUG_END("");

    digitalWrite(LED_PIN, LOW);
}

// ----------------------------------------------------------

static void monitor(void)
{
    remaining_quantity = QUANTITY;
    num_samples = 0;

    RESET_ACCUMULATORS();

    while (remaining_quantity) {
        num_samples++;

        REFRESH_ELAPSED_TIME();
        sample();

        if (MODE == MODE_INST)
            SEND_INST_EVENT(ELAPSED_TIME_B(), voltage.b, current.b);
        else if (MODE == MODE_RAW) {
            SEND_RAW_EVENT(voltage.b, current.b);
            remaining_quantity--;
        }

        if (MODE != MODE_RAW && NEW_WAVE_STARTING()) {
            remaining_quantity--;
        }
    }

    if (MODE == MODE_AGRE) {
        rms_voltage.n = sqrt(sum_rms_voltage / num_samples);
        rms_current.n = sqrt(sum_rms_current / num_samples);
        real_power.n = sum_real_power / num_samples;

        SEND_AGRE_EVENT(rms_voltage.b, rms_current.b, real_power.b);
        DEBUG_INIT(); DEBUG_END(num_samples);
    }
}

static void monitor_enter(void)
{
    uint8_t wait = WAIT_NEW_WAVE;
    if (MODE == MODE_RAW)
        wait = DONT_WAIT_NEW_WAVE;

    DEBUG_INIT(); DEBUG_END("");

    update_sample_function();
    VOLTAGE_ZERO = (ADC_MAX_VALUE / 2) - VOLTAGE_OFFSET;


    if (reset_powermeter(wait)) {
        DEBUG_INIT();
        DEBUG_END("failed to reset powermeter");
    }

    current_state_func = monitor;
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
    case STATE_MONITOR:
        monitor_exit();
        break;
    }

    switch (new_state) {
    case STATE_STOPPED:
        stopped_enter();
        break;
    case STATE_MONITOR:
        monitor_enter();
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
