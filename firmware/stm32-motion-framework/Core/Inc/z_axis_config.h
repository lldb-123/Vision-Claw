#ifndef Z_AXIS_CONFIG_H
#define Z_AXIS_CONFIG_H
/* TIM3 CH1, PA6. Physical direction: UP = 180 deg, DOWN = 0 deg. */
#define Z_SERVO_PULSE_MIN_US 500u
#define Z_SERVO_PULSE_MAX_US 2500u
#define Z_MIN_US Z_SERVO_PULSE_MIN_US
#define Z_MAX_US Z_SERVO_PULSE_MAX_US
#define Z_START_US 1500u
#define Z_UP_US 2500u
#define Z_DOWN_US 500u
#define Z_MAX_DURATION_MS 30000u
#endif
