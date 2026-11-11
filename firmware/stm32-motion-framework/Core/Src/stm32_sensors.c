#include "stm32_sensors.h"
#include "motion_config.h"
static bool active(GPIO_TypeDef *p,uint16_t n){return HAL_GPIO_ReadPin(p,n)==MOTION_LIMIT_ACTIVE;}
void Sensors_Read(sensor_state_t *s){if(!s)return;s->photoelectric=active(GPIOC,GPIO_PIN_0);s->x_min=active(X_MIN_GPIO_Port,X_MIN_Pin);s->x_max=active(X_MAX_GPIO_Port,X_MAX_Pin);s->y_min=active(Y_MIN_GPIO_Port,Y_MIN_Pin);s->y_max=active(Y_MAX_GPIO_Port,Y_MAX_Pin);s->estop=active(ESTOP_GPIO_Port,ESTOP_Pin);}
