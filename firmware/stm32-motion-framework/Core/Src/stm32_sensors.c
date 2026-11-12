#include "stm32_sensors.h"
#include "motion_config.h"
static bool active_low(GPIO_TypeDef *p,uint16_t n){return HAL_GPIO_ReadPin(p,n)==GPIO_PIN_RESET;}
void Sensors_Read(sensor_state_t *s){if(!s)return;s->photoelectric=active_low(GPIOC,GPIO_PIN_0);s->estop=active_low(ESTOP_GPIO_Port,ESTOP_Pin);}
