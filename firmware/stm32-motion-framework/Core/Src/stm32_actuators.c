#include "stm32_actuators.h"
#include "z_axis_config.h"
#include <math.h>

static const uint32_t servo_channels[SERVO_COUNT] = {
    TIM_CHANNEL_1,
    TIM_CHANNEL_2,
    TIM_CHANNEL_3
};

#define SERVO_QUEUE_DEPTH 16u

typedef struct {
    uint16_t target_us;
    uint32_t duration_ms;
} servo_move_request_t;

static servo_status_t servo_status[SERVO_COUNT];
static bool servo_started[SERVO_COUNT];
static uint16_t start_us[SERVO_COUNT];
static uint32_t start_ms[SERVO_COUNT];
static uint32_t duration_ms[SERVO_COUNT];
static servo_move_request_t move_queue[SERVO_COUNT][SERVO_QUEUE_DEPTH];
static uint8_t move_queue_head[SERVO_COUNT];
static uint8_t move_queue_tail[SERVO_COUNT];
static uint8_t move_queue_count[SERVO_COUNT];

static bool valid_id(servo_id_t id)
{
    return (unsigned)id < (unsigned)SERVO_COUNT;
}

static void pulse_range(servo_id_t id, uint16_t *min_us, uint16_t *max_us)
{
    if (id == SERVO_MG90S) {
        *min_us = Z_SERVO_PULSE_MIN_US;
        *max_us = Z_SERVO_PULSE_MAX_US;
    } else {
        *min_us = SERVO_PULSE_MIN_US;
        *max_us = SERVO_PULSE_MAX_US;
    }
}

static bool valid_pulse(servo_id_t id, uint16_t us)
{
    uint16_t min_us;
    uint16_t max_us;
    pulse_range(id, &min_us, &max_us);
    return us >= min_us && us <= max_us;
}

static uint32_t lock(void)
{
    uint32_t primask = __get_PRIMASK();
    __disable_irq();
    return primask;
}

static void unlock(uint32_t primask)
{
    __set_PRIMASK(primask);
}

bool Servo_Init(void)
{
    for (unsigned i = 0; i < (unsigned)SERVO_COUNT; i++) {
        servo_started[i] = false;
        servo_status[i] = (servo_status_t){
            .pulse_us = SERVO_PULSE_INITIAL_US,
            .target_us = SERVO_PULSE_INITIAL_US,
            .enabled = false,
            .busy = false,
            .estop = false
        };
        start_us[i] = SERVO_PULSE_INITIAL_US;
        start_ms[i] = 0;
        duration_ms[i] = 0;
        move_queue_head[i] = 0;
        move_queue_tail[i] = 0;
        move_queue_count[i] = 0;

        __HAL_TIM_SET_COMPARE(&htim3, servo_channels[i], SERVO_PULSE_INITIAL_US);
        if (HAL_TIM_PWM_Start(&htim3, servo_channels[i]) == HAL_OK) {
            servo_started[i] = true;
            servo_status[i].enabled = true;
        } else {
            for (unsigned j = 0; j < i; j++) {
                if (servo_started[j]) {
                    (void)HAL_TIM_PWM_Stop(&htim3, servo_channels[j]);
                    servo_started[j] = false;
                }
            }

            for (unsigned j = 0; j < (unsigned)SERVO_COUNT; j++) {
                __HAL_TIM_SET_COMPARE(&htim3, servo_channels[j], 0u);
                servo_status[j].pulse_us = 0u;
                servo_status[j].target_us = 0u;
                servo_status[j].enabled = false;
                servo_status[j].busy = false;
                servo_status[j].estop = false;
                servo_started[j] = false;
                start_us[j] = 0u;
                start_ms[j] = 0u;
                duration_ms[j] = 0u;
            }
            return false;
        }
    }

    return true;
}

bool Servo_EnableById(servo_id_t id)
{
    if (!valid_id(id)) {
        return false;
    }

    uint32_t primask = lock();
    bool ok = !servo_status[id].estop;
    if (ok && !servo_started[id]) {
        ok = HAL_TIM_PWM_Start(&htim3, servo_channels[id]) == HAL_OK;
        if (ok) {
            servo_started[id] = true;
            servo_status[id].enabled = true;
        }
    }
    unlock(primask);
    return ok;
}

bool Servo_Enable(void)
{
    return Servo_EnableById(SERVO_MG90S);
}

