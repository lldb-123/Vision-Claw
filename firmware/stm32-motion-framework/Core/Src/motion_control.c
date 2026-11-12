#include "motion_control.h"
#include "motion_config.h"
#include "stm32f4xx_hal.h"
#include <math.h>
#include <limits.h>

static motion_axis_t ax[MOTION_AXIS_COUNT];
static uint32_t phase[MOTION_AXIS_COUNT], high_ticks, pulse_left[MOTION_AXIS_COUNT];
static bool stopping[MOTION_AXIS_COUNT];
static uint32_t enter(void){uint32_t p=__get_PRIMASK();__disable_irq();return p;}
static void leave(uint32_t p){__set_PRIMASK(p);}
static GPIO_TypeDef *step_port[] = {X_STEP_GPIO_Port,Y_STEP_GPIO_Port};
static uint16_t step_pin[] = {X_STEP_Pin,Y_STEP_Pin};
static GPIO_TypeDef *dir_port[] = {X_DIR_GPIO_Port,Y_DIR_GPIO_Port};
static uint16_t dir_pin[] = {X_DIR_Pin,Y_DIR_Pin};
static const int32_t min_steps[] = {(int32_t)(X_MIN_MM*X_STEPS_PER_MM),(int32_t)(Y_MIN_MM*Y_STEPS_PER_MM)};
static const int32_t max_steps[] = {(int32_t)(X_MAX_MM*X_STEPS_PER_MM+0.5f),(int32_t)(Y_MAX_MM*Y_STEPS_PER_MM+0.5f)};

