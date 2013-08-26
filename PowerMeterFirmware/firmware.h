#ifndef FIRMWARE_H
#define FIRMWARE_H

#define LED_PIN 13

#define STATE_POWERED_ON    1
#define STATE_CONFIG_BAUD   2
#define STATE_UNINITIALIZED 3
#define STATE_STOPPED       4
#define STATE_SNAPSHOT      5
#define STATE_MONITOR       6
#define STATE_RAW           7

typedef void (*current_state_func_t) (void);

void setup_firmware(void);
void change_state(char new_state);

void serialEventRun(void);

extern current_state_func_t current_state_func;

extern char current_state;

#endif
