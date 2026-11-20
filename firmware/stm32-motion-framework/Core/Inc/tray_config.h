#ifndef TRAY_CONFIG_H
#define TRAY_CONFIG_H

#include <stdint.h>
#include "stm32_actuators.h"

#define TRAY_SERVO_ID                  SERVO_DS3120_1
#define TRAY_STOP_PULSE_US             1500u
#define TRAY_REVERSE_MIN_PULSE_US      1000u
#define TRAY_FORWARD_MAX_PULSE_US      2000u
#define TRAY_DEADBAND_US               25u
#define TRAY_DEFAULT_DURATION_MS       1000u
#define TRAY_MAX_DURATION_MS           30000u
#define TRAY_MS_PER_DEG_AT_FULL_SPEED  12.0f

#endif
