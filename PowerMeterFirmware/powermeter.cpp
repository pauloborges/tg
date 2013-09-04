#include "Arduino.h"
#include "config.h"
#include "debug.h"
#include "timer.h"
#include "protocol.h"
#include "powermeter.h"

// --------------------------------------------------------
// Defines

#define cbi(sfr, bit) (_SFR_BYTE(sfr) &= ~_BV(bit))
#define sbi(sfr, bit) (_SFR_BYTE(sfr) |= _BV(bit))

#ifndef VOLTAGE_PIN
#define VOLTAGE_PIN A0
#endif

#ifndef CURRENT_PIN
#define CURRENT_PIN A1
#endif

#define PI              3.14159265359
#define FREQ_60HZ       376.9911184         /* 2*PI*60 */
#define PHASE_ZERO      0
#define OFFSET_HALF_ADC (ADC_MAX_VALUE / 2)

// --------------------------------------------------------
// Configuration variables

uint8_t MODE;
uint8_t FAKE;
uint16_t QUANTITY;

float PHASE_CORRECTION;
float VOLTAGE_OFFSET;
float CURRENT_OFFSET;

float VOLTAGE_ZERO;

// --------------------------------------------------------
// Current sampling function

sample_function sample;

// --------------------------------------------------------
// Sampling-related variables

int raw_voltage;
int last_raw_voltage;

int raw_current;
int last_raw_current;

float fixed_voltage;
float last_fixed_voltage;

float_t voltage;
float last_voltage;

float_t current;
float last_current;

float sum_rms_voltage;
float_t rms_voltage;

float sum_rms_current;
float_t rms_current;

float sum_real_power;
float_t real_power;

// --------------------------------------------------------
// Fake-related variables, defines and sampling function

static float voltage_freq  = FREQ_60HZ;
static float voltage_phase = PHASE_ZERO;
static int voltage_ampl    = OFFSET_HALF_ADC;
static int voltage_offset  = OFFSET_HALF_ADC;

static float current_freq  = FREQ_60HZ;
static float current_phase = PHASE_ZERO;
static int current_ampl    = (ADC_MAX_VALUE / 10);
static int current_offset  = OFFSET_HALF_ADC;

#define FAKE_SAMPLE(freq, phase, ampl, offset, elapsed)     \
    ((int) (ampl * sin(freq * elapsed + phase)) + offset)

#define FAKE_VOLTAGE_SAMPLE()                               \
    FAKE_SAMPLE(voltage_freq, voltage_phase, voltage_ampl,  \
        voltage_offset, ELAPSED_TIME())

#define FAKE_CURRENT_SAMPLE()                               \
    FAKE_SAMPLE(current_freq, current_phase, current_ampl,  \
        current_offset, ELAPSED_TIME())

static void fake_sample(void)
{
    last_raw_voltage = raw_voltage;
    last_raw_current = raw_current;

    raw_voltage = FAKE_VOLTAGE_SAMPLE();
    raw_current = FAKE_CURRENT_SAMPLE();

    last_fixed_voltage = fixed_voltage;
    fixed_voltage = last_raw_voltage + PHASE_CORRECTION
                            * (raw_voltage - last_raw_voltage);

    last_voltage = voltage.n;
    last_current = current.n;

    voltage.n = fixed_voltage - VOLTAGE_OFFSET;
    current.n = raw_current - CURRENT_OFFSET;

    sum_rms_voltage += voltage.n * voltage.n;
    sum_rms_current += current.n * current.n;

    sum_real_power += voltage.n * current.n;
}

// --------------------------------------------------------
// Fake-related variables, defines and sampling function

#define REAL_VOLTAGE_SAMPLE() analogRead(VOLTAGE_PIN)
#define REAL_CURRENT_SAMPLE() analogRead(CURRENT_PIN)

static void real_sample(void)
{
    last_raw_voltage = raw_voltage;
    last_raw_current = raw_current;

    raw_voltage = REAL_VOLTAGE_SAMPLE();
    raw_current = REAL_CURRENT_SAMPLE();

    // DEBUG_INIT(); DEBUG("Before: "); DEBUG_END(raw_current);
    // raw_current &= ~0x0001;
    // DEBUG_INIT(); DEBUG("After: "); DEBUG_END(raw_current);

    last_fixed_voltage = fixed_voltage;
    fixed_voltage = last_raw_voltage + PHASE_CORRECTION
                            * (raw_voltage - last_raw_voltage);

    last_voltage = voltage.n;
    last_current = current.n;

    voltage.n = fixed_voltage - VOLTAGE_OFFSET;
    current.n = raw_current - CURRENT_OFFSET;

    sum_rms_voltage += voltage.n * voltage.n;
    sum_rms_current += current.n * current.n;

    sum_real_power += voltage.n * current.n;
}

// --------------------------------------------------------
// External API

void update_sample_function(void)
{
    if (FAKE == 1)
        sample = fake_sample;
    else
        sample = real_sample;
}

uint8_t reset_powermeter(uint8_t mode)
{
    RESET_ELAPSED_TIME();
    sample();

    if (mode == WAIT_NEW_WAVE) {
        uint32_t start_time = millis();

        while (1) {
            REFRESH_ELAPSED_TIME();
            sample();

            if (NEW_WAVE_STARTING())
                break;
            else if (millis() - start_time > 1000)
                return 1;
        }
    }

    RESET_ELAPSED_TIME();
    return 0;
}

void setup_powermeter(void)
{
    // Prescale 16 -> 100 [~5 ksps]
    // sbi(ADCSRA, ADPS2);
    // cbi(ADCSRA, ADPS1);
    // cbi(ADCSRA, ADPS0);

    // Prescale 32 -> 101 [~4.3 ksps]
    // sbi(ADCSRA, ADPS2);
    // cbi(ADCSRA, ADPS1);
    // sbi(ADCSRA, ADPS0);

    // Prescale 64 -> 110 [~3.5 ksps]
    sbi(ADCSRA, ADPS2);
    sbi(ADCSRA, ADPS1);
    cbi(ADCSRA, ADPS0);

    // Prescale 128 -> 111 [~2.5 ksps]
    // sbi(ADCSRA, ADPS2);
    // sbi(ADCSRA, ADPS1);
    // sbi(ADCSRA, ADPS0);
}
