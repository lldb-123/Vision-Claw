#include "stm32_actuators.h"
#include "z_axis_config.h"
#include <math.h>
static servo_status_t z;
static uint16_t start_us;
static uint32_t start_ms,duration;
static uint32_t lock(void){uint32_t k=__get_PRIMASK();__disable_irq();return k;}
static void unlock(uint32_t k){__set_PRIMASK(k);}
void Servo_Init(void){z=(servo_status_t){.pulse_us=Z_START_US,.target_us=Z_START_US};__HAL_TIM_SET_COMPARE(&htim3,TIM_CHANNEL_1,Z_START_US);}
bool Servo_Enable(void){uint32_t k=lock();bool ok=!z.estop;if(ok&&!z.enabled){ok=HAL_TIM_PWM_Start(&htim3,TIM_CHANNEL_1)==HAL_OK;if(ok)z.enabled=true;}unlock(k);return ok;}
bool Servo_Move(uint16_t us,uint32_t ms){if(us<Z_MIN_US||us>Z_MAX_US||ms<20||ms>Z_MAX_DURATION_MS)return false;uint32_t k=lock();bool ok=z.enabled&&!z.busy&&!z.estop;if(ok){start_us=z.pulse_us;z.target_us=us;duration=ms;start_ms=HAL_GetTick();z.busy=true;}unlock(k);return ok;}
void Servo_Stop(void){uint32_t k=lock();z.busy=false;z.target_us=z.pulse_us;unlock(k);}
void Servo_EStop(void){uint32_t k=lock();z.estop=true;z.busy=false;z.target_us=z.pulse_us;unlock(k);}
bool Servo_ClearFault(void){uint32_t k=lock();z.estop=false;unlock(k);return true;}
void Servo_Snapshot(servo_status_t *out){if(!out)return;uint32_t k=lock();*out=z;unlock(k);}
void Servo_Service(void){uint32_t k=lock();if(z.busy&&!z.estop){uint32_t elapsed=HAL_GetTick()-start_ms;if(elapsed>=duration){z.pulse_us=z.target_us;z.busy=false;}else{int32_t delta=(int32_t)z.target_us-start_us;z.pulse_us=(uint16_t)((int32_t)start_us+delta*(int32_t)elapsed/(int32_t)duration);}__HAL_TIM_SET_COMPARE(&htim3,TIM_CHANNEL_1,z.pulse_us);}unlock(k);}
bool Servo_SetPulseUs(servo_id_t id,uint16_t us){return id==SERVO_MG90S&&Servo_Move(us,500);}
bool Servo_SetAngle(servo_id_t id,float angle){if(id!=SERVO_MG90S||!isfinite(angle)||angle<0||angle>180)return false;return Servo_Move((uint16_t)(Z_MIN_US+angle*(Z_MAX_US-Z_MIN_US)/180.0f),500);}
