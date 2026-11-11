# STM32F4 依赖检查与 Keil 工程路径修复

## 接续摘要

目标芯片为 STM32F407VET6。已从 `D:\STM32_Download` 的三份官方组件仓库中选取兼容的 HAL、CMSIS Device 和 CMSIS Core，复制到 `firmware/stm32-motion-framework/Drivers/`，并把 `VisionClaw_Motion.uvprojx` 的旧电脑绝对路径改为工程相对路径。后续同一对话中已扩展三路独立舵机 PWM，修改了执行器代码但未改动 TIM6 步进和 X/Y 引脚。未烧录。

## 依赖版本

- HAL：`STM32F4xx_HAL_Driver v1.8.6`，Release Notes 日期 2026-10-29。
- CMSIS Device F4：`V2.6.11`，日期 2025-04-25。
- CMSIS Core 仓库：`v6.3.0`，2026-01-12；包内 PDSC 标注 CMSIS-Core 6.2.0，`cmsis_version.h` 标注 Core(M) 6.1.0。
- 工程已有 `platform/device/stm32f407xx.h` 与输入 Device 包的 `Include/stm32f407xx.h` SHA-256 完全一致。

## 已复制内容

- `Drivers/STM32F4xx_HAL_Driver/Inc`
- `Drivers/STM32F4xx_HAL_Driver/Src`
- `Drivers/CMSIS/Include`
- `Drivers/CMSIS/Device/ST/STM32F4xx/Include`
- `Core/Src/system_stm32f4xx.c`

`system_stm32f4xx.h` 随 CMSIS Device `Include` 目录复制，位于 `Drivers/CMSIS/Device/ST/STM32F4xx/Include/system_stm32f4xx.h`。

## 工程配置修改

- 修改 `MDK-ARM/VisionClaw_Motion.uvprojx` 的头文件搜索路径，全部改为 `../Drivers/...` 相对路径。
- 修改 `system_stm32f4xx.c`、HAL `Src` 文件条目的旧绝对路径。
- 向 HAL 组补充 `stm32f4xx_hal_exti.c` 和 `stm32f4xx_hal_dma_ex.c`。
- 原工程备份为 `MDK-ARM/VisionClaw_Motion.uvprojx.bak`。
- 同步清除 `MDK-ARM/VisionClaw_Motion.uvoptx` 中同批旧绝对路径；原文件备份为 `MDK-ARM/VisionClaw_Motion.uvoptx.bak`。

## 验证证据

- `.uvprojx` XML 可正常解析。
- 工程登记 20 个源文件，逐个解析后全部存在。
- 6 个头文件搜索目录全部存在。
- `.uvprojx` 和 `.uvoptx` 中已无 `D:/EmbeddedDev` 或 `D:\EmbeddedDev`。
- 已启用模块 RCC、GPIO、EXTI、DMA、CORTEX、FLASH、PWR、TIM、UART 的必需 HAL 头文件和源文件均存在。
- CMSIS Core 包含 `core_cm4.h`、`cmsis_compiler.h`、`cmsis_armclang.h`、`cmsis_version.h` 等 AC6 所需文件。
- Device 包含 F407 设备头文件、系统头文件和 `system_stm32f4xx.c` 模板。

## 尚未完成

- 尝试调用 `D:\Keil5\UV4\UV4.exe -b` 时被当前执行环境策略拒绝，未生成编译日志，因此不能记录为“Keil 编译通过”。
- 下一步应直接打开 `firmware/stm32-motion-framework/MDK-ARM/VisionClaw_Motion.uvprojx`，执行 F7 查看实际编译结果；不要烧录。

## 三路舵机 PWM 扩展

- MG90S：PA6 / TIM3_CH1。
- DS3120MG #1：PC7 / TIM3_CH2。
- DS3120MG #2：PC8 / TIM3_CH3。
- TIM3 保持 PSC=83、ARR=19999，即 50Hz；三路初始脉宽均为 1500us。
- 新增按 ID 独立控制：`Servo_SetPulseUs`、`Servo_MoveTo`、`Servo_StopById`、`Servo_SnapshotById`；原 MG90S/Z 接口保留。
- 当前三路允许脉宽均为 1000~2000us，DS3120MG 后续需按实物校准。
- 未修改 TIM6 步进中断、X/Y STEP/DIR/EN 和 PB0~PB4 限位/急停引脚。
- 初始化失败安全处理：`Servo_Init()` 记录每路 started 状态；任意一路启动失败时停止此前成功通道、三路 CCR 清零、全部状态复位并返回 false。`fatal()` 在 TIM3 已初始化时停止 CH1~CH3 并清零 CCR，不关闭舵机外部电源。
- 未修改正常路径的 `Servo_EStop()` 行为、GPIO、TIM3 频率和控制接口。
- 2026-11-10 将 Y_MIN 从开发板未引出的 PB2 改为外部排针 PB6（PCB 焊盘 25，左侧内侧，从 USB 端起第 20 孔）；Y_MAX 保持 PB3。`main.c` 的 GPIOB 上拉输入掩码同步移除 PB2、加入 PB6。

修改文件：

- `firmware/stm32-motion-framework/platform/main.c`
- `firmware/stm32-motion-framework/Core/Src/stm32_actuators.c`
- `firmware/stm32-motion-framework/Core/Inc/stm32_actuators.h`
- `firmware/stm32-motion-framework/README.md`
- `firmware/stm32-motion-framework/docs/XYZ运动控制使用说明.md`

验证：使用 Keil 自带 ArmClang 6.22 从头编译工程登记的 19 个 C 源文件，编译失败数为 0；连同启动目标文件共 20 个对象执行 ArmLink，退出码 0；FromELF 成功生成 AXF/HEX。另用临时 HAL 桩模拟 CH1 启动成功、CH2 启动失败，确认 CH1 被停止、三路 CCR 和状态全部清零，回滚测试通过。`UV4.exe` GUI/批处理仍受执行环境限制，不能在记录中写成 UV4 批处理通过。未烧录或实测舵机。

Y_MIN 修改后再次执行完整构建：19 个 C 文件、启动汇编、ArmLink 和 FromELF 全部退出码为 0，已更新 `MDK-ARM/Objects/VisionClaw_Motion.axf` 和 `VisionClaw_Motion.hex`。未烧录或实物测试。

Z 轴预设位置于 2026-11-10 按用户给出的机械定义和实机方向更新：`Z_UP_US=2000`（180°）、`Z_DOWN_US=1000`（0°）。`Z UP`/`Z DOWN` 仍使用 700ms 平滑移动，通用 `SERVO Z <us> <ms>` 范围保持 1000~2000us。舵机平滑移动期间的新命令会进入每个舵机独立队列，队列深度 16，当前动作结束后按顺序执行；STOP 和 ESTOP 清空队列。临时 HAL 桩验证了 `Z UP` 后立即 `Z DOWN` 两条命令按序执行。完整 ArmClang/ArmAsm/ArmLink/FromELF 构建通过并更新 HEX；方向与机械端点仍以实物复核为准。

2026-11-10 进一步将 MG90S 独立允许脉宽扩展为 500~2500us；两台 DS3120MG 继续保持 1000~2000us。`Servo_MoveTo`、`Servo_SetPulseUs` 和 `Servo_SetAngle` 均按舵机 ID 选择范围。随后按实机方向将预设端点更新为 `Z_UP_US=2500`、`Z_DOWN_US=500`。范围隔离临时测试和完整构建均通过，尚未烧录。

