.syntax unified
.thumb

/* STM32F407VE, no HAL and no external crystal required.
 * PA0 -> A4988 STEP; PA1 -> DIR; PA4 -> active-low ENABLE.
 * On reset: disable, wait 1s, ramp from 50 Hz to 200 Hz, keep running.
 * Each pulse HIGH 1ms; LOW ramps from 19ms down to 4ms.
 * Stop by disconnecting motor power. Current limiting is external.
 * References: ST RM0090 and the STM32F405/407 datasheet.
 */
reset_handler:
    cpsid i

    /* Enable HSI and select it as SYSCLK, AHB/APB prescalers = 1. */
    movw r0, #0x3800
    movt r0, #0x4002
    ldr r1, [r0]
    orr r1, r1, #1
    str r1, [r0]
wait_hsi:
    ldr r1, [r0]
    tst r1, #2
    beq wait_hsi
    movs r1, #0
    str r1, [r0, #8]
wait_clock:
    ldr r1, [r0, #8]
    tst r1, #12
    bne wait_clock

    /* Enable GPIOA clock. */
    ldr r1, [r0, #0x30]
    orr r1, r1, #1
    str r1, [r0, #0x30]
    ldr r1, [r0, #0x30]
    dsb

    /* Preload output values: STEP=0, DIR=0, ENABLE=1. */
    movw r5, #0x0000
    movt r5, #0x4002
    movw r1, #0x0010
    movt r1, #0x0003
    str r1, [r5, #0x18]

    /* Only PA0, PA1, PA4 change; preserve PA13/PA14 SWD. */
    ldr r1, [r5, #4]
    bic r1, r1, #0x13
    str r1, [r5, #4]
    movw r2, #0x030f
    ldr r1, [r5, #0x0c]
    bic r1, r1, r2
    str r1, [r5, #0x0c]
    ldr r1, [r5]
    bic r1, r1, r2
    movw r2, #0x0105
    orr r1, r1, r2
    str r1, [r5]

    /* SysTick at 1ms from the 16MHz HSI. Interrupt disabled. */
    movw r2, #0xe010
    movt r2, #0xe000
    movs r1, #0
    str r1, [r2]
    movw r1, #15999
    str r1, [r2, #4]
    movs r1, #0
    str r1, [r2, #8]
    movs r1, #5
    str r1, [r2]

    movw r0, #1000
    bl delay_ms

    /* Enable the A4988 and gently ramp up before continuous rotation. */
    movs r1, #16
    lsls r1, r1, #16
    str r1, [r5, #0x18]
    movs r0, #5
    bl delay_ms
    movs r7, #19
ramp_level:
    movs r6, #10
pulse_loop:
    movs r1, #1
    str r1, [r5, #0x18]
    movs r0, #1
    bl delay_ms
    movs r1, #1
    lsls r1, r1, #16
    str r1, [r5, #0x18]
    mov r0, r7
    bl delay_ms
    subs r6, r6, #1
    bne pulse_loop
    subs r7, r7, #1
    cmp r7, #4
    bhi ramp_level

    /* 200 STEP pulses/second, continuous, one direction. */
continuous_loop:
    movs r1, #1
    str r1, [r5, #0x18]
    movs r0, #1
    bl delay_ms
    movs r1, #1
    lsls r1, r1, #16
    str r1, [r5, #0x18]
    movs r0, #4
    bl delay_ms
    b continuous_loop

delay_ms:
    push {r4, lr}
    mov r4, r0
    movw r2, #0xe010
    movt r2, #0xe000
delay_next:
    movs r1, #0
    str r1, [r2, #8]
delay_wait:
    ldr r1, [r2]
    tst r1, #0x10000
    beq delay_wait
    subs r4, r4, #1
    bne delay_next
    pop {r4, pc}

fault_handler:
    /* Attempt to disable outputs, then halt. */
    movw r0, #0x0018
    movt r0, #0x4002
    movs r1, #16
    str r1, [r0]
fault_loop:
    b fault_loop
