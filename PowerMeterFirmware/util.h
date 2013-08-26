#ifndef UTIL_H
#define UTIL_H

#include "Arduino.h"

typedef union {
    uint8_t bytes[4];
    float number;
} float_t;

#endif
