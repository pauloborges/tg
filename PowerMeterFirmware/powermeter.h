#ifndef POWERMETER_H
#define POWERMETER_H

#include "config.h"

#if CONF_ARDUINO_PLATFORM == ARM
#define ADC_MAX_VALUE 4095
#else
#define ADC_MAX_VALUE 1023
#define cbi(sfr, bit) (_SFR_BYTE(sfr) &= ~_BV(bit))
#define sbi(sfr, bit) (_SFR_BYTE(sfr) |= _BV(bit))
#endif

#ifndef VOLTAGE_PIN
#define VOLTAGE_PIN A0
#endif

#ifndef CURRENT_PIN
#define CURRENT_PIN A1
#endif

#define INSTANTANEOUS_MODE 'I'
#define AGREGATE_MODE 'A'

struct PowerMeter {
    unsigned short int fake;
    char mode;
    unsigned short int num_waves;
    unsigned short int num_cycles;
};

typedef void (*sample_function) (void);

extern struct PowerMeter powermeter;

extern sample_function sample;

extern int raw_voltage;
extern int last_raw_voltage;

extern int raw_current;
extern int last_raw_current;

void update_sample_function(void);
void reset_power_meter(void);
void setup_powermeter(void);

#endif
