#ifndef STM32_ACTUATORS_H
#define STM32_ACTUATORS_H
#include <stdint.h>
#include "stm32f4xx_hal.h"
typedef enum { SERVO_MG90S=0, SERVO_DS3120=1 } servo_id_t;
extern TIM_HandleTypeDef htim3;
void Servo_Init(void);
void Servo_SetPulseUs(servo_id_t id, uint16_t pulse_us);
void Servo_SetAngle(servo_id_t id, float angle);
#endif
