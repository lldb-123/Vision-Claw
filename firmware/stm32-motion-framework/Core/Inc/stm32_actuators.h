#ifndef STM32_ACTUATORS_H
#define STM32_ACTUATORS_H
#include <stdint.h>
#include <stdbool.h>
#include "stm32f4xx_hal.h"

#define SERVO_PULSE_MIN_US      1000u
#define SERVO_PULSE_MAX_US      2000u
#define SERVO_PULSE_INITIAL_US  1500u

typedef enum {
    SERVO_MG90S = 0,
    SERVO_DS3120_1 = 1,
    SERVO_DS3120_2 = 2,
    SERVO_DS3120 = SERVO_DS3120_1,
    SERVO_COUNT = 3
} servo_id_t;

typedef struct { uint16_t pulse_us,target_us; bool enabled,busy,estop; } servo_status_t;
extern TIM_HandleTypeDef htim3;
bool Servo_Init(void);
bool Servo_Enable(void);
bool Servo_EnableById(servo_id_t id);
bool Servo_Move(uint16_t pulse_us,uint32_t duration_ms);
bool Servo_MoveTo(servo_id_t id,uint16_t pulse_us,uint32_t duration_ms);
void Servo_Stop(void);
void Servo_StopById(servo_id_t id);
void Servo_EStop(void);
bool Servo_ClearFault(void);
void Servo_Service(void);
void Servo_Snapshot(servo_status_t *out);
bool Servo_SnapshotById(servo_id_t id,servo_status_t *out);
bool Servo_SetPulseUs(servo_id_t id,uint16_t us);
bool Servo_SetAngle(servo_id_t id,float angle);
#endif