bool Servo_MoveTo(servo_id_t id, uint16_t pulse_us, uint32_t move_ms)
{
    if (!valid_id(id) || !valid_pulse(id, pulse_us) ||
        move_ms < 20u || move_ms > Z_MAX_DURATION_MS) {
        return false;
    }

    uint32_t primask = lock();
    bool ok = servo_status[id].enabled && !servo_status[id].estop;
    if (ok) {
        if (!servo_status[id].busy) {
            start_us[id] = servo_status[id].pulse_us;
            servo_status[id].target_us = pulse_us;
            duration_ms[id] = move_ms;
            start_ms[id] = HAL_GetTick();
            servo_status[id].busy = true;
        } else if (move_queue_count[id] < SERVO_QUEUE_DEPTH) {
            uint8_t tail = move_queue_tail[id];
            move_queue[id][tail].target_us = pulse_us;
            move_queue[id][tail].duration_ms = move_ms;
            move_queue_tail[id] = (uint8_t)((tail + 1u) % SERVO_QUEUE_DEPTH);
            move_queue_count[id]++;
        } else {
            ok = false;
        }
    }
    unlock(primask);
    return ok;
}

bool Servo_Move(uint16_t pulse_us, uint32_t move_ms)
{
    return Servo_MoveTo(SERVO_MG90S, pulse_us, move_ms);
}

void Servo_StopById(servo_id_t id)
{
    if (!valid_id(id)) {
        return;
    }

    uint32_t primask = lock();
    servo_status[id].busy = false;
    servo_status[id].target_us = servo_status[id].pulse_us;
    move_queue_head[id] = 0;
    move_queue_tail[id] = 0;
    move_queue_count[id] = 0;
    unlock(primask);
}

void Servo_Stop(void)
{
    Servo_StopById(SERVO_MG90S);
}

void Servo_EStop(void)
{
    uint32_t primask = lock();
    for (unsigned i = 0; i < (unsigned)SERVO_COUNT; i++) {
        servo_status[i].estop = true;
        servo_status[i].busy = false;
        servo_status[i].target_us = servo_status[i].pulse_us;
        move_queue_head[i] = 0;
        move_queue_tail[i] = 0;
        move_queue_count[i] = 0;
    }
    unlock(primask);
}

bool Servo_ClearFault(void)
{
    uint32_t primask = lock();
    for (unsigned i = 0; i < (unsigned)SERVO_COUNT; i++) {
        servo_status[i].estop = false;
    }
    unlock(primask);
    return true;
}

void Servo_Service(void)
{
    uint32_t primask = lock();

    for (unsigned i = 0; i < (unsigned)SERVO_COUNT; i++) {
        if (servo_status[i].estop) {
            continue;
        }

        if (servo_status[i].busy) {
            uint32_t elapsed = HAL_GetTick() - start_ms[i];
            if (elapsed >= duration_ms[i]) {
                servo_status[i].pulse_us = servo_status[i].target_us;
                servo_status[i].busy = false;
            } else {
                int32_t delta = (int32_t)servo_status[i].target_us - start_us[i];
                servo_status[i].pulse_us = (uint16_t)(
                    (int32_t)start_us[i] +
                    delta * (int32_t)elapsed / (int32_t)duration_ms[i]
                );
            }
        }

        if (!servo_status[i].busy && move_queue_count[i] > 0u) {
            uint8_t head = move_queue_head[i];
            start_us[i] = servo_status[i].pulse_us;
            servo_status[i].target_us = move_queue[i][head].target_us;
            duration_ms[i] = move_queue[i][head].duration_ms;
            start_ms[i] = HAL_GetTick();
            servo_status[i].busy = true;
            move_queue_head[i] =
                (uint8_t)((head + 1u) % SERVO_QUEUE_DEPTH);
            move_queue_count[i]--;
        }

        __HAL_TIM_SET_COMPARE(
            &htim3, servo_channels[i], servo_status[i].pulse_us
        );
    }

    unlock(primask);
}

bool Servo_SnapshotById(servo_id_t id, servo_status_t *out)
{
    if (!valid_id(id) || !out) {
        return false;
    }

    uint32_t primask = lock();
    *out = servo_status[id];
    unlock(primask);
    return true;
}

void Servo_Snapshot(servo_status_t *out)
{
    (void)Servo_SnapshotById(SERVO_MG90S, out);
}

bool Servo_SetPulseUs(servo_id_t id, uint16_t us)
{
    if (!valid_id(id) || !valid_pulse(id, us)) {
        return false;
    }

    uint32_t primask = lock();
    bool ok = servo_status[id].enabled && !servo_status[id].estop;
    if (ok) {
        servo_status[id].pulse_us = us;
        servo_status[id].target_us = us;
        servo_status[id].busy = false;
        move_queue_head[id] = 0;
        move_queue_tail[id] = 0;
        move_queue_count[id] = 0;
        __HAL_TIM_SET_COMPARE(&htim3, servo_channels[id], us);
    }
    unlock(primask);
    return ok;
}

bool Servo_SetAngle(servo_id_t id, float angle)
{
    if (!valid_id(id) || !isfinite(angle) || angle < 0.0f || angle > 180.0f) {
        return false;
    }

    uint16_t min_us;
    uint16_t max_us;
    pulse_range(id, &min_us, &max_us);
    uint16_t us = (uint16_t)(
        min_us + angle * (max_us - min_us) / 180.0f
    );
    return Servo_MoveTo(id, us, 500u);
}
