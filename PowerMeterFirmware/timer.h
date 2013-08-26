#ifndef TIMER_H
#define TIMER_H

#include "util.h"

#define MICRO_TO_SECOND 1000000

#define RESET_ELAPSED_TIME()                                  \
    do {                                                      \
        seconds_base = ((float) micros()) / MICRO_TO_SECOND;  \
        seconds.number = seconds_base;                        \
    } while (0)

#define REFRESH_ELAPSED_TIME()                                \
    do {                                                      \
        seconds.number = ((float) micros()) / MICRO_TO_SECOND \
                            		- seconds_base;           \
    } while(0)

#define ELAPSED_TIME() (seconds)

extern float seconds_base;
extern float_t seconds;

#endif
