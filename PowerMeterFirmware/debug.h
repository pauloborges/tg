#ifndef DEBUG_H
#define DEBUG_H

#include "config.h"

#ifdef CONF_DEBUG_ENABLED
#define DEBUG_INIT()                                         \
    do {                                                     \
        Serial.print("DEBUG:");                              \
        Serial.print(__func__);                              \
        Serial.print("(): ");                                \
    } while (0)
#define DEBUG_END(str) do { Serial.println(str); } while (0)
#define DEBUG(str) do { Serial.print(str); } while (0)
#else
#define DEBUG_INIT()
#define DEBUG_END(str)
#define DEBUG(str)
#endif

#endif
