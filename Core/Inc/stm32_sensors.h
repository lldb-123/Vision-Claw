#ifndef STM32_SENSORS_H
#define STM32_SENSORS_H
#include <stdbool.h>
#include "stm32f4xx_hal.h"
typedef struct { bool photoelectric; bool x_min,x_max,y_min,y_max,estop; } sensor_state_t;
void Sensors_Read(sensor_state_t *s);
#endif
