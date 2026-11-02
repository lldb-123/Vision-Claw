# STM32F407 端职责与接口

## STM32 负责的功能
- A4988 步进驱动：STEP、DIR、ENABLE；默认 1/8 细分，1600 脉冲/转。
- 执行机构：MG90S 和 DS3120 使用定时器 PWM 输出，角度/脉宽通过参数表配置。
- 传感器：对射光电 YIYFA F3、正负限位开关 KW11，使用 GPIO 输入和 EXTI/轮询消抖。
- 上位机通信：与香橙派 5B 通过 UART 连接，STM32 只执行运动和采集，不处理视觉模型。
- 状态回传：位置、运动状态、限位、光电触发、急停和故障码。

## 推荐通信帧
二进制帧：`55 AA | LEN | CMD | SEQ | PAYLOAD | CRC16`

- `CMD=0x01`：步进相对移动，payload=`axis:int8, steps:int32, speed:uint16`
- `CMD=0x02`：步进绝对定位，payload=`axis:int8, pos:int32, speed:uint16`
- `CMD=0x03`：回零，payload=`axis:int8`
- `CMD=0x04`：舵机设置，payload=`servo:uint8, pulse_us:uint16`
- `CMD=0x05`：停止/急停
- `CMD=0x81`：状态回传
- `CMD=0x82`：传感器事件回传

串口建议 115200 8-N-1；接收采用中断或 DMA + 环形缓冲，解析在主循环完成，避免在 UART ISR 里执行运动控制。

## 外设分配建议
- TIM6：50 kHz 步进调度中断。
- TIM3/TIM4：舵机 PWM，50 Hz，1~2 ms 脉宽。
- USART2：香橙派通信。
- GPIO/EXTI：光电、限位、急停。
- SWD：ST-Link 下载和调试。

## 调试顺序
1. 只接 STM32、A4988 和一个步进电机，低速验证 STEP/DIR。
2. 加入限位和急停，验证触发后输出立即停止。
3. 验证舵机 PWM 的 1 ms/1.5 ms/2 ms 三个位置。
4. 接香橙派，先用固定命令测试，再接入视觉流程。
