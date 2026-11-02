#include "motion_control.h"
#include "motion_config.h"
#include "stm32f4xx_hal.h"
#include <math.h>

static motion_axis_t ax[MOTION_AXIS_COUNT];
static uint32_t phase[MOTION_AXIS_COUNT], high_ticks;
static GPIO_TypeDef *step_port[] = {X_STEP_GPIO_Port,Y_STEP_GPIO_Port};
static uint16_t step_pin[] = {X_STEP_Pin,Y_STEP_Pin};
static GPIO_TypeDef *dir_port[] = {X_DIR_GPIO_Port,Y_DIR_GPIO_Port};
static uint16_t dir_pin[] = {X_DIR_Pin,Y_DIR_Pin};
static bool home_dir[MOTION_AXIS_COUNT] = {false,false};
static bool axis_limit(motion_axis_id_t id, int dir) { GPIO_PinState a,b; if(id==MOTION_AXIS_X){a=HAL_GPIO_ReadPin(X_MIN_GPIO_Port,X_MIN_Pin); b=HAL_GPIO_ReadPin(X_MAX_GPIO_Port,X_MAX_Pin);} else {a=HAL_GPIO_ReadPin(Y_MIN_GPIO_Port,Y_MIN_Pin); b=HAL_GPIO_ReadPin(Y_MAX_GPIO_Port,Y_MAX_Pin);} return (dir<0&&a==MOTION_LIMIT_ACTIVE)||(dir>0&&b==MOTION_LIMIT_ACTIVE); }
void Motion_Init(void){ high_ticks=(MOTION_TICK_HZ*MOTION_STEP_HIGH_US)/1000000u; if(!high_ticks)high_ticks=1; for(int i=0;i<2;i++){ax[i]=(motion_axis_t){0,0,0,2000,4000,AXIS_IDLE,0,0};phase[i]=0;} }
void Motion_Start(void){ HAL_TIM_Base_Start_IT(&htim6); }
static bool valid(motion_axis_id_t id,float s){return id<2 && s>=MOTION_MIN_SPEED && s<=MOTION_MAX_SPEED;}
bool Motion_MoveRelative(motion_axis_id_t id,int32_t n,float s){if(!valid(id,s)||ax[id].state==AXIS_ESTOP)return false; ax[id].target=ax[id].position+n; ax[id].max_speed=s; ax[id].state=AXIS_MOVING; return true;}
bool Motion_Goto(motion_axis_id_t id,int32_t p,float s){if(!valid(id,s)||ax[id].state==AXIS_ESTOP)return false; ax[id].target=p; ax[id].max_speed=s; ax[id].state=AXIS_MOVING; return true;}
bool Motion_Home(motion_axis_id_t id){if(id>1||ax[id].state==AXIS_ESTOP)return false; ax[id].target=home_dir[id]?-200000:200000; ax[id].max_speed=300; ax[id].state=AXIS_HOMING; return true;}
void Motion_Stop(motion_axis_id_t id){if(id<2&&ax[id].state!=AXIS_ESTOP){ax[id].target=ax[id].position; ax[id].state=AXIS_IDLE; HAL_GPIO_WritePin(step_port[id],step_pin[id],GPIO_PIN_RESET);}}
void Motion_EStop(void){for(int i=0;i<2;i++){ax[i].state=AXIS_ESTOP; HAL_GPIO_WritePin(step_port[i],step_pin[i],GPIO_PIN_RESET);}}
const motion_axis_t *Motion_GetAxis(motion_axis_id_t id){return id<2?&ax[id]:0;}
void Motion_TickISR(void){ if(HAL_GPIO_ReadPin(ESTOP_GPIO_Port,ESTOP_Pin)==MOTION_ESTOP_ACTIVE){Motion_EStop();return;} for(int i=0;i<2;i++){motion_axis_t *a=&ax[i]; if(a->state!=AXIS_MOVING&&a->state!=AXIS_HOMING)continue; int d=(a->target>a->position)?1:-1; if(a->target==a->position){a->state=AXIS_IDLE;continue;} if(axis_limit((motion_axis_id_t)i,d)){a->state=AXIS_LIMIT;continue;} HAL_GPIO_WritePin(dir_port[i],dir_pin[i],d>0?GPIO_PIN_SET:GPIO_PIN_RESET); uint32_t interval=(uint32_t)((float)MOTION_TICK_HZ/a->max_speed); if(interval<high_ticks+1)interval=high_ticks+1; if(++phase[i]>=interval){phase[i]=0;HAL_GPIO_WritePin(step_port[i],step_pin[i],GPIO_PIN_SET); HAL_GPIO_WritePin(step_port[i],step_pin[i],GPIO_PIN_RESET); a->position+=d; if(a->state==AXIS_HOMING&&axis_limit((motion_axis_id_t)i,d)){a->position=0;a->target=0;a->state=AXIS_IDLE;}}}}
void Motion_Service(void){for(int i=0;i<2;i++){ax[i].limit_min=(HAL_GPIO_ReadPin(i?Y_MIN_GPIO_Port:X_MIN_GPIO_Port,i?Y_MIN_Pin:X_MIN_Pin)==MOTION_LIMIT_ACTIVE);ax[i].limit_max=(HAL_GPIO_ReadPin(i?Y_MAX_GPIO_Port:X_MAX_GPIO_Port,i?Y_MAX_Pin:X_MAX_Pin)==MOTION_LIMIT_ACTIVE);}}
