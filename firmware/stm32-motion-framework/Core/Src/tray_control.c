#include "tray_control.h"
#include "tray_config.h"
#include "stm32_actuators.h"
#include "stm32f4xx_hal.h"
#include <math.h>

static tray_status_t status;
static uint32_t stop_at;

static uint32_t enter(void)
{
    uint32_t p = __get_PRIMASK();
    __disable_irq();
    return p;
}

static void leave(uint32_t p) { __set_PRIMASK(p); }

static bool valid_speed(uint8_t speed) { return speed > 0u && speed <= 100u; }

static uint16_t pulse_for(tray_dir_t direction, uint8_t speed)
{
    if (direction == TRAY_DIR_CW) {
        uint16_t span = (uint16_t)(speed * (TRAY_FORWARD_MAX_PULSE_US -
                                             TRAY_STOP_PULSE_US - TRAY_DEADBAND_US) / 100u);
        return (uint16_t)(TRAY_STOP_PULSE_US + TRAY_DEADBAND_US + span);
    }
    uint16_t span = (uint16_t)(speed * (TRAY_STOP_PULSE_US -
                                         TRAY_REVERSE_MIN_PULSE_US - TRAY_DEADBAND_US) / 100u);
    return (uint16_t)(TRAY_STOP_PULSE_US - TRAY_DEADBAND_US - span);
}

void Tray_Init(void)
{
    status = (tray_status_t){TRAY_IDLE, TRAY_DIR_NONE, 0u,
                             TRAY_STOP_PULSE_US, 0u, true};
    stop_at = 0u;
    (void)Servo_SetPulseUs(TRAY_SERVO_ID, TRAY_STOP_PULSE_US);
}

bool Tray_Start(tray_dir_t direction, uint8_t speed, uint32_t duration_ms)
{
    if ((direction != TRAY_DIR_CW && direction != TRAY_DIR_CCW) ||
        !valid_speed(speed) || duration_ms == 0u ||
        duration_ms > TRAY_MAX_DURATION_MS) {
        return false;
    }
    uint32_t p = enter();
    bool ok = status.state != TRAY_ESTOP;
    if (ok) {
        uint16_t pulse = pulse_for(direction, speed);
        ok = Servo_SetPulseUs(TRAY_SERVO_ID, pulse);
        if (ok) {
            status.state = TRAY_RUNNING;
            status.direction = direction;
            status.speed = speed;
            status.pulse_us = pulse;
            status.remaining_ms = duration_ms;
            stop_at = HAL_GetTick() + duration_ms;
        }
    }
    leave(p);
    return ok;
}

bool Tray_StartAngle(tray_dir_t direction, float angle_deg, uint8_t speed)
{
    if (!isfinite(angle_deg) || angle_deg <= 0.0f || angle_deg > 3600.0f ||
        !valid_speed(speed)) {
        return false;
    }
    float duration = angle_deg * TRAY_MS_PER_DEG_AT_FULL_SPEED * 100.0f /
                     (float)speed;
    if (duration < 1.0f || duration > (float)TRAY_MAX_DURATION_MS) {
        return false;
    }
    return Tray_Start(direction, speed, (uint32_t)(duration + 0.5f));
}

void Tray_Stop(void)
{
    uint32_t p = enter();
    (void)Servo_SetPulseUs(TRAY_SERVO_ID, TRAY_STOP_PULSE_US);
    status.state = TRAY_IDLE;
    status.direction = TRAY_DIR_NONE;
    status.speed = 0u;
    status.pulse_us = TRAY_STOP_PULSE_US;
    status.remaining_ms = 0u;
    stop_at = 0u;
    leave(p);
}

void Tray_EStop(void)
{
    uint32_t p = enter();
    (void)Servo_SetPulseUs(TRAY_SERVO_ID, TRAY_STOP_PULSE_US);
    status.state = TRAY_ESTOP;
    status.direction = TRAY_DIR_NONE;
    status.speed = 0u;
    status.pulse_us = TRAY_STOP_PULSE_US;
    status.remaining_ms = 0u;
    stop_at = 0u;
    leave(p);
}

bool Tray_ClearFault(void)
{
    uint32_t p = enter();
    bool ok = status.state == TRAY_ESTOP;
    if (ok) {
        ok = Servo_ClearFault();
        if (ok) {
            status.state = TRAY_IDLE;
            status.direction = TRAY_DIR_NONE;
        }
    }
    leave(p);
    return ok;
}

void Tray_Service(void)
{
    uint32_t now;
    uint32_t p = enter();
    if (status.state != TRAY_RUNNING) {
        leave(p);
        return;
    }
    now = HAL_GetTick();
    if ((int32_t)(now - stop_at) >= 0) {
        leave(p);
        Tray_Stop();
        return;
    }
    status.remaining_ms = stop_at - now;
    leave(p);
}

bool Tray_Snapshot(tray_status_t *out)
{
    if (!out) return false;
    uint32_t p = enter();
    *out = status;
    leave(p);
    return true;
}