static bool in_range(motion_axis_id_t id,int64_t position){return position>=min_steps[id]&&position<=max_steps[id];}
void Motion_Init(void){ high_ticks=(MOTION_TICK_HZ*MOTION_STEP_HIGH_US+999999u)/1000000u; if(!high_ticks)high_ticks=1; for(int i=0;i<2;i++){ax[i]=(motion_axis_t){0,0,0,2000,4000,AXIS_IDLE,0};phase[i]=0;pulse_left[i]=0;stopping[i]=false;HAL_GPIO_WritePin(step_port[i],step_pin[i],GPIO_PIN_RESET);} }
void Motion_Start(void){ HAL_TIM_Base_Start_IT(&htim6); }
static bool valid(motion_axis_id_t id,float s){return (unsigned)id<2 && isfinite(s) && s>=MOTION_MIN_SPEED && s<=MOTION_MAX_SPEED;}
static bool check_goto_locked(motion_axis_id_t id,int32_t p,float s){
 if(!valid(id,s))return false;
 if(!ax[id].homed||ax[id].state!=AXIS_IDLE)return false;
 if(!in_range(id,p))return false;
 return true;
}
static bool check_rel_locked(motion_axis_id_t id,int32_t n,float s){
 if((unsigned)id>=2)return false;
 if(n==0)return ax[id].state==AXIS_IDLE;
 if(!valid(id,s))return false;
 if(ax[id].state!=AXIS_IDLE)return false;
 if(n>max_steps[id]||n<-max_steps[id])return false;
 int64_t target=(int64_t)ax[id].position+n;
 if(!in_range(id,target))return false;
 return true;
}
static void start_move_locked(motion_axis_id_t id,int32_t p,float s,float accel){
 if(p==ax[id].position)return;
 int d=p>ax[id].position?1:-1;
 ax[id].target=p;ax[id].max_speed=s;ax[id].accel=accel;ax[id].speed=MOTION_MIN_SPEED;ax[id].state=AXIS_MOVING;phase[id]=0;stopping[id]=false;
 HAL_GPIO_WritePin(dir_port[id],dir_pin[id],d>0?GPIO_PIN_SET:GPIO_PIN_RESET);
}
const char *Motion_CheckMoveError(motion_axis_id_t id,int32_t v,float s,bool relative){
 if((unsigned)id>=2)return "ERR FORMAT\r\n";
 uint32_t k=enter();
 motion_axis_t a=ax[id];
 int32_t target=relative?(int32_t)((int64_t)a.position+v):v;
 leave(k);
 if(a.state==AXIS_ESTOP)return "ERR ESTOP_ACTIVE\r\n";
 if(a.state==AXIS_FAULT)return id==MOTION_AXIS_X?"ERR X_FAULT\r\n":"ERR Y_FAULT\r\n";
 if(a.state!=AXIS_IDLE)return id==MOTION_AXIS_X?"ERR X_BUSY\r\n":"ERR Y_BUSY\r\n";
 if(!relative&&!a.homed)return id==MOTION_AXIS_X?"ERR X_NOT_HOMED\r\n":"ERR Y_NOT_HOMED\r\n";
 if((relative&&v==0)||(!relative&&v==a.position))return 0;
 if(!valid(id,s))return "ERR SPEED\r\n";
 if(relative){
  int64_t t64=(int64_t)a.position+v;
  if(v>max_steps[id]||v<-max_steps[id]||!in_range(id,t64))return "ERR RANGE\r\n";
 }else if(!in_range(id,target))return "ERR RANGE\r\n";
 return 0;
}
bool Motion_Goto(motion_axis_id_t id,int32_t p,float s){
 if((unsigned)id>=2)return false;
 uint32_t k=enter();
 bool ok=(p==ax[id].position)?(ax[id].homed&&ax[id].state==AXIS_IDLE):check_goto_locked(id,p,s);
 if(ok)start_move_locked(id,p,s,4000.0f);
 leave(k);return ok;
}
bool Motion_MoveRelative(motion_axis_id_t id,int32_t n,float s){
 if((unsigned)id>=2)return false;
 uint32_t k=enter();
 bool ok=check_rel_locked(id,n,s);
 if(ok&&n!=0)start_move_locked(id,ax[id].position+n,s,4000.0f);
 leave(k);return ok;
}
bool Motion_MoveRelativeXY(int32_t nx,float sx,int32_t ny,float sy){
 uint32_t k=enter();
 bool ok=check_rel_locked(MOTION_AXIS_X,nx,sx)&&check_rel_locked(MOTION_AXIS_Y,ny,sy);
 if(ok){
  float dx=fabsf((float)nx),dy=fabsf((float)ny),len=hypotf(dx,dy);
  float ax_acc=(len>0.0f&&nx!=0)?fmaxf(4000.0f*(dx/len),100.0f):4000.0f;
  float ay_acc=(len>0.0f&&ny!=0)?fmaxf(4000.0f*(dy/len),100.0f):4000.0f;
  if(nx!=0)start_move_locked(MOTION_AXIS_X,ax[MOTION_AXIS_X].position+nx,sx,ax_acc);
  if(ny!=0)start_move_locked(MOTION_AXIS_Y,ax[MOTION_AXIS_Y].position+ny,sy,ay_acc);
 }
 leave(k);return ok;
}
bool Motion_GotoXY(int32_t px,float sx,int32_t py,float sy){
 uint32_t k=enter();
 int32_t nx=px-ax[MOTION_AXIS_X].position,ny=py-ax[MOTION_AXIS_Y].position;
 bool ok_x=(nx==0)?(ax[MOTION_AXIS_X].homed&&ax[MOTION_AXIS_X].state==AXIS_IDLE&&in_range(MOTION_AXIS_X,px)):check_goto_locked(MOTION_AXIS_X,px,sx);
 bool ok_y=(ny==0)?(ax[MOTION_AXIS_Y].homed&&ax[MOTION_AXIS_Y].state==AXIS_IDLE&&in_range(MOTION_AXIS_Y,py)):check_goto_locked(MOTION_AXIS_Y,py,sy);
 bool ok=ok_x&&ok_y;
 if(ok){
  float dx=fabsf((float)nx),dy=fabsf((float)ny),len=hypotf(dx,dy);
  float ax_acc=(len>0.0f&&nx!=0)?fmaxf(4000.0f*(dx/len),100.0f):4000.0f;
  float ay_acc=(len>0.0f&&ny!=0)?fmaxf(4000.0f*(dy/len),100.0f):4000.0f;
  if(nx!=0)start_move_locked(MOTION_AXIS_X,px,sx,ax_acc);
  if(ny!=0)start_move_locked(MOTION_AXIS_Y,py,sy,ay_acc);
 }
 leave(k);return ok;
}
bool Motion_SetZero(motion_axis_id_t id){
 if((unsigned)id>=2)return false;
 uint32_t k=enter();
 bool ok=HAL_GPIO_ReadPin(ESTOP_GPIO_Port,ESTOP_Pin)!=MOTION_ESTOP_ACTIVE&&ax[id].state==AXIS_IDLE;
 if(ok){ax[id].position=0;ax[id].target=0;ax[id].homed=true;}
 leave(k);return ok;
}
bool Motion_SetZeroAll(void){
 uint32_t k=enter();
 bool ok=HAL_GPIO_ReadPin(ESTOP_GPIO_Port,ESTOP_Pin)!=MOTION_ESTOP_ACTIVE&&ax[0].state==AXIS_IDLE&&ax[1].state==AXIS_IDLE;
 if(ok){for(int i=0;i<2;i++){ax[i].position=0;ax[i].target=0;ax[i].homed=true;}}
 leave(k);return ok;
}
bool Motion_Home(motion_axis_id_t id){
 return Motion_SetZero(id);
}
bool Motion_HomeAll(void){
 return Motion_SetZeroAll();
}
void Motion_Stop(motion_axis_id_t id){if((unsigned)id>=2)return;uint32_t k=enter();if(ax[id].state==AXIS_MOVING)stopping[id]=true;leave(k);}
void Motion_EStop(void){for(int i=0;i<2;i++){ax[i].state=AXIS_ESTOP;ax[i].homed=false;ax[i].speed=0;pulse_left[i]=0; HAL_GPIO_WritePin(step_port[i],step_pin[i],GPIO_PIN_RESET);}}
const motion_axis_t *Motion_GetAxis(motion_axis_id_t id){return (unsigned)id<2?&ax[id]:0;}
static void done(int i,motion_axis_state_t state){ax[i].state=state;ax[i].speed=0;ax[i].target=ax[i].position;stopping[i]=false;}
bool Motion_ClearFault(void){uint32_t k=enter();bool ok=HAL_GPIO_ReadPin(ESTOP_GPIO_Port,ESTOP_Pin)!=MOTION_ESTOP_ACTIVE;if(ok)for(int i=0;i<2;i++)if(ax[i].state==AXIS_FAULT||ax[i].state==AXIS_ESTOP)done(i,AXIS_IDLE);leave(k);return ok;}
bool Motion_Snapshot(motion_axis_id_t id,motion_axis_t *out){if((unsigned)id>=2||!out)return false;uint32_t k=enter();*out=ax[id];leave(k);return true;}
void Motion_TickISR(void){
 if(HAL_GPIO_ReadPin(ESTOP_GPIO_Port,ESTOP_Pin)==MOTION_ESTOP_ACTIVE){Motion_EStop();return;}
 for(int i=0;i<2;i++){
  bool falling=false;if(pulse_left[i]&&!--pulse_left[i]){HAL_GPIO_WritePin(step_port[i],step_pin[i],GPIO_PIN_RESET);falling=true;}
  motion_axis_t *a=&ax[i];if(a->state!=AXIS_MOVING)continue;
  int64_t delta=(int64_t)a->target-a->position;if(!delta){done(i,AXIS_IDLE);continue;}int d=delta>0?1:-1;
  float distance=(float)(delta>0?delta:-delta);float dv=a->accel/MOTION_TICK_HZ;
  if(stopping[i]||a->speed*a->speed>=2*a->accel*distance){a->speed-=dv;if(a->speed<MOTION_MIN_SPEED){if(stopping[i]){done(i,AXIS_IDLE);continue;}a->speed=MOTION_MIN_SPEED;}}
  else{a->speed+=dv;if(a->speed>a->max_speed)a->speed=a->max_speed;}
  uint32_t interval=(uint32_t)(MOTION_TICK_HZ/a->speed);if(interval<high_ticks+1)interval=high_ticks+1;
  if(++phase[i]>=interval&&!pulse_left[i]&&!falling){
   if(!in_range((motion_axis_id_t)i,(int64_t)a->position+d)){done(i,AXIS_IDLE);continue;}
   phase[i]=0;HAL_GPIO_WritePin(step_port[i],step_pin[i],GPIO_PIN_SET);pulse_left[i]=high_ticks;a->position+=d;
  }
 }
}
void Motion_Service(void){}
