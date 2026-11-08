# VisionClaw STM32 XYZ 运动控制

STM32F407VET6 运动控制工程，服务于智能分拣设备。当前控制模型为：

- X、Y：A4988 STEP/DIR 步进轴，支持回零、限位、加减速、脉冲坐标和毫米坐标。
- Z：MG90S 舵机，使用 PWM 脉宽控制升降，支持上升、下降、停止和急停锁存。
- 串口：USART2，115200-8-N-1，PD5=TX、PD6=RX。

当前工程支持三轴独立控制和并发执行。Z 轴没有位置反馈；三轴直线插补、自动分拣轨迹和整机任务协议仍需在实物联调后加入。

## 目录

```text
Core/
├─ Inc/                    头文件、引脚和运动参数
│  ├─ motion_config.h      X/Y 引脚、限位、速度和毫米换算参数
│  ├─ motion_control.h     X/Y 运动接口
│  ├─ stm32_actuators.h    Z 舵机接口
│  └─ z_axis_config.h      Z 上升/下降脉宽
└─ Src/
   ├─ motion_control.c     X/Y 脉冲、加减速、回零、急停
   └─ stm32_actuators.c    Z PWM 平滑移动和停止
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

推荐双击：

```text
D:\Users\linjiangwen\Documents\ChatGPT\工创赛\MDK-ARM\open-keil.cmd
```

打开后选择 `VisionClaw_Motion`，按 **F7**。也可以在 PowerShell 执行：

```powershell
Set-Location 'D:\Users\linjiangwen\Documents\ChatGPT\工创赛\MDK-ARM'
.\build-keil.ps1
```

工具链、Pack、许可证缓存和临时目录均配置在 D 盘。工程依赖本机已有的 HAL/CMSIS 路径：`D:\EmbeddedDev\STM32_Workspace\Task1_CubeMX_Fixed`。Keil 编译验证结果为 0 错误、0 警告。

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
| Z 舵机信号 | PA6 / TIM3_CH1 | 50Hz PWM |
| X 负限位 / 正限位 | PB0 / PB1 | 低有效，上拉 |
| Y 负限位 / 正限位 | PB2 / PB3 | 低有效，上拉 |
| 急停 | PB4 | 低有效，上拉 |
| 串口 TX / RX | PD5 / PD6 | USART2，115200 8N1 |

Z 舵机使用独立合适电源，控制地与 STM32 共地。接入机构前先断开负载校准脉宽，不能用 STM32 的 3.3V 给舵机电机供电。

## 串口命令

每条命令以回车或换行结束。先使能并回零：

```text
ENABLE X
ENABLE Y
ENABLE Z
HOME X
HOME Y
```

毫米坐标控制：

```text
GOTO_MM X 100 5
GOTO_MM Y 80 5
MOVE_MM X 10 5
```

`GOTO_MM` 使用绝对坐标，`MOVE_MM` 使用相对位移，速度单位是 mm/s。脉冲换算参数在 `Core/Inc/motion_config.h`：

```c
#define X_STEPS_PER_MM 80.0f
#define Y_STEPS_PER_MM 80.0f
```

公式为：`脉冲/毫米 = 每转脉冲数 ÷ 丝杆导程`。80.0 只是当前开发默认值，必须按实际电机细分和丝杆导程校准。

Z 轴控制：

```text
Z UP
Z DOWN
SERVO Z 1600 1000
STOP Z
```

`Z UP` 和 `Z DOWN` 的脉宽在 `Core/Inc/z_axis_config.h` 配置；`SERVO Z` 的范围默认 1000~2000us。`STATUS` 返回 X/Y 步数、毫米位置、限位和 Z 脉宽状态。`ESTOP` 急停，`CLEAR` 在物理急停释放后清除锁存。

## 当前边界

源码已经完成 Keil 编译和链接，尚未完成烧录、示波器时序测量、机械方向校准、限位消抖和 Z 舵机实物到位验证。Z 的 `busy=0` 只表示 PWM 输出过程结束，不代表机构已到位。开始台架测试时，使用低速、短距离、断开机构负载的顺序逐轴验证。

## 审查修复

已修复负向 MOVE_MM、回零长行程限制、GOTO 回零前拒绝、原点限位处理、限位采样稳定和物理急停关断 XY EN。Keil 重新编译 0 错误、0 警告。
