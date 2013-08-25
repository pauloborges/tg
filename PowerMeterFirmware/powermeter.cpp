#include "Arduino.h"
#include "config.h"
#include "debug.h"
#include "timer.h"
#include "protocol.h"
#include "powermeter.h"

#define PI              3.14159265359
#define FREQ_60HZ       376.9911184         /* 2*PI*60 */
#define PHASE_ZERO      0
#define OFFSET_HALF_ADC (ADC_MAX_VALUE / 2)

struct PowerMeter powermeter = {1, 'I', 60, 50};

sample_function sample;

int raw_voltage;
int last_raw_voltage;

int raw_current;
int last_raw_current;

float fixed_voltage;
float last_fixed_voltage;

float voltage;
float last_voltage;

float current;
float last_current;

float sum_rms_voltage;
float rms_voltage;

float sum_rms_current;
float rms_current;

float sum_real_power;
float real_power;

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

#define REAL_VOLTAGE_SAMPLE() analogRead(VOLTAGE_PIN)
#define REAL_CURRENT_SAMPLE() analogRead(CURRENT_PIN)

static void fake_sample(void)
{
    last_raw_voltage = raw_voltage;
    last_raw_current = raw_current;

    raw_voltage = FAKE_VOLTAGE_SAMPLE();
    raw_current = FAKE_CURRENT_SAMPLE();

    // FIXME
    // last_fixed_voltage = fixed_voltage;
    // fixed_voltage = last_raw_voltage + PHASE_CORRECTION
    //                         * (raw_voltage - last_raw_voltage);
    last_fixed_voltage = fixed_voltage;
    fixed_voltage = raw_voltage;

    last_voltage = voltage;
    last_current = current;

    // FIXME HFP
    voltage = fixed_voltage - OFFSET_HALF_ADC;
    current = raw_current - OFFSET_HALF_ADC;

    sum_rms_voltage += voltage * voltage;
    sum_rms_current += current * current;

    sum_real_power += voltage * current;
}

static void real_sample(void)
{
    last_raw_voltage = raw_voltage;
    last_raw_current = raw_current;

    raw_voltage = REAL_VOLTAGE_SAMPLE();
    raw_current = REAL_CURRENT_SAMPLE();

    // FIXME HFP
    // last_fixed_voltage = fixed_voltage;
    // fixed_voltage = last_raw_voltage + PHASE_CORRECTION
    //                         * (raw_voltage - last_raw_voltage);
    last_fixed_voltage = fixed_voltage;
    fixed_voltage = raw_voltage;

    last_voltage = voltage;
    last_current = current;

    // FIXME HFP
    voltage = fixed_voltage - OFFSET_HALF_ADC;
    current = raw_current - OFFSET_HALF_ADC;

    sum_rms_voltage += voltage * voltage;
    sum_rms_current += current * current;

    sum_real_power += voltage * current;
}

void update_sample_function(void)
{
    if (powermeter.fake == 1)
        sample = fake_sample;
    else
        sample = real_sample;
}

void reset_powermeter(void)
{
    RESET_ELAPSED_TIME();
    sample();

    while (1) {
        REFRESH_ELAPSED_TIME();
        sample();

        if (NEW_WAVE_STARTING())
            break;
    }
}

void setup_powermeter(void)
{
    #if CONF_ARDUINO_PLATFORM == ARM
    analogReadResolution(12);
    // TODO faster ADC in Arduino Due
    #else
    sbi(ADCSRA, ADPS2);
    cbi(ADCSRA, ADPS1);
    cbi(ADCSRA, ADPS0);
    #endif
}


