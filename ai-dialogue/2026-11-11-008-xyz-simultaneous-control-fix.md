# XYZ 三轴同时控制与联调问题修复

- 记录日期：2026-11-11，Asia/Shanghai。
- 对话编号：008。
- 关联仓库/分支：`lldb-123/Vision-Claw` / `stm32-progress-20261111`。
- 相关历史记录：[007](2026-11-11-007-git-sync-and-firmware-audit.md)。
- 本次状态：代码修复与 Keil 构建验证通过，待上机烧录与实物联调验证。

## 接续摘要

排查上机联调时“只有 Z 轴能动、无法通过串口同时控制 XYZ 三轴”的根因并完成固件修复：解耦相对移动（`MOVE` / `MOVE_MM` / `MOVE_XYZ`）与回零前置条件（未回零允许正反向相对移动，保留硬限位保护），将上电 X/Y 使能状态与 Z 轴对齐（非急停时默认使能），将 USART2 改为中断 + 512 字节环形缓冲区接收以消除多行命令连发丢字节，新增 `MOVE_XYZ` / `GOTO_XYZ` / `ENABLE ALL` / `SET_ZERO` / `HOME ALL` / `STOP ALL` / `SERVO 1|2` 命令及细化错误码。Keil ArmClang V6.24 完整构建 `0 Error(s), 0 Warning(s)`。

## 用户本次目标与约束

- 查找上机联调 XYZ 三轴时只有 Z 轴能动（单轴独立测试均正常）的原因。
- 修复固件，支持通过串口同时控制 X、Y、Z 三轴运动。

## 本次新增或确认的事实

- 原 `Motion_MoveRelative()` 直接调用 `Motion_Goto()`，而 `Motion_Goto()` 强制要求 `ax[id].homed == true` 且 `0 <= target <= max_steps`；导致未完成回零前，连相对移动 `MOVE` / `MOVE_MM` 也被全部拒绝。
- 原 `init()` 中 Z 轴通过 `Servo_Init()` 上电即启动 PWM 并使能，而 X/Y 轴 `PA4`/`PA5` 上电置高（禁用），行为不一致。
- 原 `main()` 使用 `HAL_UART_Receive(&huart2, &c, 1, 1)` 轮询收字节，处理首条命令及阻塞发送 `ACK\r\n` 期间会导致后续连发命令首字节溢出丢失。
- 原 `command()` 将所有运动拒绝原因统一返回 `ERR REJECTED`，掩盖了未回零、限位有效、轴忙或故障等具体原因。

## 决策与方案

- **相对移动与绝对移动解耦**：`Motion_MoveRelative` / `Motion_MoveRelativeXY` 不再要求 `homed=1`，未回零时允许在 `[-max_steps, +max_steps]` 范围内相对移动并受硬限位保护；`Motion_Goto` / `Motion_GotoXY` 仍要求 `homed=1`（可通过 `HOME` 或新增的 `SET_ZERO` 建立）。
- **串口中断环形缓冲**：新增 `USART2_IRQHandler` 与 512 字节 `uart_rx_buf`（中断优先级 2，低于 `TIM6` 的优先级 1，不影响 50 kHz 步进脉冲时序）。
- **新增三轴同步与便捷命令**：
  - `MOVE_XYZ <dx_mm> <dy_mm> <z_us> <speed_mm/s> [z_ms]`：免回零三轴同步相对运动，X/Y 按位移比例分配速度与加速度。
  - `GOTO_XYZ <x_mm> <y_mm> <z_us> <speed_mm/s> [z_ms]`：回零后三轴同步绝对运动。
  - `ENABLE ALL`、`DISABLE ALL`、`SET_ZERO [X|Y|ALL]`、`HOME ALL`、`STOP ALL`、`SERVO 1|2 <us> <ms>`。
- **细化错误码**：新增 `Motion_CheckMoveError()`，明确返回 `ERR X_NOT_HOMED`、`ERR Y_NOT_HOMED`、`ERR X_LIMIT_MIN/MAX`、`ERR Y_LIMIT_MIN/MAX`、`ERR X_BUSY`、`ERR Y_BUSY`、`ERR X_FAULT`、`ERR Y_FAULT`、`ERR ESTOP_ACTIVE` 等。

