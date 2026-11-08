#include "motion_control.h"
#include "motion_config.h"
#include "stm32f4xx_hal.h"
#include <math.h>
#include <limits.h>

static motion_axis_t ax[MOTION_AXIS_COUNT];
static uint32_t phase[MOTION_AXIS_COUNT], high_ticks, pulse_left[MOTION_AXIS_COUNT];
static uint32_t home_ticks[MOTION_AXIS_COUNT];
static bool stopping[MOTION_AXIS_COUNT];
static unsigned home_stage[MOTION_AXIS_COUNT];
static uint32_t enter(void){uint32_t p=__get_PRIMASK();__disable_irq();return p;}
static void leave(uint32_t p){__set_PRIMASK(p);}
static GPIO_TypeDef *step_port[] = {X_STEP_GPIO_Port,Y_STEP_GPIO_Port};
static uint16_t step_pin[] = {X_STEP_Pin,Y_STEP_Pin};
static GPIO_TypeDef *dir_port[] = {X_DIR_GPIO_Port,Y_DIR_GPIO_Port};
static uint16_t dir_pin[] = {X_DIR_Pin,Y_DIR_Pin};

static bool axis_limit(motion_axis_id_t id, int dir) { GPIO_PinState a,b; if(id==MOTION_AXIS_X){a=HAL_GPIO_ReadPin(X_MIN_GPIO_Port,X_MIN_Pin); b=HAL_GPIO_ReadPin(X_MAX_GPIO_Port,X_MAX_Pin);} else {a=HAL_GPIO_ReadPin(Y_MIN_GPIO_Port,Y_MIN_Pin); b=HAL_GPIO_ReadPin(Y_MAX_GPIO_Port,Y_MAX_Pin);} return (dir<0&&a==MOTION_LIMIT_ACTIVE)||(dir>0&&b==MOTION_LIMIT_ACTIVE); }
void Motion_Init(void){ high_ticks=(MOTION_TICK_HZ*MOTION_STEP_HIGH_US+999999u)/1000000u; if(!high_ticks)high_ticks=1; for(int i=0;i<2;i++){ax[i]=(motion_axis_t){0,0,0,2000,4000,AXIS_IDLE,0,0,0};phase[i]=0;pulse_left[i]=0;stopping[i]=false;home_stage[i]=0;HAL_GPIO_WritePin(step_port[i],step_pin[i],GPIO_PIN_RESET);} }
void Motion_Start(void){ HAL_TIM_Base_Start_IT(&htim6); }
static bool valid(motion_axis_id_t id,float s){return (unsigned)id<2 && isfinite(s) && s>=MOTION_MIN_SPEED && s<=MOTION_MAX_SPEED;}
bool Motion_Goto(motion_axis_id_t id,int32_t p,float s){
 if(!valid(id,s))return false;
 uint32_t k=enter();
 bool ok=ax[id].state==AXIS_IDLE||ax[id].state==AXIS_LIMIT;
 int d=p>ax[id].position?1:-1;
 if(p!=ax[id].position&&axis_limit(id,d))ok=false;
 if(ok&&p!=ax[id].position){ax[id].target=p;ax[id].max_speed=s;ax[id].speed=MOTION_MIN_SPEED;ax[id].state=AXIS_MOVING;phase[id]=0;stopping[id]=false;HAL_GPIO_WritePin(dir_port[id],dir_pin[id],d>0?GPIO_PIN_SET:GPIO_PIN_RESET);}
 leave(k);return ok;
}
bool Motion_MoveRelative(motion_axis_id_t id,int32_t n,float s){
 if((unsigned)id>=2)return false;
 uint32_t k=enter();int64_t target=(int64_t)ax[id].position+n;
 bool ok=target>=INT32_MIN&&target<=INT32_MAX&&Motion_Goto(id,(int32_t)target,s);leave(k);return ok;
}
bool Motion_Home(motion_axis_id_t id){
 if((unsigned)id>=2)return false;
 uint32_t k=enter();
 bool ok=ax[id].state==AXIS_IDLE||ax[id].state==AXIS_LIMIT;
 if(ok){ax[id].state=AXIS_HOMING;ax[id].homed=false;ax[id].speed=300;home_ticks[id]=0;home_stage[id]=axis_limit(id,-1)?1:2;phase[id]=0;HAL_GPIO_WritePin(dir_port[id],dir_pin[id],home_stage[id]==1?GPIO_PIN_SET:GPIO_PIN_RESET);}
 leave(k);return ok;
}
void Motion_Stop(motion_axis_id_t id){if((unsigned)id>=2)return;uint32_t k=enter();if(ax[id].state==AXIS_MOVING)stopping[id]=true;else if(ax[id].state==AXIS_HOMING){ax[id].state=AXIS_IDLE;ax[id].speed=0;ax[id].target=ax[id].position;}leave(k);}
void Motion_EStop(void){for(int i=0;i<2;i++){ax[i].state=AXIS_ESTOP;ax[i].homed=false;ax[i].speed=0;pulse_left[i]=0; HAL_GPIO_WritePin(step_port[i],step_pin[i],GPIO_PIN_RESET);}}
const motion_axis_t *Motion_GetAxis(motion_axis_id_t id){return (unsigned)id<2?&ax[id]:0;}
static void done(int i,motion_axis_state_t state){ax[i].state=state;ax[i].speed=0;ax[i].target=ax[i].position;stopping[i]=false;}
bool Motion_ClearFault(void){uint32_t k=enter();bool ok=HAL_GPIO_ReadPin(ESTOP_GPIO_Port,ESTOP_Pin)!=MOTION_ESTOP_ACTIVE;if(ok)for(int i=0;i<2;i++)if(ax[i].state==AXIS_FAULT||ax[i].state==AXIS_ESTOP)done(i,AXIS_IDLE);leave(k);return ok;}
bool Motion_Snapshot(motion_axis_id_t id,motion_axis_t *out){if((unsigned)id>=2||!out)return false;uint32_t k=enter();*out=ax[id];leave(k);return true;}
void Motion_TickISR(void){
 if(HAL_GPIO_ReadPin(ESTOP_GPIO_Port,ESTOP_Pin)==MOTION_ESTOP_ACTIVE){Motion_EStop();return;}
 for(int i=0;i<2;i++){
  bool falling=false;if(pulse_left[i]&&!--pulse_left[i]){HAL_GPIO_WritePin(step_port[i],step_pin[i],GPIO_PIN_RESET);falling=true;}
  motion_axis_t *a=&ax[i];if(a->state!=AXIS_MOVING&&a->state!=AXIS_HOMING)continue;
  int d;
  if(a->state==AXIS_HOMING){
   if(++home_ticks[i]>30u*MOTION_TICK_HZ){done(i,AXIS_FAULT);continue;}
   bool hit=axis_limit((motion_axis_id_t)i,-1);
   d=(home_stage[i]==1||home_stage[i]==3)?1:-1;
   if(d>0&&axis_limit((motion_axis_id_t)i,1)){done(i,AXIS_FAULT);continue;}
   if(d>0&&!hit){home_stage[i]=home_stage[i]==1?2:4;a->speed=home_stage[i]==4?100:300;phase[i]=0;HAL_GPIO_WritePin(dir_port[i],dir_pin[i],GPIO_PIN_RESET);continue;}
   if(d<0&&hit){if(home_stage[i]==4){a->position=0;done(i,AXIS_IDLE);a->homed=true;}else{home_stage[i]=3;phase[i]=0;HAL_GPIO_WritePin(dir_port[i],dir_pin[i],GPIO_PIN_SET);}continue;}
  }else{
   int64_t delta=(int64_t)a->target-a->position;if(!delta){done(i,AXIS_IDLE);continue;}d=delta>0?1:-1;
   if(axis_limit((motion_axis_id_t)i,d)){a->homed=false;done(i,AXIS_LIMIT);continue;}
   float distance=(float)(delta>0?delta:-delta);float dv=a->accel/MOTION_TICK_HZ;
   if(stopping[i]||a->speed*a->speed>=2*a->accel*distance){a->speed-=dv;if(a->speed<MOTION_MIN_SPEED){if(stopping[i]){done(i,AXIS_IDLE);continue;}a->speed=MOTION_MIN_SPEED;}}
   else{a->speed+=dv;if(a->speed>a->max_speed)a->speed=a->max_speed;}
  }
  uint32_t interval=(uint32_t)(MOTION_TICK_HZ/a->speed);if(interval<high_ticks+1)interval=high_ticks+1;
  if(++phase[i]>=interval&&!pulse_left[i]&&!falling){
   if((d>0&&a->position==INT32_MAX)||(d<0&&a->position==INT32_MIN)){a->homed=false;done(i,AXIS_FAULT);continue;}
   phase[i]=0;HAL_GPIO_WritePin(step_port[i],step_pin[i],GPIO_PIN_SET);pulse_left[i]=high_ticks;a->position+=d;
  }
 }
}
void Motion_Service(void){for(int i=0;i<2;i++){ax[i].limit_min=(HAL_GPIO_ReadPin(i?Y_MIN_GPIO_Port:X_MIN_GPIO_Port,i?Y_MIN_Pin:X_MIN_Pin)==MOTION_LIMIT_ACTIVE);ax[i].limit_max=(HAL_GPIO_ReadPin(i?Y_MAX_GPIO_Port:X_MAX_GPIO_Port,i?Y_MAX_Pin:X_MAX_Pin)==MOTION_LIMIT_ACTIVE);}}

