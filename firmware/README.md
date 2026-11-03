# STM32 电控代码

[stm32-motion-framework/](stm32-motion-framework/) 是电控同学提供的初版，按原内容导入。

## 阅读顺序

1. [原始运动控制设计](stm32-motion-framework/docs/superpowers/specs/2026-11-02-stm32f407-motion-control-design.md)。
2. [原始接入说明](stm32-motion-framework/README_MOTION.md)。
3. [GPIO 与句柄配置](stm32-motion-framework/Core/Inc/motion_config.h)。
4. [运动接口](stm32-motion-framework/Core/Inc/motion_control.h)、[实现](stm32-motion-framework/Core/Src/motion_control.c)、[命令解析](stm32-motion-framework/Core/Src/motion_protocol.c)。
5. [回调集成提示](stm32-motion-framework/Core/Inc/motion_integration.txt)。

## 当前范围

这是一份 STM32F407 HAL 双轴步进控制框架，需要自行接入 CubeMX/CubeIDE 工程。目录中没有完整的启动文件、HAL 库、`main.c` 或工程构建配置，不能直接当成整机固件下载。

原设计出现 A3967、1/8 细分和示例 GPIO，当前单电机实物实验使用 A4988、整步。这些值需要队友结合实物统一；导入时没有改动原设计或替队友修正控制逻辑。

文档中的梯形速度、脉宽、UART 状态与错误反馈等设计目标，不代表当前实现均已完成。此前审阅记录见 [本次对话第 5 节](../ai-dialogue/2026-11-03-001-project-and-motor.md#5-队友提供的-stm32-框架)。

## 与另外两个工程的关系

- [上位机演示协议](../software/upper-computer/docs/通信协议.md) 采用完整分拣任务和结果反馈；本框架的 `MOVE/GOTO/HOME/STOP/ESTOP` 是另一套底层文本命令，当前不能直接互通。
- [单电机实验](../experiments/single-motor/README.md) 是独立裸机固件，已经烧录过，但没有串口和整机流程。
- 正式开发应先商议接口，再集成四个电机、限位、回零、落料反馈和组合动作。职责和已确认信息见 [当前状态](../ai-dialogue/README.md)。
