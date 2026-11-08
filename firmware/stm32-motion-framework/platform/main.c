#include "motion_control.h"
#include "motion_config.h"
#include "stm32_actuators.h"
#include "z_axis_config.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <errno.h>
#include <limits.h>
#include <math.h>
TIM_HandleTypeDef htim6,htim3;
UART_HandleTypeDef huart2;
void SysTick_Handler(void){HAL_IncTick();}
void TIM6_DAC_IRQHandler(void){HAL_TIM_IRQHandler(&htim6);}
void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *h){if(h->Instance==TIM6){Motion_TickISR();motion_axis_t a;Motion_Snapshot(MOTION_AXIS_X,&a);if(a.state==AXIS_ESTOP)Servo_EStop();}}
static void fatal(void){__disable_irq();while(1){}}
static void reply(const char *s){HAL_UART_Transmit(&huart2,(uint8_t*)s,strlen(s),50);}
static void pins(GPIO_TypeDef *p,uint32_t mask,uint32_t mode,uint32_t pull,uint32_t af){GPIO_InitTypeDef g={0};g.Pin=mask;g.Mode=mode;g.Pull=pull;g.Speed=GPIO_SPEED_FREQ_HIGH;g.Alternate=af;HAL_GPIO_Init(p,&g);}
static void init(void){
 HAL_Init();
 RCC_OscInitTypeDef osc={0};osc.OscillatorType=RCC_OSCILLATORTYPE_HSI;osc.HSIState=RCC_HSI_ON;osc.HSICalibrationValue=RCC_HSICALIBRATION_DEFAULT;
 osc.PLL.PLLState=RCC_PLL_ON;osc.PLL.PLLSource=RCC_PLLSOURCE_HSI;osc.PLL.PLLM=16;osc.PLL.PLLN=336;osc.PLL.PLLP=RCC_PLLP_DIV4;osc.PLL.PLLQ=7;
 __HAL_RCC_PWR_CLK_ENABLE();__HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE2);
 if(HAL_RCC_OscConfig(&osc)!=HAL_OK)fatal();
 RCC_ClkInitTypeDef clk={0};clk.ClockType=RCC_CLOCKTYPE_SYSCLK|RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;clk.SYSCLKSource=RCC_SYSCLKSOURCE_PLLCLK;clk.AHBCLKDivider=RCC_SYSCLK_DIV1;clk.APB1CLKDivider=RCC_HCLK_DIV2;clk.APB2CLKDivider=RCC_HCLK_DIV1;
 if(HAL_RCC_ClockConfig(&clk,FLASH_LATENCY_2)!=HAL_OK)fatal();
 __HAL_RCC_GPIOA_CLK_ENABLE();__HAL_RCC_GPIOB_CLK_ENABLE();__HAL_RCC_GPIOD_CLK_ENABLE();__HAL_RCC_TIM6_CLK_ENABLE();__HAL_RCC_TIM3_CLK_ENABLE();__HAL_RCC_USART2_CLK_ENABLE();
 HAL_GPIO_WritePin(GPIOA,GPIO_PIN_0|GPIO_PIN_1|GPIO_PIN_2|GPIO_PIN_3,GPIO_PIN_RESET);
 HAL_GPIO_WritePin(GPIOA,GPIO_PIN_4|GPIO_PIN_5,GPIO_PIN_SET);
 pins(GPIOA,GPIO_PIN_0|GPIO_PIN_1|GPIO_PIN_2|GPIO_PIN_3|GPIO_PIN_4|GPIO_PIN_5,GPIO_MODE_OUTPUT_PP,GPIO_NOPULL,0);
 pins(GPIOB,GPIO_PIN_0|GPIO_PIN_1|GPIO_PIN_2|GPIO_PIN_3|GPIO_PIN_4,GPIO_MODE_INPUT,GPIO_PULLUP,0);
 pins(GPIOD,GPIO_PIN_5|GPIO_PIN_6,GPIO_MODE_AF_PP,GPIO_PULLUP,GPIO_AF7_USART2);
 huart2.Instance=USART2;huart2.Init=(UART_InitTypeDef){.BaudRate=115200,.WordLength=UART_WORDLENGTH_8B,.StopBits=UART_STOPBITS_1,.Parity=UART_PARITY_NONE,.Mode=UART_MODE_TX_RX,.HwFlowCtl=UART_HWCONTROL_NONE,.OverSampling=UART_OVERSAMPLING_16};
 if(HAL_UART_Init(&huart2)!=HAL_OK)fatal();
 htim6.Instance=TIM6;htim6.Init=(TIM_Base_InitTypeDef){.Prescaler=83,.CounterMode=TIM_COUNTERMODE_UP,.Period=19,.ClockDivision=TIM_CLOCKDIVISION_DIV1};
 if(HAL_TIM_Base_Init(&htim6)!=HAL_OK)fatal();
 pins(GPIOA,GPIO_PIN_6,GPIO_MODE_AF_PP,GPIO_NOPULL,GPIO_AF2_TIM3);
 htim3.Instance=TIM3;htim3.Init=(TIM_Base_InitTypeDef){.Prescaler=83,.CounterMode=TIM_COUNTERMODE_UP,.Period=19999,.ClockDivision=TIM_CLOCKDIVISION_DIV1};
 if(HAL_TIM_PWM_Init(&htim3)!=HAL_OK)fatal();
 TIM_OC_InitTypeDef pwm={0};pwm.OCMode=TIM_OCMODE_PWM1;pwm.Pulse=1500;pwm.OCPolarity=TIM_OCPOLARITY_HIGH;pwm.OCFastMode=TIM_OCFAST_DISABLE;
 if(HAL_TIM_PWM_ConfigChannel(&htim3,&pwm,TIM_CHANNEL_1)!=HAL_OK)fatal();
 Servo_Init();
 HAL_NVIC_SetPriority(TIM6_DAC_IRQn,1,0);HAL_NVIC_EnableIRQ(TIM6_DAC_IRQn);Motion_Init();Motion_Start();
}
static void command(char *s){
 char cmd[16],axis,extra;long value;float speed;bool ok=false;
 if(strcmp(s,"STATUS")==0){char b[160];for(int i=0;i<2;i++){motion_axis_t a;Motion_Snapshot((motion_axis_id_t)i,&a);snprintf(b,sizeof b,"STATUS %c pos_steps=%ld pos_mm=%.2f target=%ld state=%u homed=%u min=%u max=%u\r\n",i?'Y':'X',(long)a.position,(float)a.position/(i?Y_STEPS_PER_MM:X_STEPS_PER_MM),(long)a.target,(unsigned)a.state,a.homed,a.limit_min,a.limit_max);reply(b);}servo_status_t z;Servo_Snapshot(&z);snprintf(b,sizeof b,"STATUS Z pulse_us=%u target_us=%u enabled=%u busy=%u estop=%u feedback=NONE\r\n",z.pulse_us,z.target_us,z.enabled,z.busy,z.estop);reply(b);return;}
 if(strcmp(s,"ESTOP")==0){Motion_EStop();Servo_EStop();HAL_GPIO_WritePin(GPIOA,GPIO_PIN_4|GPIO_PIN_5,GPIO_PIN_SET);ok=true;}
 else if(strcmp(s,"CLEAR")==0){uint32_t k=__get_PRIMASK();__disable_irq();ok=Motion_ClearFault();if(ok)Servo_ClearFault();__set_PRIMASK(k);}
 else if(strcmp(s,"ENABLE X")==0||strcmp(s,"ENABLE Y")==0||strcmp(s,"ENABLE Z")==0){
  uint32_t k=__get_PRIMASK();__disable_irq();motion_axis_t a;Motion_Snapshot(MOTION_AXIS_X,&a);
  if(HAL_GPIO_ReadPin(ESTOP_GPIO_Port,ESTOP_Pin)!=MOTION_ESTOP_ACTIVE&&a.state!=AXIS_ESTOP){if(s[7]=='Z')ok=Servo_Enable();else{HAL_GPIO_WritePin(GPIOA,s[7]=='X'?GPIO_PIN_4:GPIO_PIN_5,GPIO_PIN_RESET);ok=true;}}__set_PRIMASK(k);
 }
 else if(strcmp(s,"STOP Z")==0){Servo_Stop();ok=true;}
 else if(strcmp(s,"Z UP")==0||strcmp(s,"Z DOWN")==0){ok=Servo_Move(strcmp(s,"Z UP")==0?Z_UP_US:Z_DOWN_US,700);}
 else if(strncmp(s,"SERVO Z ",8)==0){
  char *end;errno=0;long us=strtol(s+8,&end,10);if(errno||end==s+8||*end!=' '||us<0||us>65535){reply("ERR FORMAT\r\n");return;}
  char *begin=end;errno=0;long ms=strtol(begin,&end,10);if(errno||end==begin||*end||ms<0||ms>30000){reply("ERR FORMAT\r\n");return;}ok=Servo_Move((uint16_t)us,(uint32_t)ms);
 }
 else if(strncmp(s,"MOVE_MM ",8)==0||strncmp(s,"GOTO_MM ",8)==0){
  char *v[5];unsigned count=0;char *token=strtok(s," ");while(token&&count<5){v[count++]=token;token=strtok(NULL," ");}
  if(count!=4||strlen(v[1])!=1||(v[1][0]!='X'&&v[1][0]!='Y')){reply("ERR FORMAT\r\n");return;}
  char *end;errno=0;float mm=strtof(v[2],&end);if(errno||*end||!isfinite(mm)||mm<0||mm>10000){reply("ERR RANGE\r\n");return;}
  errno=0;float mmps=strtof(v[3],&end);if(errno||*end||!isfinite(mmps)||mmps<=0){reply("ERR SPEED\r\n");return;}
  motion_axis_id_t i=v[1][0]=='X'?MOTION_AXIS_X:MOTION_AXIS_Y;float k=i==MOTION_AXIS_X?X_STEPS_PER_MM:Y_STEPS_PER_MM;
  if(HAL_GPIO_ReadPin(GPIOA,i==MOTION_AXIS_X?GPIO_PIN_4:GPIO_PIN_5)==GPIO_PIN_SET){reply("ERR AXIS_DISABLED\r\n");return;}
  int32_t steps=(int32_t)lroundf(mm*k);float stepsps=mmps*k;if(strcmp(v[0],"MOVE_MM")==0)ok=Motion_MoveRelative(i,steps,stepsps);else ok=Motion_Goto(i,steps,stepsps);
 }else if(strncmp(s,"MOVE ",5)==0||strncmp(s,"GOTO ",5)==0){
  char *v[5];unsigned count=0;char *token=strtok(s," ");
  while(token&&count<5){v[count++]=token;token=strtok(NULL," ");}
  if(count!=4||strlen(v[1])!=1||(v[1][0]!='X'&&v[1][0]!='Y')){reply("ERR FORMAT\r\n");return;}
  char *end;errno=0;value=strtol(v[2],&end,10);if(errno||*end||value<INT32_MIN||value>INT32_MAX){reply("ERR RANGE\r\n");return;}
  errno=0;speed=strtof(v[3],&end);if(errno||*end){reply("ERR SPEED\r\n");return;}
  motion_axis_id_t i=v[1][0]=='X'?MOTION_AXIS_X:MOTION_AXIS_Y;
  if(HAL_GPIO_ReadPin(GPIOA,i==MOTION_AXIS_X?GPIO_PIN_4:GPIO_PIN_5)==GPIO_PIN_SET){reply("ERR AXIS_DISABLED\r\n");return;}
  if(strcmp(v[0],"MOVE")==0)ok=Motion_MoveRelative(i,(int32_t)value,speed);else ok=Motion_Goto(i,(int32_t)value,speed);
 }else if(sscanf(s,"%15s %c %c",cmd,&axis,&extra)==2&&(axis=='X'||axis=='Y')){
  motion_axis_id_t i=axis=='X'?MOTION_AXIS_X:MOTION_AXIS_Y;
  if(strcmp(cmd,"HOME")==0){if(HAL_GPIO_ReadPin(GPIOA,i==MOTION_AXIS_X?GPIO_PIN_4:GPIO_PIN_5)==GPIO_PIN_RESET)ok=Motion_Home(i);}else if(strcmp(cmd,"STOP")==0){Motion_Stop(i);ok=true;}
 }
 reply(ok?"ACK\r\n":"ERR REJECTED\r\n");
}
int main(void){init();reply("READY XYZ F407 HSI_PLL84 UART2_PD5_PD6\r\n");char line[96];unsigned n=0;bool overflow=false;uint8_t c;
 while(1){Motion_Service();Servo_Service();if(HAL_UART_Receive(&huart2,&c,1,1)==HAL_OK){if(c=='\r'||c=='\n'){if(overflow)reply("ERR LINE_TOO_LONG\r\n");else if(n){line[n]=0;command(line);}n=0;overflow=false;}else if(n<sizeof line-1&&!overflow)line[n++]=(char)c;else overflow=true;}}
}


