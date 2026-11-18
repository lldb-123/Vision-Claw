#include <stdint.h>
extern uint32_t _estack,_sidata,_sdata,_edata,_sbss,_ebss;
extern int main(void);
extern void SystemInit(void),SysTick_Handler(void),TIM6_DAC_IRQHandler(void),USART2_IRQHandler(void);
static void Default_Handler(void){while(1){}}
void Reset_Handler(void){uint32_t *s=&_sidata;for(uint32_t *d=&_sdata;d<&_edata;)*d++=*s++;for(uint32_t *d=&_sbss;d<&_ebss;)*d++=0;SystemInit();main();while(1){}}
__attribute__((section(".isr_vector"),used)) void (*const vectors[98])(void)={
 [0]=(void(*)(void))(&_estack),[1]=Reset_Handler,[2]=Default_Handler,[3]=Default_Handler,[4]=Default_Handler,[5]=Default_Handler,[6]=Default_Handler,[11]=Default_Handler,[12]=Default_Handler,[14]=Default_Handler,[15]=SysTick_Handler,[16+38]=USART2_IRQHandler,[16+54]=TIM6_DAC_IRQHandler
};
