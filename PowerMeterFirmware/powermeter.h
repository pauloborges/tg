#ifndef POWERMETER_H
#define POWERMETER_H

#include "config.h"
#include "util.h"

// --------------------------------------------------------
// Configuration variables

extern uint8_t MODE;       // MODE_RAW, MODE_INST or MODE_AGRE
extern uint8_t FAKE;       // boolean
extern uint16_t QUANTITY;  // waves or samples (MODE)

extern float PHASE_CORRECTION;
extern float VOLTAGE_OFFSET;
extern float CURRENT_OFFSET;

extern float VOLTAGE_ZERO;

// --------------------------------------------------------
// Current sampling function

typedef void (*sample_function) (void);
extern sample_function sample;

// --------------------------------------------------------
// Sampling-related variables

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

// --------------------------------------------------------
// External API

#define ADC_MAX_VALUE 1023

#define DONT_WAIT_NEW_WAVE 0x00
#define WAIT_NEW_WAVE      0x01

void update_sample_function(void);
uint8_t reset_powermeter(uint8_t);
void setup_powermeter(void);

#define NEW_WAVE_STARTING()                                 \
    (last_voltage <= VOLTAGE_ZERO                           \
        && voltage.n >= VOLTAGE_ZERO)                       \

#define RESET_ACCUMULATORS()                                \
    do {                                                    \
        sum_rms_voltage = 0.0;                              \
        sum_rms_current = 0.0;                              \
        sum_real_power = 0.0;                               \
    } while (0)

#endif
