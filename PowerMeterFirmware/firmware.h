#ifndef FIRMWARE_H
#define FIRMWARE_H

#include "Arduino.h"

#define LED_PIN 13

#define STATE_STOPPED  0x00
#define STATE_MONITOR  0x01

void setup_firmware(void);
void change_state(char new_state);

void serialEventRun(void);

typedef void (*current_state_func_t) (void);
extern current_state_func_t current_state_func;

extern uint8_t current_state;

#endif
