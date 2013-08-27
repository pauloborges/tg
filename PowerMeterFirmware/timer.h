#ifndef TIMER_H
#define TIMER_H

#include "util.h"

#define MICRO_TO_SECOND 1000000

#define RESET_ELAPSED_TIME()                                  \
    do {                                                      \
        seconds_base = ((float) micros()) / MICRO_TO_SECOND;  \
        seconds.n = seconds_base;                             \
    } while (0)

#define REFRESH_ELAPSED_TIME()                                \
    do {                                                      \
        seconds.n = ((float) micros()) / MICRO_TO_SECOND      \
                            		- seconds_base;           \
    } while(0)

#define ELAPSED_TIME() (seconds.n)
#define ELAPSED_TIME_B() (seconds.b)

extern float seconds_base;
extern float_t seconds;

#endif