## 文件与实际修改

| 路径 | 修改 | 实际状态 |
| --- | --- | --- |
| `firmware/stm32-motion-framework/Core/Inc/motion_control.h` | 新增 `Motion_MoveRelativeXY`、`Motion_GotoXY`、`Motion_SetZero`、`Motion_CheckMoveError` 声明 | 已落盘、已构建 |
| `firmware/stm32-motion-framework/Core/Src/motion_control.c` | 解耦相对移动回零检查，实现双轴比例同步加减速、置零及细化错误检查 | 已落盘、已构建 |
| `firmware/stm32-motion-framework/Core/Inc/stm32_actuators.h` | 新增 `Servo_CanMove` 声明 | 已落盘、已构建 |
| `firmware/stm32-motion-framework/Core/Src/stm32_actuators.c` | 实现 `Servo_CanMove` 供三轴命令原子校验 | 已落盘、已构建 |
| `firmware/stm32-motion-framework/platform/main.c` | USART2 中断环形缓冲、上电默认使能、`MOVE_XYZ`/`GOTO_XYZ`/`SET_ZERO`/`ENABLE ALL` 等命令与详细报错 | 已落盘、已构建 |
| `firmware/stm32-motion-framework/platform/startup.c` | 补齐 GNU 构建向量表 `[16+38]=USART2_IRQHandler` | 已落盘 |
| `firmware/stm32-motion-framework/MDK-ARM/build-keil.ps1` | 增加 `D:\EmbeddedDev\Keil_v5\UV4.exe` 及 Pack/License 自动识别 | 已落盘、已构建 |
| `firmware/stm32-motion-framework/MDK-ARM/open-keil.cmd` | 增加 `D:\EmbeddedDev\Keil_v5\UV4.exe` 自动识别 | 已落盘 |
| `firmware/stm32-motion-framework/README.md` | 更新串口命令说明 | 已落盘 |
| `firmware/stm32-motion-framework/docs/XYZ运动控制使用说明.md` | 补充 2026-11-11 三轴同时控制与联调修复记录 | 已落盘 |

## 验证与证据

- Keil ArmClang V6.24 完整构建：`0 Error(s), 0 Warning(s)`（`Code=23966 RO-data=1182 RW-data=20 ZI-data=5412`）。
- ARM GCC 14.3.1（开启 `-Wall -Wextra`）编译验证：项目核心源文件 0 错误、0 警告。
- `fromelf -c -s` 反汇编核对：`__Vectors` 中 `0x080000D8`（`USART2_IRQn=38`）指向 `USART2_IRQHandler`（`0x080040D1`），`0x08000118`（`TIM6_DAC_IRQn=54`）指向 `TIM6_DAC_IRQHandler`（`0x08003EB5`）。
- 边界加固：`Motion_SetZeroAll` / `Motion_HomeAll` 双轴原子检查、未回零相对移动撞负限位不误置 `homed=1`、`PB4` 内部上拉电平稳定后再初始化 `PA4/PA5` 使能、`MOVE_XYZ`/`GOTO_XYZ` 合成速度越界校验。
- 生成 `MDK-ARM/Objects/VisionClaw_Motion.hex` 与 `VisionClaw_Motion.axf`，并同步至本机 `D:\Users\linjiangwen\Documents\ChatGPT\工创赛`（即 `D:\EmbeddedDev\VisionClawMotion`）工程目录。
- 本轮未连接硬件烧录，待用户上机实测。

## 未解决的问题与下一步

- 用户烧录最新 `VisionClaw_Motion.hex` 后，通过串口发送 `STATUS`、`MOVE_XYZ 20 20 2500 10` 验证三轴同时运动。
- 若实机限位开关为常闭或未接导致触发 `ERR X_LIMIT_MIN/MAX`，按 `STATUS` 返回的 `min/max` 状态调整接线或极性宏。
