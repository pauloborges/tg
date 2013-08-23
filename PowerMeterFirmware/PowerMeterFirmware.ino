#include "firmware.h"

void setup()
{
    setup_firmware();
}

void loop()
{
    current_state_func();
}
