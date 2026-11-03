#include "stm32_actuators.h"
#define SERVO_MG90S_CH TIM_CHANNEL_1
#define SERVO_DS3120_CH TIM_CHANNEL_2
static uint32_t clamp_u32(uint32_t x,uint32_t a,uint32_t b){return x<a?a:(x>b?b:x);}
void Servo_Init(void){HAL_TIM_PWM_Start(&htim3,SERVO_MG90S_CH);HAL_TIM_PWM_Start(&htim3,SERVO_DS3120_CH);Servo_SetPulseUs(SERVO_MG90S,1500);Servo_SetPulseUs(SERVO_DS3120,1500);}
void Servo_SetPulseUs(servo_id_t id,uint16_t us){uint32_t v=clamp_u32(us,500,2500);__HAL_TIM_SET_COMPARE(&htim3,id==SERVO_MG90S?SERVO_MG90S_CH:SERVO_DS3120_CH,v);}
void Servo_SetAngle(servo_id_t id,float angle){if(angle<0)angle=0;if(angle>180)angle=180;Servo_SetPulseUs(id,(uint16_t)(500.0f+angle*2000.0f/180.0f));}
