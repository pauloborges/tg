#ifndef POWERMETER_H
#define POWERMETER_H

#include "config.h"
#include "util.h"

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

#define INSTANTANEOUS_MODE 0x01
#define AGREGATE_MODE      0x02

struct PowerMeter {
    uint8_t action;
    uint8_t fake;
    uint8_t mode;
    uint16_t num_waves;
    uint16_t num_cycles;
};

typedef void (*sample_function) (void);

extern struct PowerMeter powermeter;

extern sample_function sample;

extern int raw_voltage;
extern int last_raw_voltage;

extern int raw_current;
extern int last_raw_current;

extern float fixed_voltage;
extern float last_fixed_voltage;

extern float_t voltage;
extern float last_voltage;

extern float_t current;
extern float last_current;

extern float sum_rms_voltage;
extern float_t rms_voltage;

extern float sum_rms_current;
extern float_t rms_current;

extern float sum_real_power;
extern float_t real_power;

void update_sample_function(void);
void reset_powermeter(void);
void setup_powermeter(void);

#define NEW_WAVE_STARTING()                                 \
    (last_voltage <= 0 && voltage.number >= 0)

#define RESET_ACCUMULATORS()                                \
    do {                                                    \
        sum_rms_voltage = 0.0;                              \
        sum_rms_current = 0.0;                              \
        sum_real_power = 0.0;                               \
    } while (0)

#endif
