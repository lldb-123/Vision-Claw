# VisionClaw STM32 XYZ 运动控制

STM32F407VET6 运动控制工程，服务于智能分拣设备。当前控制模型为：

- X、Y：A4988 STEP/DIR 步进轴，支持软件零点、软件行程、加减速、脉冲坐标和毫米坐标。
- Z：MG90S 舵机，使用 PWM 脉宽控制升降，支持上升、下降、停止和急停锁存。
- 两台 DS3120MG：分别使用 TIM3_CH2 和 TIM3_CH3，与 MG90S 共用 50 Hz 时基，脉宽独立。
- 串口：USART2，115200-8-N-1，PD5=TX、PD6=RX。

当前工程支持 X/Y 独立控制以及三路独立舵机 PWM。舵机没有位置反馈；三轴直线插补、自动分拣轨迹和整机任务协议仍需在实物联调后加入。

## 目录

```text
Core/
├─ Inc/                    头文件、引脚和运动参数
│  ├─ motion_config.h      X/Y 引脚、软件行程、速度和毫米换算参数
│  ├─ motion_control.h     X/Y 运动接口
│  ├─ stm32_actuators.h    三路舵机接口
│  └─ z_axis_config.h      Z 上升/下降脉宽
└─ Src/
   ├─ motion_control.c     X/Y 脉冲、加减速、软件范围、急停
   └─ stm32_actuators.c    三路独立 PWM、平滑移动和停止
platform/
├─ main.c                  HAL 初始化、串口命令和主循环
├─ stm32f4xx_hal_conf.h    HAL 配置
└─ device/                 F407 设备头文件
MDK-ARM/
├─ VisionClaw_Motion.uvprojx   Keil 工程
├─ open-keil.cmd               打开工程
├─ build-keil.ps1              命令行构建
└─ Objects/                    Keil 生成物（HEX/AXF）
docs/
├─ XYZ运动控制使用说明.md       接线和完整命令
└─ 坐标与Z轴命令.md              坐标换算和快速命令
build/                         GNU 构建临时产物
```

`MDK-ARM/Objects`、`build`、Keil 用户缓存和日志不作为源码的一部分。旧的框架压缩包保留在仓库根目录，仅作原始资料备份。

## Keil 编译

直接打开：

```text
MDK-ARM\VisionClaw_Motion.uvprojx
```

选择 `VisionClaw_Motion` 后按 **F7**。HAL/CMSIS 已放在工程的 `Drivers/` 目录，工程不再依赖旧电脑的 `D:\EmbeddedDev` 路径。

输出文件：

```text
MDK-ARM\Objects\VisionClaw_Motion.hex
MDK-ARM\Objects\VisionClaw_Motion.axf
```

## 接线约定

| 功能 | 引脚 | 说明 |
|---|---|---|
| X STEP / DIR / EN | PA0 / PA1 / PA4 | EN 低有效 |
| Y STEP / DIR / EN | PA2 / PA3 / PA5 | EN 低有效 |
| MG90S 信号 | PA6 / TIM3_CH1 | 50Hz PWM |
| DS3120MG #1 信号 | PC7 / TIM3_CH2 | 50Hz PWM |
| DS3120MG #2 信号 | PC8 / TIM3_CH3 | 50Hz PWM |
| 急停 | PB4 | 低有效，上拉 |
| 串口 TX / RX | PD5 / PD6 | USART2，115200 8N1 |

三路舵机使用独立合适电源，控制地与 STM32 共地。接入机构前先断开负载校准脉宽，不能用 STM32 的 3.3V 给舵机电机供电。三路 PWM 上电均以 1500us 启动。

## 舵机 C 接口

`stm32_actuators.h` 提供三个独立 ID：

```c
SERVO_MG90S
SERVO_DS3120_1
SERVO_DS3120_2
```

立即设置单路脉宽：

```c
Servo_SetPulseUs(SERVO_MG90S, 1500);
Servo_SetPulseUs(SERVO_DS3120_1, 1500);
Servo_SetPulseUs(SERVO_DS3120_2, 1500);
```

指定时间平滑移动到目标脉宽：

```c
Servo_MoveTo(SERVO_DS3120_1, 1800, 500);
```

MG90S 当前允许 500~2500us；两台 DS3120MG 仍允许 1000~2000us，最终范围需按实物校准。

## 串口命令

串口（USART2，115200 8N1）已采用 **中断 + 512 字节环形缓冲区接收**，支持多行连续发送不丢字节。每条命令以回车或换行结束。

