# 底部托盘 360° 舵机旋转控制设计

## 目标

在现有 STM32F407VET6 运动控制工程中加入底部托盘旋转控制。执行器为 DS3120MG 360° 连续旋转舵机，复用现有 `TIM3_CH2 / PC7` 输出。控制接口支持顺/逆时针、速度、定时旋转、按标定时间估算角度、停止、急停和状态查询，并保持现有 X/Y/Z 功能兼容。

## 控制模型

DS3120MG 的 PWM 中位脉宽作为停止点。高于停止点和低于停止点分别表示两个方向，偏离中位的幅度映射到速度。由于没有编码器，角度定位采用开环时间估算，`TRAY_MS_PER_DEG` 作为可调标定参数。所有动作完成、停止或急停时输出停止脉宽。

默认配置如下，最终值集中在 `Core/Inc/tray_config.h`：

- 停止脉宽 `1500us`
- 正向范围 `1500 + deadband .. 2000us`
- 反向范围 `1000 .. 1500 - deadband`
- 速度范围 `0..100`
- 角度换算 `TRAY_MS_PER_DEG` 可在实机标定后修改

## 软件结构

- `tray_control.h/.c` 管理托盘状态、速度到脉宽的映射、动作计时、队列清理、急停和快照。
- `tray_config.h` 保存引脚对应的舵机 ID、脉宽范围、停止死区、最大动作时长和每度毫秒数。
- `motion_protocol.c` 增加 `TRAY STOP`、`TRAY CW`、`TRAY CCW`、`TRAY ANGLE`、`TRAY STATUS` 命令解析，并复用现有串口响应格式。
- `platform/main.c` 在主循环调用 `Tray_Service()`，在急停和清除故障路径调用托盘模块接口。
- `MDK-ARM/VisionClaw_Motion.uvprojx` 加入新源文件和头文件路径，保持现有 Keil 设备、链接脚本和输出目录。

## 命令接口

```text
TRAY STOP
TRAY CW <speed> [duration_ms]
TRAY CCW <speed> [duration_ms]
TRAY ANGLE <CW|CCW> <angle_deg> [speed]
TRAY STATUS
```

不提供持续无限运行的默认动作。省略 `duration_ms` 时使用配置的短时默认值，避免串口异常时托盘持续旋转。`TRAY ANGLE` 由角度和速度换算动作时长，并在完成后回中位。非法速度、角度、时长、忙状态和急停状态返回明确错误码。

## 故障与并发

- 所有状态更新在关中断临界区完成，`Tray_Service()` 只在主循环修改 PWM 和计时状态。
- `TRAY STOP` 清除当前动作并立即输出停止脉宽。
- `ESTOP` 将托盘输出设为停止并锁存 `estop`，不接受新动作。
- `CLEAR` 仅在物理急停释放后清除锁存。
- `TRAY STATUS` 返回运行状态、方向、速度、当前脉宽、剩余时间和开环标志。

## 验证

1. 用现有 `build-keil.ps1` 构建，确保 0 错误、0 警告。
2. 上电确认 PC7 输出 1500us 停止脉宽，舵机不转。
3. 低速短时分别执行 `TRAY CW 20 500` 和 `TRAY CCW 20 500`，确认方向。
4. 执行 `TRAY ANGLE CW 90 20`，根据实际转角调整 `TRAY_MS_PER_DEG`。
5. 在动作期间执行 `TRAY STOP`、`ESTOP`、`CLEAR`，确认输出停止和锁存逻辑。

