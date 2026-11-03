# STM32F407 运动控制接入说明

1. 在 CubeMX 中启用 TIM6 基本定时器，配置更新频率 50 kHz，并开启中断。
2. 启用 USART2（115200-8-N-1）；将 `motion_protocol.c` 接到自己的行缓冲接收逻辑。
3. 按 `Core/Inc/motion_config.h` 修改 GPIO、定时器句柄和串口句柄。
4. 在 `HAL_TIM_PeriodElapsedCallback()` 中调用 `Motion_TickISR()`，主循环调用 `Motion_Service()`。
5. 上电先低速单轴测试，确认 DIR 极性、限位有效电平和急停接线后再提高速度。

命令示例：`MOVE X 1600 800`、`GOTO Y 3200 1200`、`HOME X`、`STOP Y`、`ESTOP`。
# 外设补充

- TIM3 计数频率配置为 1 MHz，周期 20,000，CH1/CH2 输出 50 Hz 舵机 PWM。
- `Servo_SetPulseUs()` 的参数单位为微秒，MG90S/DS3120 初始中位 1500 us。
- `Sensors_Read()` 中的 GPIOC Pin0 是对射光电示例引脚，请按实际接线替换。
- `host_protocol.h` 提供香橙派通信帧的命令号和 CRC16；接收解析建议使用 DMA 环形缓冲。
