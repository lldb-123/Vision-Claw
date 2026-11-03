#ifndef MOTION_CONTROL_H
#define MOTION_CONTROL_H
#include <stdint.h>
#include <stdbool.h>

typedef enum { MOTION_AXIS_X=0, MOTION_AXIS_Y=1, MOTION_AXIS_COUNT=2 } motion_axis_id_t;
typedef enum { AXIS_IDLE=0, AXIS_MOVING, AXIS_HOMING, AXIS_LIMIT, AXIS_ESTOP, AXIS_FAULT } motion_axis_state_t;
typedef struct { int32_t position, target; float speed, max_speed, accel; motion_axis_state_t state; bool limit_min, limit_max; } motion_axis_t;
void Motion_Init(void);
void Motion_Start(void);
void Motion_TickISR(void);
void Motion_Service(void);
bool Motion_MoveRelative(motion_axis_id_t id, int32_t steps, float speed);
bool Motion_Goto(motion_axis_id_t id, int32_t position, float speed);
bool Motion_Home(motion_axis_id_t id);
void Motion_Stop(motion_axis_id_t id);
void Motion_EStop(void);
const motion_axis_t *Motion_GetAxis(motion_axis_id_t id);
#endif
