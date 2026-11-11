# GitHub 同步与 STM32 固件整理

- 记录日期：2026-11-11，Asia/Shanghai。
- 对话编号：007。
- 关联仓库/分支：`lldb-123/Vision-Claw` / `stm32-progress-20261111`。
- 相关历史记录：[006](2026-11-09-006-stm32-dependencies.md)。
- 本次状态：进行中，等待分支推送与最终远程核对。

## 接续摘要

从原始工作目录选择性迁移 STM32 运动控制工程到 Git 克隆，不整体覆盖远程。保留远程 `motion_control.c` 的回零/限位安全修复，合入三路舵机、PB6、Z 轴独立脉宽范围和本地化 HAL/CMSIS。Keil ArmClang 完整构建已通过，生成 HEX；目标分支已创建，尚未完成提交与推送。

## 用户本次目标与约束

- 将截至 2026-11-11 的有效本地成果安全同步到团队 GitHub 仓库。
- 不直接推送 `main`，不强制推送，不覆盖队友提交。
- 排除 Keil 构建产物、个人调试配置、备份、密钥和无关文件。
- 以源码实际状态为准，不把计划功能写成已完成。

## 本次新增或确认的事实

- 原始目录不是 Git 仓库；Git 克隆现位于原目录下的 `Vision-Claw-git`。
- 远程 `origin/main` 为 `a3b1ccc`。
- 克隆检出后显示的 22 个修改仅由 CRLF/LF 差异造成，忽略行尾后无内容变化。
- 远程 `motion_control.c` 比原始目录副本更新，包含正向最大步数、回零步数清零、限位消抖和并发安全修复。
- 源码确认 MG90S 范围为 500~2500us，两台 DS3120MG 保持 1000~2000us；`Z UP=2500us`、`Z DOWN=500us`。
- 用户已实测 X/Y 电机运动、Y 轴回零和 MG90S 串口控制；两台 DS3120MG、Orange Pi 正式协议和完整自动分拣尚未验证。

## 决策与方案

- 以最新 `origin/main` 为基线创建 `stm32-progress-20261111`。
- 不复制旧的本地 `motion_control.c`；保留远程安全版本。
- 运动配置仅把 `Y_MIN_Pin` 改为 `PB6`，保留远程动态最大回零步数等配置。
- `main.c` 合并三路 PWM 和 GPIOC 初始化，同时保留 `MOVE_MM` 的相对位移范围检查。
- 本地化 HAL/CMSIS 只在必要目录保存，`system_stm32f4xx.h` 使用 CMSIS Device Include 中的标准位置。
- Keil 文件中的旧 `D:/EmbeddedDev` 源文件和头文件路径改为相对路径。
- 构建脚本自动查找本机 `UV4.exe`，不再依赖原电脑的 Pack、许可证和临时目录。

## 文件与实际修改

| 路径 | 修改 | 实际状态 |
| --- | --- | --- |
| `firmware/stm32-motion-framework/Core/Inc/motion_config.h` | `Y_MIN_Pin=GPIO_PIN_6`，保留远程回零安全配置 | 已落盘、已构建 |
| `firmware/stm32-motion-framework/Core/Src/stm32_actuators.c` | 三路独立舵机、500~2500us Z 范围、命令队列和安全初始化 | 已落盘、已构建 |
| `firmware/stm32-motion-framework/Core/Inc/stm32_actuators.h` | 三路舵机接口及 DS3120MG 独立范围 | 已落盘、已构建 |
| `firmware/stm32-motion-framework/Core/Inc/z_axis_config.h` | `Z UP=2500us`、`Z DOWN=500us` | 已落盘、已构建 |
| `firmware/stm32-motion-framework/platform/main.c` | GPIOC、PC7/PC8、三通道初始化、PB6、失败关断；保留远程 MOVE_MM 检查 | 已落盘、已构建 |
| `firmware/stm32-motion-framework/Drivers/` | HAL v1.8.6、CMSIS Device v2.6.11、CMSIS Core 头文件 | 已落盘、已构建 |
| `firmware/stm32-motion-framework/Core/Src/system_stm32f4xx.c` | STM32F4 系统初始化源文件 | 已落盘、已构建 |
| `firmware/stm32-motion-framework/MDK-ARM/VisionClaw_Motion.uvprojx` | 相对依赖路径，补入 EXTI、DMA EX 源文件 | 已落盘、已构建 |
| `firmware/stm32-motion-framework/MDK-ARM/VisionClaw_Motion.uvoptx` | 保留远程用户配置，仅修正失效源文件路径 | 已落盘、已构建 |
| `firmware/stm32-motion-framework/MDK-ARM/build-keil.ps1` | 自动查找 Keil，移除旧电脑硬编码目录 | 已落盘、已构建 |
| `firmware/stm32-motion-framework/MDK-ARM/open-keil.cmd` | 使用脚本相对工程路径并自动查找 Keil | 已落盘 |
| `.gitignore` | 排除 Keil Objects/Listings、AXF/O/D、用户界面配置和备份 | 已落盘 |

## 验证与证据

- `git fetch origin --prune`：成功，远程 `main=a3b1ccc`。
- `VisionClaw_Motion.uvprojx` 中全部源文件和头文件路径：解析成功。
- Keil ArmClang V6.22 完整构建：`0 Error(s), 0 Warning(s)`。
- 生成 `MDK-ARM/Objects/VisionClaw_Motion.hex`，SHA-256 为 `8F4D308C8A6A81BDE1ACDA084526900A0E1AA238159477D18768CAF1B5FB3CC7`。
- 未烧录，未连接硬件。

## 未解决的问题与下一步

- 提交筛选后的文件到 `stm32-progress-20261111`。
- 推送分支并核对本地 HEAD、远程分支和提交差异。
- 两台 DS3120MG 仍需实物验证；Orange Pi 正式协议与完整分拣流程未完成。

## 给下一次对话的提示

沿用本次 Git 分支和构建结论。若远程后续更新，先重新 fetch，再检查是否影响 `motion_control.c` 的远程安全修复。不要把构建产物或个人 ST-Link 配置提交到仓库。
