#ifndef MOTION_CONFIG_H
#define MOTION_CONFIG_H
#include "stm32f4xx_hal.h"

/* Replace these handles/pins with CubeMX generated resources. */
extern TIM_HandleTypeDef htim6;
extern UART_HandleTypeDef huart2;
#define MOTION_TICK_HZ       50000u   /* 20 us ISR period */
#define MOTION_STEPS_PER_REV 1600L
#define MOTION_STEP_HIGH_US  5u
#define MOTION_MAX_SPEED     12000.0f
#define MOTION_MIN_SPEED     100.0f
#define X_STEPS_PER_MM       80.0f
#define Y_STEPS_PER_MM       80.0f
#define X_MIN_MM             0.0f
#define Y_MIN_MM             0.0f
#define X_MAX_MM             260.0f
#define Y_MAX_MM             260.0f
#define MOTION_LIMIT_TRIGGER_TICKS  50u
#define MOTION_LIMIT_DEBOUNCE_TICKS 500u
#define MOTION_HOME_MAX_STEPS       ((uint32_t)((X_MAX_MM + 20.0f) * X_STEPS_PER_MM))
#define MOTION_HOME_TIMEOUT_S       120u
#define X_STEP_GPIO_Port GPIOA
#define X_STEP_Pin       GPIO_PIN_0
#define X_DIR_GPIO_Port  GPIOA
#define X_DIR_Pin        GPIO_PIN_1
#define Y_STEP_GPIO_Port GPIOA
#define Y_STEP_Pin       GPIO_PIN_2
#define Y_DIR_GPIO_Port  GPIOA
#define Y_DIR_Pin        GPIO_PIN_3
#define X_MIN_GPIO_Port  GPIOB
#define X_MIN_Pin        GPIO_PIN_0
#define X_MAX_GPIO_Port  GPIOB
#define X_MAX_Pin        GPIO_PIN_1
#define Y_MIN_GPIO_Port  GPIOB
#define Y_MIN_Pin        GPIO_PIN_6
#define Y_MAX_GPIO_Port  GPIOB
#define Y_MAX_Pin        GPIO_PIN_3
#define ESTOP_GPIO_Port  GPIOB
#define ESTOP_Pin        GPIO_PIN_4
#define MOTION_LIMIT_ACTIVE GPIO_PIN_RESET
#define MOTION_ESTOP_ACTIVE GPIO_PIN_RESET
#endif
