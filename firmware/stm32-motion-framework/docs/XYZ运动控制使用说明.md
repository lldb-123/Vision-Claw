# XYZ 三轴运动控制工程

> 2026-11-11 更新：当前固件已取消 X/Y 上电自动使能，也不再读取 PB0、PB1、PB3、PB6 的物理限位开关。上电和 `CLEAR` 成功后 PA4、PA5 均保持高电平，必须显式执行 `ENABLE X` / `ENABLE Y`。X/Y 使用暂定 `0～200mm` 软件行程，`HOME` 等同当前位置置零。最新操作流程见[三轴电机使用说明](三轴电机使用说明.md)。

当前硬件模型：X/Y 为 STEP/DIR 步进电机，MG90S 与两台 DS3120MG 使用三路独立 PWM。不是三路步进，也不提供 XYZ 直线插补；自动避障、拨料轨迹和整机 SORT 尚未集成。

## 打开与构建

打开 MDK-ARM/VisionClaw_Motion.uvprojx，目标为 VisionClaw_Motion，按 F7 构建。
输出 MDK-ARM/Objects/VisionClaw_Motion.hex。HAL/CMSIS 依赖已本地化到工程 Drivers/ 目录。

## 工程接线约定

| 功能 | STM32F407 引脚 | 说明 |
|---|---|---|
| X STEP / DIR / EN | PA0 / PA1 / PA4 | EN 低有效，上电禁用 |
| Y STEP / DIR / EN | PA2 / PA3 / PA5 | 新增 PA5，EN 低有效，上电禁用 |
| MG90S 信号 | PA6 / TIM3_CH1 | 50Hz；上电以 1500us 启动 PWM |
| DS3120MG #1 信号 | PC7 / TIM3_CH2 | 50Hz；上电以 1500us 启动 PWM |
| DS3120MG #2 信号 | PC8 / TIM3_CH3 | 50Hz；上电以 1500us 启动 PWM |
| 急停输入 | PB4 | 低有效，上拉 |
| 串口 TX / RX | PD5 / PD6 | USART2，115200 8N1 |

PA6、PC7、PC8 均使用 TIM3 的独立比较通道，共用 PSC=83、ARR=19999 的 50Hz 时基。三台舵机需使用独立合适电源，控制地共地；不要由 STM32 的 GPIO/3V3 给舵机电机供电。

## 控制命令

每条命令以回车/换行结束。ACK 表示命令接受，ERR 表示拒绝。

| 命令 | 含义 |
|---|---|
| STATUS | 查询 X/Y 位置、状态、使能、软件零点；Z 当前输出/目标脉宽、使能、busy、estop |
| ENABLE X / ENABLE Y | 启用对应步进驱动 |
| ENABLE Z | 兼容旧命令；三路 PWM 已在上电初始化时启动 |
| MOVE X 200 200 | X 相对移动 200 脉冲，最高 200 脉冲/秒；Y 同理 |
| GOTO Y 1000 300 | Y 移动到软件脉冲坐标 1000；X 同理 |
| HOME X / HOME Y | 当前等同原地软件置零，不驱动电机 |
| SERVO Z 1600 1000 | Z 输出从当前脉宽平滑变化到 1600us，历时 1000ms |
| STOP X / STOP Y | 定位时减速停止 |
| STOP Z | 停止更新目标，保持当前输出脉宽 |
| ESTOP | 锁存三轴急停，终止 XY 脉冲，X/Y EN 拉高，三路舵机保持最后输出脉宽 |
| CLEAR | 物理急停释放后清除锁存并禁用 X/Y；再次运动需重新 ENABLE |

硬件急停输入在 TIM6 中断内停止 XY 脉冲并冻结 Z 输出，保留使能/保持力；串口 ESTOP 额外断开 XY 使能。Z 无位置反馈，冻结 PWM 目标不能保证实物瞬间停止。需要断电的紧急停止应由实际硬件回路实现。

MG90S 当前合法脉宽为 500~2500us，两台 DS3120MG 保持 1000~2000us；平滑时间范围均为 20~30000ms。拒绝越界、未使能和急停锁存；平滑移动期间可继续发送命令，每个舵机最多排队 16 条，当前动作完成后按顺序执行。STOP Z 和 ESTOP 会清空相应待执行队列。没有 HOME Z 命令：舵机没有原点传感器，不能假称回零已完成。

Z busy=0 仅代表目标输出过程结束，不代表实物已经到位。界面明确报告 feedback=NONE。第一次使能的 1500us 及各端点必须在装连杆前校准。不能把脉宽直接当毫米高度或已验证角度。

## 推荐台架验证顺序

