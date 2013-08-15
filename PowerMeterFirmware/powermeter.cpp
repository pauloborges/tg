#include "Arduino.h"
#include "timer.h"
#include "powermeter.h"

#define PI              3.14159265359
#define FREQ_60HZ       376.9911184			/* 2*PI*60 */
#define PHASE_ZERO      0
#define OFFSET_HALF_ADC (ADC_MAX_VALUE / 2)

struct PowerMeter powermeter = {1, 'I', 60, 50};

sample_function sample;

int raw_voltage;
int last_raw_voltage;

int raw_current;
int last_raw_current;

static float voltage_freq  = FREQ_60HZ;
static float voltage_phase = PHASE_ZERO;
static int voltage_ampl    = OFFSET_HALF_ADC;
static int voltage_offset  = OFFSET_HALF_ADC;

static float current_freq  = FREQ_60HZ;
static float current_phase = PHASE_ZERO;
static int current_ampl    = (ADC_MAX_VALUE / 10);
static int current_offset  = OFFSET_HALF_ADC;

#define FAKE_SAMPLE(freq, phase, ampl, offset, elapsed)      \
    ((int) (ampl * sin(freq * elapsed + phase)) + offset)

static void fake_sample(void)
{
	raw_voltage = FAKE_SAMPLE(voltage_freq, voltage_phase,
				voltage_ampl, voltage_offset, ELAPSED_TIME());
    raw_current = FAKE_SAMPLE(current_freq, current_phase,
				current_ampl, current_offset, ELAPSED_TIME());
}

static void real_sample(void)
{
	raw_voltage = analogRead(VOLTAGE_PIN);
	raw_current = analogRead(CURRENT_PIN);
}

void update_sample_function(void)
{
	if (powermeter.fake == 1)
		sample = fake_sample;
	else
		sample = real_sample;
}

void reset_power_meter(void)
{
	RESET_ELAPSED_TIME();
	sample();
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


