#include "firmware.h"

void serialEventRun(void)
{
    if (Serial.available() > 0) {
        handle_incoming_data();
    }
} 

void setup()
{
    setup_firmware();
}

void loop()
{
    current_state_func();
}
