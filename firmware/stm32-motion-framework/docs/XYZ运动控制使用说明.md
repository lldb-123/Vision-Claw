# XYZ 三轴运动控制工程

当前硬件模型：X/Y 为 STEP/DIR 步进电机，Z 为 MG90S 位置舵机。不是三路步进，也不提供 XYZ 直线插补。三轴可分别下发命令并同时执行；自动避障、拨料轨迹和整机 SORT 尚未集成。

## 打开与构建

双击 MDK-ARM/open-keil.cmd；已有 Keil 窗口请关闭工程后重新打开，以加载新增 stm32_actuators.c。目标仍为 VisionClaw_Motion，按 F7 构建。
输出 MDK-ARM/Objects/VisionClaw_Motion.hex。命令行执行 MDK-ARM/build-keil.ps1；GNU 构建执行 platform/build.ps1。
本次两个工具链均编译链接成功：Keil 0 错误、0 警告；GNU 仍有原有第三方/系统调用占位警告。没有烧录、台架测试或舵机位置反馈验证。

## 工程接线约定

| 功能 | STM32F407 引脚 | 说明 |
|---|---|---|
| X STEP / DIR / EN | PA0 / PA1 / PA4 | EN 低有效，上电禁用 |
| Y STEP / DIR / EN | PA2 / PA3 / PA5 | 新增 PA5，EN 低有效，上电禁用 |
| Z 舵机信号 | PA6 / TIM3_CH1 | 新增，50Hz；上电不启动 PWM |
| X 负/正限位 | PB0 / PB1 | 低有效，上拉 |
| Y 负/正限位 | PB2 / PB3 | 低有效，上拉 |
| 急停输入 | PB4 | 低有效，上拉 |
| 串口 TX / RX | PD5 / PD6 | USART2，115200 8N1 |

PA5、PA6 是本次选择的工程配置，尚未确认现场已按此接线。Z 舵机需按其实际规格使用独立合适电源，控制地共地；不要由 STM32 的 GPIO/3V3 给舵机电机供电。

## 控制命令

每条命令以回车/换行结束。ACK 表示命令接受，ERR 表示拒绝。

| 命令 | 含义 |
|---|---|
| STATUS | 查询 X/Y 位置、状态、回零、限位；Z 当前输出/目标脉宽、使能、busy、estop |
| ENABLE X / ENABLE Y | 启用对应步进驱动 |
| ENABLE Z | 启动 Z PWM，首次目标默认 1500us；可能引起实物转动 |
| MOVE X 200 200 | X 相对移动 200 脉冲，最高 200 脉冲/秒；Y 同理 |
| GOTO Y 1000 300 | Y 移动到软件脉冲坐标 1000；X 同理 |
| HOME X / HOME Y | 朝负限位回零，带退离和低速复寻，30秒超时 |
| SERVO Z 1600 1000 | Z 输出从当前脉宽平滑变化到 1600us，历时 1000ms |
| STOP X / STOP Y | 定位时减速停止；回零时取消回零 |
| STOP Z | 停止更新目标，保持当前输出脉宽 |
| ESTOP | 锁存三轴急停，终止 XY 脉冲，X/Y EN 拉高，Z 保持最后输出脉宽 |
| CLEAR | 物理急停释放后清除锁存；XY 再次运动需重新 ENABLE |

硬件急停输入在 TIM6 中断内停止 XY 脉冲并冻结 Z 输出，保留使能/保持力；串口 ESTOP 额外断开 XY 使能。Z 无位置反馈，冻结 PWM 目标不能保证实物瞬间停止。需要断电的紧急停止应由实际硬件回路实现。

Z 默认范围 1000~2000us，时间 20~30000ms，配置在 Core/Inc/z_axis_config.h。拒绝越界、未使能、急停锁存和忙时覆盖目标。STOP Z 后可以发新目标。没有 HOME Z 命令：舵机没有原点传感器，不能假称回零已完成。

Z busy=0 仅代表目标输出过程结束，不代表实物已经到位。界面明确报告 feedback=NONE。第一次使能的 1500us 及各端点必须在装连杆前校准。不能把脉宽直接当毫米高度或已验证角度。

## 推荐台架验证顺序

1. 先观察上电 X/Y EN 高、Z 无 PWM，并检查串口 STATUS。
2. 空载验证各路 ENABLE 和短距离 XY 正反向移动。
3. 测量 PA6 为 20ms 周期，测试合法、越界及忙时 SERVO 命令，再测试 STOP Z、ESTOP、CLEAR。
4. 核对 XY 限位、回零和方向；回零开关消抖、退离距离还需要结合实物完善。
5. 分别校准 Z 抬起/拨料脉宽与 XY 每毫米脉冲数，再设计带安全高度约束的组合分拣轨迹。

DS3120 转盘没有加入本三轴工程，SERVO_DS3120 的兼容 API 会返回 false，不会误驱动 Z。当前串口为人工调试入口，没有正式任务编号、DONE、重试去重和连续高速收包保证。
## 毫米坐标与 Z 升降（2026-11-08）

新增配置：`Core/Inc/motion_config.h` 中的 `X_STEPS_PER_MM`、`Y_STEPS_PER_MM`，当前暂设 80.0，必须按实际电机整步数、细分和丝杆导程校准。速度参数使用 mm/s，固件自动换算为脉冲/s。

新增命令：
- `MOVE_MM X 10 5`：X 相对移动 10mm，速度 5mm/s。
- `GOTO_MM Y 80 5`：Y 移到绝对坐标 80mm，速度 5mm/s。
- `Z UP`：Z 移到 `Z_UP_US`（默认 1150us）。
- `Z DOWN`：Z 移到 `Z_DOWN_US`（默认 1850us）。
- `STOP Z`：保持当前舵机脉宽。
- `STATUS`：X/Y 同时回报步数和换算后的毫米位置。

Z 仍是无位置反馈舵机，UP/DOWN 是脉宽位置命令，不代表机构已经到位。首次使用前必须断开负载校准两个脉宽，并确认舵机独立供电和共地。Keil 编译已通过 0 错误、0 警告，生成 `MDK-ARM/Objects/VisionClaw_Motion.hex`；尚未烧录和实物验证。