当前固件不读取 PB0、PB1、PB3、PB6。X/Y 行程由 `motion_config.h` 中的 `X_MIN_MM`、`X_MAX_MM`、`Y_MIN_MM`、`Y_MAX_MM` 软件限制，当前暂设为 `0～200mm`。

### 1. 使能、置零与软件零点
当前安全版本上电后，X/Y 的 PA4、PA5 均为高电平，两个 A4988 默认禁用；Z 舵机初始化后启用。需要显式使能 X/Y：

```text
ENABLE ALL
ENABLE X
ENABLE Y
ENABLE Z
DISABLE ALL
SET_ZERO
HOME ALL
HOME X
HOME Y
```

- `SET_ZERO`（或 `SET_ZERO X` / `SET_ZERO Y`）：将当前位置设为 `0` 并标记 `homed=1`。
- `HOME` / `HOME ALL`：当前等同软件置零，只在当前位置建立坐标零点，不产生运动脉冲。

### 2. 三轴同时运动命令
```text
MOVE_XYZ 20 20 2500 10
MOVE_XYZ -20 -20 500 10 700
GOTO_XYZ 100 80 2500 15
GOTO_XYZ 100 80 500 15 700
```

- `MOVE_XYZ <dx_mm> <dy_mm> <z_us> <speed_mm/s> [z_ms]`：**无需先回零**，X/Y 相对移动与 Z 轴脉宽同时启动；X/Y 按位移比例自动分配速度与加速度以同步到达，`z_ms` 省略时默认 `700` ms。
- `GOTO_XYZ <x_mm> <y_mm> <z_us> <speed_mm/s> [z_ms]`：需已建立软件零点（`HOME` 或 `SET_ZERO`），X/Y 绝对坐标与 Z 轴同时运动。

### 3. 单轴毫米与脉冲坐标控制
```text
MOVE_MM X 10 5
MOVE_MM Y -10 5
GOTO_MM X 100 5
GOTO_MM Y 80 5
```

- `MOVE_MM` / `MOVE` 使用相对位移，**无需先回零**即可正反向点动调试，但结果必须在 `0～200mm` 软件行程内；`GOTO_MM` / `GOTO` 使用绝对坐标，需先完成 `HOME` 或 `SET_ZERO`。
- 由于各轴非阻塞并发执行，连续发送多行 `MOVE_MM X ...`、`MOVE_MM Y ...`、`Z UP` 也会三轴同时运动。
- 脉冲换算参数在 `Core/Inc/motion_config.h`：

```c
#define X_STEPS_PER_MM 80.0f
#define Y_STEPS_PER_MM 80.0f
```

公式为：`脉冲/毫米 = 每转脉冲数 ÷ 丝杆导程`。80.0 只是当前开发默认值，必须按实际电机细分和丝杆导程校准。

### 4. Z 轴与舵机控制
```text
Z UP
Z DOWN
SERVO Z 1600 1000
SERVO 1 1500 500
SERVO 2 1500 500
STOP Z
STOP ALL
```

`Z UP` 和 `Z DOWN` 的脉宽在 `Core/Inc/z_axis_config.h` 配置，当前按实机方向 `Z UP=2500us`、`Z DOWN=500us`；MG90S（`SERVO Z`）允许 500~2500us，两台 DS3120MG（`SERVO 1`、`SERVO 2`）允许 1000~2000us。平滑移动期间可继续发送舵机命令，每个舵机最多排队 16 条，当前动作完成后按顺序执行。`STATUS` 返回 X/Y 步数、毫米位置、使能、回零和 Z 脉宽状态。`ESTOP` 急停；`CLEAR` 在物理急停释放后清除故障锁存，同时保持 X/Y 禁用，之后必须再次执行 `ENABLE X`、`ENABLE Y` 或 `ENABLE ALL`。命令被拒绝时会返回具体原因（如 `ERR X_NOT_HOMED`、`ERR X_BUSY`、`ERR X_FAULT`、`ERR ESTOP_ACTIVE` 等）。

## 当前边界

源码已经完成 Keil 编译和链接。用户已实测 X/Y 电机运动、旧版 Y 轴回零和 MG90S 串口脉宽控制；当前无物理限位版本仍需上机标定软件行程，并验证两台 DS3120MG、示波器时序、机械端点和完整自动分拣流程。Z 的 `busy=0` 只表示 PWM 输出过程结束，不代表机构已到位。开始台架测试时，使用低速、短距离、断开机构负载的顺序逐轴验证。

## 审查修复

当前版本已移除物理限位开关读取和寻边回零逻辑，改用 `0～200mm` 软件行程和原地软件零点；物理急停仍会关断 X/Y EN。Keil 编译结果需以本次重新构建日志为准。