1. 先保持三台舵机空载，观察上电 X/Y EN 高且 PA6、PC7、PC8 均为 50Hz、1500us PWM。
2. 空载验证各路 ENABLE 和短距离 XY 正反向移动。
3. 分别测量 PA6、PC7、PC8 的 20ms 周期，测试合法、越界及忙时 SERVO 命令，再测试 STOP Z、ESTOP、CLEAR。
4. 核对 X/Y 方向和软件行程；当前不读取物理限位，软件最大行程暂设 200mm。
5. 分别校准 Z 抬起/拨料脉宽与 XY 每毫米脉冲数，再设计带安全高度约束的组合分拣轨迹。

两台 DS3120MG 已接入 TIM3_CH2 和 TIM3_CH3。代码中可通过 `Servo_SetPulseUs(SERVO_DS3120_1/2, us)` 或 `Servo_MoveTo(...)` 独立控制；当前串口命令仍只提供 MG90S 的 Z 调试入口。串口没有正式任务编号、DONE、重试去重和连续高速收包保证。
## 毫米坐标与 Z 升降（2026-11-08）

新增配置：`Core/Inc/motion_config.h` 中的 `X_STEPS_PER_MM`、`Y_STEPS_PER_MM`，当前暂设 80.0，必须按实际电机整步数、细分和丝杆导程校准。速度参数使用 mm/s，固件自动换算为脉冲/s。

新增命令：
- `MOVE_MM X 10 5`：X 相对移动 10mm，速度 5mm/s。
- `GOTO_MM Y 80 5`：Y 移到绝对坐标 80mm，速度 5mm/s。
- `Z UP`：Z 移到 `Z_UP_US`，当前按实机方向为 2500us，700ms 平滑移动。
- `Z DOWN`：Z 移到 `Z_DOWN_US`，当前按实机方向为 500us，700ms 平滑移动。
- `STOP Z`：保持当前舵机脉宽。
- `STATUS`：X/Y 同时回报步数和换算后的毫米位置。

Z 仍是无位置反馈舵机，UP/DOWN 是脉宽位置命令，不代表机构已经到位。首次使用前必须断开负载校准两个脉宽，并确认舵机独立供电和共地。Keil 编译已通过 0 错误、0 警告，生成 `MDK-ARM/Objects/VisionClaw_Motion.hex`；尚未烧录和实物验证。

## 审查修复（2026-11-08）

已按实物调试前审查修正：

- `MOVE_MM` 允许相对位移，但结果必须落在 `0～200mm` 软件范围内；`GOTO_MM` 仍要求绝对坐标位于该范围。
- `GOTO`/`GOTO_MM` 需要先通过 `HOME` 或 `SET_ZERO` 建立软件零点。
- 当前已删除限位开关消抖、寻边和限位停止逻辑；PB0、PB1、PB3、PB6 不再用于输入。物理急停 PB4 仍会拉高 X/Y EN。

仍待后续：ACK/DONE 任务编号和去重、软件限位按实际行程标定、Z 反馈和完整机械联调。

## 三轴同时控制与联调修复（2026-11-11）

针对整机联调时“只有 Z 轴能动、无法同时控制三轴”的问题完成以下修复：

- **解耦相对移动与回零前置条件**：`MOVE`、`MOVE_MM` 及 `MOVE_XYZ` 不要求 `homed=1`，但所有目标必须位于 `0～200mm` 软件行程内；`GOTO`、`GOTO_MM`、`GOTO_XYZ` 仍要求通过 `HOME` 或 `SET_ZERO` 建立软件零点。
- **上电使能策略已再次收紧**：曾短暂采用 X/Y 上电自动使能，现已撤销；当前上电及 `CLEAR` 成功后 X/Y 均保持禁用，必须显式使能。
- **新增单条三轴同步命令**：`MOVE_XYZ <dx_mm> <dy_mm> <z_us> <speed_mm/s> [z_ms]` 与 `GOTO_XYZ <x_mm> <y_mm> <z_us> <speed_mm/s> [z_ms]`，X/Y 按位移比例分配速度与加速度以同步到达，Z 轴并行动作；同时新增 `SERVO 1/2 <us> <ms>` 控制两台 DS3120MG。
- **USART2 中断 + 512 字节环形缓冲接收**：替换原逐字节轮询 `HAL_UART_Receive`，消除多行命令连发时的 ORE 溢出丢字节问题。
- **细化串口错误码**：将被笼统合并为 `ERR REJECTED` 的拒绝原因细化为 `ERR X_NOT_HOMED`、`ERR Y_NOT_HOMED`、`ERR X_BUSY`、`ERR Y_BUSY`、`ERR X_FAULT`、`ERR Y_FAULT`、`ERR ESTOP_ACTIVE`、`ERR RANGE` 等；物理限位错误码已随限位逻辑删除。
