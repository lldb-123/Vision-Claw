# 三轴安全启用与操作手册

- 记录日期：2026-11-11，Asia/Shanghai。
- 对话编号：009。
- 关联仓库/分支：`lldb-123/Vision-Claw` / `stm32-progress-20261111`。
- 相关历史记录：[007](2026-11-11-007-git-sync-and-firmware-audit.md)、[008](2026-11-11-008-xyz-simultaneous-control-fix.md)。
- 本次状态：源码安全修改和 Keil 构建完成，尚未烧录。

## 接续摘要

在队友提交 `d3f4994` 的基础上，撤销 X/Y 上电自动使能，并让 `CLEAR` 成功后将 PA4、PA5 拉高。随后移除物理限位开关逻辑，改用暂定 `0～200mm` 软件行程；`HOME` 改为原地软件置零。Keil V6.22 串行构建 0 错误、0 警告，并生成新 HEX。

## 本次新增或确认的事实

- `d3f4994` 与旧本地分支 `86a08f5` 为直接父子关系，已通过 `--ff-only` 快进。
- 备份分支 `backup/stm32-progress-20261111-86a08f5` 保留在 `86a08f5`。
- 当前 PA4= X EN、PA5= Y EN，均为低有效；上电初始化先拉高。
- 删除初始化末尾自动拉低 PA4、PA5 的逻辑后，X/Y 上电默认禁用。
- `CLEAR` 成功后现在同时调用 `Servo_ClearFault()` 并把 PA4、PA5 拉高。
- `ENABLE X` 和 `ENABLE Y` 仍分别只拉低对应轴。
- PB0、PB1、PB3、PB6 不再配置为限位输入，也不参与运动停止判断。
- X/Y 软件行程暂设为 `0～200mm`，按 80 脉冲/mm 对应 `0～16000` 脉冲。
- 当前 `HOME X/Y` 与 `SET_ZERO X/Y` 等价：在当前位置建立软件零点，不驱动电机。

## 决策与方案

- 安全优先：任何上电、故障恢复都不自动给 X/Y 驱动使能。
- 保留 `d3f4994` 的未回零相对运动、USART2 中断接收、XYZ 组合命令和详细错误码。
- `CLEAR` 只清故障并强制 X/Y 禁用；重新运动必须显式执行使能命令。
- `HOME X`、`HOME Y` 仍要求对应 EN 引脚为低，避免驱动器关闭时启动回零状态机。
- 所有相对和绝对运动目标都必须位于 `0～200mm` 软件范围内，超出返回 `ERR RANGE`。

## 文件与实际修改

| 路径 | 修改 | 实际状态 |
| --- | --- | --- |
| `firmware/stm32-motion-framework/platform/main.c` | 删除上电自动使能；`CLEAR` 成功后禁用 X/Y；移除限位引脚初始化 | 已落盘、已构建、未提交 |
| `firmware/stm32-motion-framework/Core/Inc/motion_config.h` | X/Y 软件范围暂设 0～200mm；删除限位引脚和参数 | 已落盘、已构建、未提交 |
| `firmware/stm32-motion-framework/Core/Src/motion_control.c` | 删除限位采样、消抖和寻边回零；增加全运动软件范围检查 | 已落盘、已构建、未提交 |
| `firmware/stm32-motion-framework/Core/Inc/motion_control.h` | 从轴状态结构删除限位字段 | 已落盘、已构建、未提交 |
| `firmware/stm32-motion-framework/Core/Src/stm32_sensors.c` | 传感器读取仅保留光电和急停 | 已落盘、未构建（当前 Keil 工程未包含） |
| `firmware/stm32-motion-framework/Core/Inc/stm32_sensors.h` | 传感器结构删除限位字段 | 已落盘、未构建（当前 Keil 工程未包含） |
| `firmware/stm32-motion-framework/docs/三轴电机使用说明.md` | 新增当前三轴接线、命令、状态和安全操作说明 | 已落盘 |
| `firmware/stm32-motion-framework/README.md` | 校正上电和 CLEAR 的使能说明 | 已落盘 |
| `firmware/stm32-motion-framework/docs/XYZ运动控制使用说明.md` | 增加最新安全策略覆盖说明 | 已落盘 |

## 验证与证据

- Keil ArmClang V6.22 串行完整构建：`0 Error(s), 0 Warning(s)`。
- Program Size：`Code=22446 RO-data=1098 RW-data=20 ZI-data=5364`。
- HEX：`MDK-ARM/Objects/VisionClaw_Motion.hex`，66,336 字节。
- HEX SHA-256：`3484ABBBEE5187F2F2682CAC46FB75B1A578E6863DC38B6777E993262F07AC88`。
- 并行构建曾因 ArmClang 内存不足失败；使用 `-j0` 串行构建成功。
- 未烧录；硬件现象仍待联调确认。

## 未解决的问题与下一步

- 当前 A4988 存在严重发热和无保持力矩现象，烧录前必须先排除相线、VREF、VMOD、模块损坏和机械卡死。
- 烧录后先确认上电 PA4、PA5 均为高，`STATUS` 显示 X/Y `enabled=0`。
- 分别执行 `ENABLE X`、`ENABLE Y` 和低速短距离点动，再测试 HOME 与三轴组合命令。

## 给下一次对话的提示

不要沿用历史记录中“上电默认使能 X/Y”或“CLEAR 后恢复使能”的旧结论。当前正确行为是上电和 CLEAR 成功后 X/Y 均禁用。
