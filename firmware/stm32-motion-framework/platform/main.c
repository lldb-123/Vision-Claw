#include "motion_control.h"
#include "motion_config.h"
#include "stm32_actuators.h"
#include "z_axis_config.h"
#include "tray_control.h"
#include "tray_config.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <errno.h>
#include <limits.h>
#include <math.h>

TIM_HandleTypeDef htim6,htim3;
UART_HandleTypeDef huart2;

#define UART_RX_BUF_SIZE 512u
static volatile uint8_t uart_rx_buf[UART_RX_BUF_SIZE];
static volatile uint16_t uart_rx_head=0u;
static volatile uint16_t uart_rx_tail=0u;

void SysTick_Handler(void){HAL_IncTick();}
void TIM6_DAC_IRQHandler(void){HAL_TIM_IRQHandler(&htim6);}
void USART2_IRQHandler(void){
 uint32_t sr=USART2->SR;
 if(sr&(USART_SR_RXNE|USART_SR_ORE|USART_SR_FE|USART_SR_NE)){
  uint8_t c=(uint8_t)(USART2->DR&0xFFu);
  if(sr&USART_SR_RXNE){
   uint16_t next=(uint16_t)((uart_rx_head+1u)%UART_RX_BUF_SIZE);
   if(next!=uart_rx_tail){uart_rx_buf[uart_rx_head]=c;uart_rx_head=next;}
  }
 }
}
static int uart_rx_pop(void){
 if(uart_rx_tail==uart_rx_head)return -1;
 uint8_t c=uart_rx_buf[uart_rx_tail];
 uart_rx_tail=(uint16_t)((uart_rx_tail+1u)%UART_RX_BUF_SIZE);
 return (int)c;
}
void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *h){if(h->Instance==TIM6){Motion_TickISR();motion_axis_t a;Motion_Snapshot(MOTION_AXIS_X,&a);if(a.state==AXIS_ESTOP){Tray_EStop();Servo_EStop();HAL_GPIO_WritePin(GPIOA,GPIO_PIN_4|GPIO_PIN_5,GPIO_PIN_SET);}}}
static void fatal(void){__disable_irq();if(htim3.Instance==TIM3){(void)HAL_TIM_PWM_Stop(&htim3,TIM_CHANNEL_1);(void)HAL_TIM_PWM_Stop(&htim3,TIM_CHANNEL_2);(void)HAL_TIM_PWM_Stop(&htim3,TIM_CHANNEL_3);__HAL_TIM_SET_COMPARE(&htim3,TIM_CHANNEL_1,0);__HAL_TIM_SET_COMPARE(&htim3,TIM_CHANNEL_2,0);__HAL_TIM_SET_COMPARE(&htim3,TIM_CHANNEL_3,0);}while(1){}}
static void reply(const char *s){HAL_UART_Transmit(&huart2,(uint8_t*)s,(uint16_t)strlen(s),100);}
static void pins(GPIO_TypeDef *p,uint32_t mask,uint32_t mode,uint32_t pull,uint32_t af){GPIO_InitTypeDef g={0};g.Pin=mask;g.Mode=mode;g.Pull=pull;g.Speed=GPIO_SPEED_FREQ_HIGH;g.Alternate=af;HAL_GPIO_Init(p,&g);}
static void init(void){
 HAL_Init();
 RCC_OscInitTypeDef osc={0};osc.OscillatorType=RCC_OSCILLATORTYPE_HSI;osc.HSIState=RCC_HSI_ON;osc.HSICalibrationValue=RCC_HSICALIBRATION_DEFAULT;
 osc.PLL.PLLState=RCC_PLL_ON;osc.PLL.PLLSource=RCC_PLLSOURCE_HSI;osc.PLL.PLLM=16;osc.PLL.PLLN=336;osc.PLL.PLLP=RCC_PLLP_DIV4;osc.PLL.PLLQ=7;
 __HAL_RCC_PWR_CLK_ENABLE();__HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE2);
 if(HAL_RCC_OscConfig(&osc)!=HAL_OK)fatal();
 RCC_ClkInitTypeDef clk={0};clk.ClockType=RCC_CLOCKTYPE_SYSCLK|RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;clk.SYSCLKSource=RCC_SYSCLKSOURCE_PLLCLK;clk.AHBCLKDivider=RCC_SYSCLK_DIV1;clk.APB1CLKDivider=RCC_HCLK_DIV2;clk.APB2CLKDivider=RCC_HCLK_DIV1;
 if(HAL_RCC_ClockConfig(&clk,FLASH_LATENCY_2)!=HAL_OK)fatal();
 __HAL_RCC_GPIOA_CLK_ENABLE();__HAL_RCC_GPIOB_CLK_ENABLE();__HAL_RCC_GPIOC_CLK_ENABLE();__HAL_RCC_GPIOD_CLK_ENABLE();__HAL_RCC_TIM6_CLK_ENABLE();__HAL_RCC_TIM3_CLK_ENABLE();__HAL_RCC_USART2_CLK_ENABLE();
 pins(GPIOB,GPIO_PIN_0|GPIO_PIN_1|GPIO_PIN_3|GPIO_PIN_4|GPIO_PIN_6,GPIO_MODE_INPUT,GPIO_PULLUP,0);
 HAL_GPIO_WritePin(GPIOA,GPIO_PIN_0|GPIO_PIN_1|GPIO_PIN_2|GPIO_PIN_3,GPIO_PIN_RESET);
 HAL_GPIO_WritePin(GPIOA,GPIO_PIN_4|GPIO_PIN_5,GPIO_PIN_SET);
 pins(GPIOA,GPIO_PIN_0|GPIO_PIN_1|GPIO_PIN_2|GPIO_PIN_3|GPIO_PIN_4|GPIO_PIN_5,GPIO_MODE_OUTPUT_PP,GPIO_NOPULL,0);
 pins(GPIOD,GPIO_PIN_5|GPIO_PIN_6,GPIO_MODE_AF_PP,GPIO_PULLUP,GPIO_AF7_USART2);
 huart2.Instance=USART2;huart2.Init=(UART_InitTypeDef){.BaudRate=115200,.WordLength=UART_WORDLENGTH_8B,.StopBits=UART_STOPBITS_1,.Parity=UART_PARITY_NONE,.Mode=UART_MODE_TX_RX,.HwFlowCtl=UART_HWCONTROL_NONE,.OverSampling=UART_OVERSAMPLING_16};
 if(HAL_UART_Init(&huart2)!=HAL_OK)fatal();
 __HAL_UART_ENABLE_IT(&huart2,UART_IT_RXNE);
 HAL_NVIC_SetPriority(USART2_IRQn,2,0);HAL_NVIC_EnableIRQ(USART2_IRQn);
 htim6.Instance=TIM6;htim6.Init=(TIM_Base_InitTypeDef){.Prescaler=83,.CounterMode=TIM_COUNTERMODE_UP,.Period=19,.ClockDivision=TIM_CLOCKDIVISION_DIV1};
 if(HAL_TIM_Base_Init(&htim6)!=HAL_OK)fatal();
 pins(GPIOA,GPIO_PIN_6,GPIO_MODE_AF_PP,GPIO_NOPULL,GPIO_AF2_TIM3);
 pins(GPIOC,GPIO_PIN_7|GPIO_PIN_8,GPIO_MODE_AF_PP,GPIO_NOPULL,GPIO_AF2_TIM3);
 htim3.Instance=TIM3;htim3.Init=(TIM_Base_InitTypeDef){.Prescaler=83,.CounterMode=TIM_COUNTERMODE_UP,.Period=19999,.ClockDivision=TIM_CLOCKDIVISION_DIV1};
 if(HAL_TIM_PWM_Init(&htim3)!=HAL_OK)fatal();
 TIM_OC_InitTypeDef pwm={0};pwm.OCMode=TIM_OCMODE_PWM1;pwm.Pulse=1500;pwm.OCPolarity=TIM_OCPOLARITY_HIGH;pwm.OCFastMode=TIM_OCFAST_DISABLE;
 if(HAL_TIM_PWM_ConfigChannel(&htim3,&pwm,TIM_CHANNEL_1)!=HAL_OK)fatal();
 if(HAL_TIM_PWM_ConfigChannel(&htim3,&pwm,TIM_CHANNEL_2)!=HAL_OK)fatal();
 if(HAL_TIM_PWM_ConfigChannel(&htim3,&pwm,TIM_CHANNEL_3)!=HAL_OK)fatal();
 if(!Servo_Init())fatal();
 Tray_Init();
 HAL_NVIC_SetPriority(TIM6_DAC_IRQn,1,0);HAL_NVIC_EnableIRQ(TIM6_DAC_IRQn);Motion_Init();Motion_Start();
 if(HAL_GPIO_ReadPin(ESTOP_GPIO_Port,ESTOP_Pin)!=MOTION_ESTOP_ACTIVE){HAL_GPIO_WritePin(GPIOA,GPIO_PIN_4|GPIO_PIN_5,GPIO_PIN_RESET);}
}
static float clamp_axis_speed(float steps_ps){
 if(steps_ps<MOTION_MIN_SPEED)return MOTION_MIN_SPEED;
 if(steps_ps>MOTION_MAX_SPEED)return MOTION_MAX_SPEED;
 return steps_ps;
}
static void command(char *s){
 while(*s==' '||*s=='\t')s++;
 size_t len=strlen(s);
 while(len>0&&(s[len-1]==' '||s[len-1]=='\t'))s[--len]=0;
 if(!len)return;
 char cmd[16],axis,extra;long value;float speed;bool ok=false;
 if(strcmp(s,"STATUS")==0){
  char b[180];
  for(int i=0;i<2;i++){
   motion_axis_t a;Motion_Snapshot((motion_axis_id_t)i,&a);
   unsigned en=(HAL_GPIO_ReadPin(GPIOA,i?GPIO_PIN_5:GPIO_PIN_4)==GPIO_PIN_RESET)?1u:0u;
   snprintf(b,sizeof b,"STATUS %c pos_steps=%ld pos_mm=%.2f target=%ld state=%u enabled=%u homed=%u min=%u max=%u\r\n",i?'Y':'X',(long)a.position,(float)a.position/(i?Y_STEPS_PER_MM:X_STEPS_PER_MM),(long)a.target,(unsigned)a.state,en,a.homed,a.limit_min,a.limit_max);
   reply(b);
  }
  servo_status_t z;Servo_Snapshot(&z);
  snprintf(b,sizeof b,"STATUS Z pulse_us=%u target_us=%u enabled=%u busy=%u estop=%u feedback=NONE\r\n",z.pulse_us,z.target_us,z.enabled,z.busy,z.estop);
  reply(b);return;
 }
 if(strncmp(s,"TRAY ",5)==0){
  char *v[5];unsigned count=0;char *token=strtok(s," ");while(token&&count<5){v[count++]=token;token=strtok(NULL," ");}
  if(count>=2&&strcmp(v[1],"STOP")==0&&count==2){Tray_Stop();ok=true;}
  else if(count>=3&&(strcmp(v[1],"CW")==0||strcmp(v[1],"CCW")==0)){
   char *end;errno=0;long sp=strtol(v[2],&end,10);long ms=TRAY_DEFAULT_DURATION_MS;
   if(errno||*end||sp<1||sp>100||(count==4&&(errno=(int)0,ms=strtol(v[3],&end,10),*end||ms<1||ms>TRAY_MAX_DURATION_MS))||count>4){reply("ERR FORMAT\r\n");return;}
   ok=Tray_Start(strcmp(v[1],"CW")==0?TRAY_DIR_CW:TRAY_DIR_CCW,(uint8_t)sp,(uint32_t)ms);
  } else if(count>=4&&strcmp(v[1],"ANGLE")==0){
   char *end;errno=0;float angle=strtof(v[3],&end);long sp=50;
   if(count==5){sp=strtol(v[4],&end,10);}
   if(errno||*end||!isfinite(angle)||angle<=0.0f||sp<1||sp>100){reply("ERR FORMAT\r\n");return;}
   ok=Tray_StartAngle(strcmp(v[2],"CW")==0?TRAY_DIR_CW:strcmp(v[2],"CCW")==0?TRAY_DIR_CCW:TRAY_DIR_NONE,angle,(uint8_t)sp);
  } else if(count==2&&strcmp(v[1],"STATUS")==0){
   tray_status_t t;Tray_Snapshot(&t);char b[160];
   snprintf(b,sizeof b,"STATUS TRAY state=%u dir=%u speed=%u pulse_us=%u remaining_ms=%lu feedback=%s\r\n",(unsigned)t.state,(unsigned)t.direction,t.speed,t.pulse_us,(unsigned long)t.remaining_ms,t.open_loop?"OPEN_LOOP":"NONE");reply(b);return;
  } else {reply("ERR FORMAT\r\n");return;}
 }
 else if(strcmp(s,"ESTOP")==0){Motion_EStop();Tray_EStop();Servo_EStop();HAL_GPIO_WritePin(GPIOA,GPIO_PIN_4|GPIO_PIN_5,GPIO_PIN_SET);ok=true;}
 else if(strcmp(s,"CLEAR")==0){
  uint32_t k=__get_PRIMASK();__disable_irq();
  ok=Motion_ClearFault();
  if(ok){Tray_ClearFault();Servo_ClearFault();HAL_GPIO_WritePin(GPIOA,GPIO_PIN_4|GPIO_PIN_5,GPIO_PIN_RESET);}
  __set_PRIMASK(k);
 }
 else if(strcmp(s,"ENABLE ALL")==0||strcmp(s,"ENABLE X")==0||strcmp(s,"ENABLE Y")==0||strcmp(s,"ENABLE Z")==0){
  uint32_t k=__get_PRIMASK();__disable_irq();motion_axis_t a;Motion_Snapshot(MOTION_AXIS_X,&a);
  if(HAL_GPIO_ReadPin(ESTOP_GPIO_Port,ESTOP_Pin)!=MOTION_ESTOP_ACTIVE&&a.state!=AXIS_ESTOP){
   if(strcmp(s,"ENABLE ALL")==0){HAL_GPIO_WritePin(GPIOA,GPIO_PIN_4|GPIO_PIN_5,GPIO_PIN_RESET);ok=Servo_Enable();}
   else if(s[7]=='Z')ok=Servo_Enable();
   else{HAL_GPIO_WritePin(GPIOA,s[7]=='X'?GPIO_PIN_4:GPIO_PIN_5,GPIO_PIN_RESET);ok=true;}
  }__set_PRIMASK(k);
  if(!ok){reply("ERR ESTOP_ACTIVE\r\n");return;}
 }
 else if(strcmp(s,"DISABLE ALL")==0||strcmp(s,"DISABLE X")==0||strcmp(s,"DISABLE Y")==0){
  if(strcmp(s,"DISABLE ALL")==0)HAL_GPIO_WritePin(GPIOA,GPIO_PIN_4|GPIO_PIN_5,GPIO_PIN_SET);
  else HAL_GPIO_WritePin(GPIOA,s[8]=='X'?GPIO_PIN_4:GPIO_PIN_5,GPIO_PIN_SET);
  ok=true;
 }
 else if(strcmp(s,"SET_ZERO")==0||strcmp(s,"SET_ZERO ALL")==0){ok=Motion_SetZeroAll();}
 else if(strcmp(s,"SET_ZERO X")==0){ok=Motion_SetZero(MOTION_AXIS_X);}
 else if(strcmp(s,"SET_ZERO Y")==0){ok=Motion_SetZero(MOTION_AXIS_Y);}
 else if(strcmp(s,"HOME ALL")==0){
  if(HAL_GPIO_ReadPin(GPIOA,GPIO_PIN_4)==GPIO_PIN_SET||HAL_GPIO_ReadPin(GPIOA,GPIO_PIN_5)==GPIO_PIN_SET){reply("ERR AXIS_DISABLED\r\n");return;}
  ok=Motion_HomeAll();
 }
 else if(strcmp(s,"STOP ALL")==0){Motion_Stop(MOTION_AXIS_X);Motion_Stop(MOTION_AXIS_Y);Tray_Stop();Servo_Stop();ok=true;}
 else if(strcmp(s,"STOP Z")==0){Servo_Stop();ok=true;}
 else if(strcmp(s,"Z UP")==0||strcmp(s,"Z DOWN")==0){ok=Servo_Move(strcmp(s,"Z UP")==0?Z_UP_US:Z_DOWN_US,700);}
 else if(strncmp(s,"SERVO ",6)==0){
  char *v[5];unsigned count=0;char *token=strtok(s," ");while(token&&count<5){v[count++]=token;token=strtok(NULL," ");}
  if(count!=4||strlen(v[1])!=1){reply("ERR FORMAT\r\n");return;}
  servo_id_t sid;
  if(v[1][0]=='Z')sid=SERVO_MG90S;
  else if(v[1][0]=='1')sid=SERVO_DS3120_1;
  else if(v[1][0]=='2')sid=SERVO_DS3120_2;
  else{reply("ERR FORMAT\r\n");return;}
  char *end;errno=0;long us=strtol(v[2],&end,10);if(errno||*end||us<0||us>65535){reply("ERR FORMAT\r\n");return;}
  errno=0;long ms=strtol(v[3],&end,10);if(errno||*end||ms<0||ms>30000){reply("ERR FORMAT\r\n");return;}
  ok=Servo_MoveTo(sid,(uint16_t)us,(uint32_t)ms);
 }
 else if(strncmp(s,"MOVE_XYZ ",9)==0||strncmp(s,"GOTO_XYZ ",9)==0){
  bool relative=(strncmp(s,"MOVE_XYZ ",9)==0);
  char *v[7];unsigned count=0;char *token=strtok(s," ");while(token&&count<7){v[count++]=token;token=strtok(NULL," ");}
  if(count!=5&&count!=6){reply("ERR FORMAT\r\n");return;}
  char *end;errno=0;float xmm=strtof(v[1],&end);if(errno||*end||!isfinite(xmm)){reply("ERR FORMAT\r\n");return;}
  errno=0;float ymm=strtof(v[2],&end);if(errno||*end||!isfinite(ymm)){reply("ERR FORMAT\r\n");return;}
  errno=0;long zus=strtol(v[3],&end,10);if(errno||*end||zus<0||zus>65535){reply("ERR FORMAT\r\n");return;}
  errno=0;float mmps=strtof(v[4],&end);if(errno||*end||!isfinite(mmps)||mmps<=0.0f){reply("ERR SPEED\r\n");return;}
  if(mmps*X_STEPS_PER_MM<MOTION_MIN_SPEED||mmps*X_STEPS_PER_MM>MOTION_MAX_SPEED||mmps*Y_STEPS_PER_MM<MOTION_MIN_SPEED||mmps*Y_STEPS_PER_MM>MOTION_MAX_SPEED){reply("ERR SPEED\r\n");return;}
  long zms=700;
  if(count==6){errno=0;zms=strtol(v[5],&end,10);if(errno||*end||zms<20||zms>30000){reply("ERR FORMAT\r\n");return;}}
  if(relative?(fabsf(xmm)>X_MAX_MM||fabsf(ymm)>Y_MAX_MM):(xmm<0.0f||xmm>X_MAX_MM||ymm<0.0f||ymm>Y_MAX_MM)){reply("ERR RANGE\r\n");return;}
  if(!Servo_CanMove(SERVO_MG90S,(uint16_t)zus,(uint32_t)zms)){reply("ERR Z_REJECTED\r\n");return;}
  motion_axis_t ax_snap,ay_snap;
  Motion_Snapshot(MOTION_AXIS_X,&ax_snap);Motion_Snapshot(MOTION_AXIS_Y,&ay_snap);
  int32_t tx=lroundf(xmm*X_STEPS_PER_MM),ty=lroundf(ymm*Y_STEPS_PER_MM);
  int32_t dx_steps=relative?tx:(tx-ax_snap.position);
  int32_t dy_steps=relative?ty:(ty-ax_snap.position);
  if(dx_steps!=0&&HAL_GPIO_ReadPin(GPIOA,GPIO_PIN_4)==GPIO_PIN_SET){reply("ERR X_DISABLED\r\n");return;}
  if(dy_steps!=0&&HAL_GPIO_ReadPin(GPIOA,GPIO_PIN_5)==GPIO_PIN_SET){reply("ERR Y_DISABLED\r\n");return;}
  float dx_mm=fabsf((float)dx_steps)/X_STEPS_PER_MM;
  float dy_mm=fabsf((float)dy_steps)/Y_STEPS_PER_MM;
  float dist_mm=hypotf(dx_mm,dy_mm);
  float sx=clamp_axis_speed((dist_mm>0.0f?(mmps*(dx_mm/dist_mm)):mmps)*X_STEPS_PER_MM);
  float sy=clamp_axis_speed((dist_mm>0.0f?(mmps*(dy_mm/dist_mm)):mmps)*Y_STEPS_PER_MM);
  const char *err_x=Motion_CheckMoveError(MOTION_AXIS_X,tx,sx,relative);
  if(err_x){reply(err_x);return;}
  const char *err_y=Motion_CheckMoveError(MOTION_AXIS_Y,ty,sy,relative);
  if(err_y){reply(err_y);return;}
  ok=relative?Motion_MoveRelativeXY(tx,sx,ty,sy):Motion_GotoXY(tx,sx,ty,sy);
  if(ok)ok=Servo_Move((uint16_t)zus,(uint32_t)zms);
 }
 else if(strncmp(s,"MOVE_MM ",8)==0||strncmp(s,"GOTO_MM ",8)==0){
  char *v[5];unsigned count=0;char *token=strtok(s," ");while(token&&count<5){v[count++]=token;token=strtok(NULL," ");}
  if(count!=4||strlen(v[1])!=1||(v[1][0]!='X'&&v[1][0]!='Y')){reply("ERR FORMAT\r\n");return;}
  char *end;errno=0;float mm=strtof(v[2],&end);bool relative=strcmp(v[0],"MOVE_MM")==0;float maxmm=v[1][0]=='X'?X_MAX_MM:Y_MAX_MM;if(errno||*end||!isfinite(mm)||(relative?fabsf(mm)>maxmm:(mm<0||mm>maxmm))){reply("ERR RANGE\r\n");return;}
  errno=0;float mmps=strtof(v[3],&end);if(errno||*end||!isfinite(mmps)||mmps<=0){reply("ERR SPEED\r\n");return;}
  motion_axis_id_t i=v[1][0]=='X'?MOTION_AXIS_X:MOTION_AXIS_Y;float k=i==MOTION_AXIS_X?X_STEPS_PER_MM:Y_STEPS_PER_MM;
  if(HAL_GPIO_ReadPin(GPIOA,i==MOTION_AXIS_X?GPIO_PIN_4:GPIO_PIN_5)==GPIO_PIN_SET){reply("ERR AXIS_DISABLED\r\n");return;}
  int32_t steps=(int32_t)lroundf(mm*k);float stepsps=mmps*k;
  const char *err=Motion_CheckMoveError(i,steps,stepsps,relative);
  if(err){reply(err);return;}
  if(relative)ok=Motion_MoveRelative(i,steps,stepsps);else ok=Motion_Goto(i,steps,stepsps);
 }else if(strncmp(s,"MOVE ",5)==0||strncmp(s,"GOTO ",5)==0){
  char *v[5];unsigned count=0;char *token=strtok(s," ");
  while(token&&count<5){v[count++]=token;token=strtok(NULL," ");}
  if(count!=4||strlen(v[1])!=1||(v[1][0]!='X'&&v[1][0]!='Y')){reply("ERR FORMAT\r\n");return;}
  char *end;errno=0;value=strtol(v[2],&end,10);if(errno||*end||value<INT32_MIN||value>INT32_MAX){reply("ERR RANGE\r\n");return;}
  errno=0;speed=strtof(v[3],&end);if(errno||*end){reply("ERR SPEED\r\n");return;}
  motion_axis_id_t i=v[1][0]=='X'?MOTION_AXIS_X:MOTION_AXIS_Y;
  if(HAL_GPIO_ReadPin(GPIOA,i==MOTION_AXIS_X?GPIO_PIN_4:GPIO_PIN_5)==GPIO_PIN_SET){reply("ERR AXIS_DISABLED\r\n");return;}
  bool relative=(strcmp(v[0],"MOVE")==0);
  const char *err=Motion_CheckMoveError(i,(int32_t)value,speed,relative);
  if(err){reply(err);return;}
  if(relative)ok=Motion_MoveRelative(i,(int32_t)value,speed);else ok=Motion_Goto(i,(int32_t)value,speed);
 }else if(sscanf(s,"%15s %c %c",cmd,&axis,&extra)==2&&(axis=='X'||axis=='Y')){
  motion_axis_id_t i=axis=='X'?MOTION_AXIS_X:MOTION_AXIS_Y;
  if(strcmp(cmd,"HOME")==0){if(HAL_GPIO_ReadPin(GPIOA,i==MOTION_AXIS_X?GPIO_PIN_4:GPIO_PIN_5)==GPIO_PIN_RESET)ok=Motion_Home(i);else{reply("ERR AXIS_DISABLED\r\n");return;}}
  else if(strcmp(cmd,"STOP")==0){Motion_Stop(i);ok=true;}
 }
 reply(ok?"ACK\r\n":"ERR REJECTED\r\n");
}
int main(void){
 init();
 reply("READY XYZ F407 HSI_PLL84 UART2_PD5_PD6\r\n");
 char line[128];unsigned n=0;bool overflow=false;
 while(1){
  Motion_Service();
  Servo_Service();
  Tray_Service();
  int ch;
  while((ch=uart_rx_pop())>=0){
   char c=(char)ch;
   if(c=='\r'||c=='\n'){
    if(overflow)reply("ERR LINE_TOO_LONG\r\n");
    else if(n){line[n]=0;command(line);}
    n=0;overflow=false;
   }else if(n<sizeof line-1&&!overflow){
    line[n++]=c;
   }else{
    overflow=true;
   }
  }
 }
}
