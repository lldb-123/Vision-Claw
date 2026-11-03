# 单电机持续旋转

目标：STM32F407VET6 驱动一个 A4988，按开发板 RESET 后等待约 1 秒，从 50Hz 逐渐加速到 200Hz，然后保持一个方向持续旋转。停止时断开电机电池。无需安装完整 IDE。

本程序持续输出，不控制电机电流；电流由 A4988 自身限流设置决定。上一版短时程序已在实物上转动；本版已下载并校验，持续旋转的实物效果待观察。

## 首次克隆与工具准备

源码、已生成的 HEX/BIN 和构建脚本已入库；原电脑 `.venv`、第三方 OpenOCD/驱动包、日志和原 Flash 备份没有上传。只下载当前 HEX 不需要安装 Python 构建依赖。

需要重新构建或模拟检查时，在本目录运行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe build_firmware.py
.\.venv\Scripts\python.exe check_firmware.py
```

下载需要准备 [xPack OpenOCD 0.12.0-7](https://github.com/xpack-dev-tools/openocd-xpack/releases/tag/v0.12.0-7)。将 Windows 包按原结构解压，使本目录存在：

```text
tools/xpack-openocd-0.12.0-7/bin/openocd.exe
tools/xpack-openocd-0.12.0-7/openocd/scripts/target/stm32f4x.cfg
```

也可使用已安装的 OpenOCD，从命令行指定路径：

```powershell
.\flash_motor.ps1 -OpenOcdPath 'D:\OpenOCD\bin\openocd.exe' -OpenOcdScripts 'D:\OpenOCD\share\openocd\scripts'
```

`flash_motor.ps1` 也会查找 PATH 上的 `openocd`，并尝试工具根目录下 `openocd/scripts` 或 `share/openocd/scripts`。参数和下载协议沿用已成功的 100kHz 原生 SWD 配置。

若 Windows 尚无 ST-Link 驱动，从 [ST 官方 STSW-LINK009](https://www.st.com/en/development-tools/stsw-link009.html) 获取。将解压内容放到 `tools/stlink_driver/`，保留 INF、CAT 和 `amd64/`、`x86/` 等原目录关系，再运行 `1_安装STLink驱动.cmd`。本机驱动已经可用时跳过安装。

## 接线

沿用此前已试转的接线：**A4988 EN→STM32 PA4，不能同时连 GND。**

| A4988 | STM32 或其他连接 |
| --- | --- |
| STEP | PA0 |
| DIR | PA1 |
| EN | **PA4** |
| VDD | STM32 3V3 |
| 逻辑 GND | STM32 GND |
| RESET、SLEEP | 3V3 |
| MS1、MS2、MS3 | GND，使用整步模式 |
| 1A、1B | 电机同一组线圈 |
| 2A、2B | 电机另一组线圈 |
| VMOT | 匹配电机电源的正极，经开关线 |
| 电源 GND | 电源负极，与 STM32 共地 |

沿用前面要求的驱动电源电容。6S 电池不能接 STM32 的 5V/3V3。变更接线时断开电池和 USB。

STM32 用自身合适的 USB 供电口供电。ST-Link 的 SWDIO→PA13/SWDIO、SWCLK→PA14/SWCLK、GND→GND；下载器的输出电源不与 USB 重复连接。若探针标有独立 VTref 输入，连接目标板 3V3 作为参考。

## 使用顺序

1. **电机电池保持断开。** 接好 STM32 USB 供电和 ST-Link。
2. 双击 `1_安装STLink驱动.cmd`。Windows 安装 USB 驱动需要管理员权限，会弹系统提示。若驱动已正常可跳过。
3. 双击 `2_下载试转程序（先断开电池）.cmd`。成功后 STM32 保持暂停，EN 为高电平，等待按复位键。
4. 确认 EN 接 PA4，电机空载或机构有足够运动余量。接通电机电源。
5. 按一次开发板 RESET：等待约 1 秒起转，约 2 秒逐渐加速，然后持续旋转。
6. 结束时断开电机电池。RESET 会重新启动旋转，不是停止键。STM32 重新上电也会启动旋转。

稳定速度为每秒 200 个 STEP 脉冲，HIGH 1ms、LOW 4ms。对于步距角 1.8°、整步模式的电机，理论约每分钟 60 转。实际转速取决于步距角、细分设置及有无丢步。本程序不做回零、限位或位置控制。

## 文件

- `motor_test.hex` / `motor_test.bin`：已生成的固件，Flash 地址 0x08000000。
- `motor_test.s`：完整汇编源代码，使用内部 HSI 16MHz，不依赖外部晶振。
- `build_firmware.py`：重新生成固件。
- `check_firmware.py` / `verification.json`：CPU 仿真检查，验证持续发脉冲、从 50Hz 加速到 200Hz、脉冲高电平 1ms、固定方向及保留 SWD 引脚。不是实物时序或电机测试。
- `requirements-build.txt`：本版固件构建和模拟检查使用的四项 Python 依赖版本。
- `original_sector0.bin`：首次下载时自动备份的原 Flash 首扇区，按电脑本地保存，不入库。原实验目录中的现有备份没有随迁移复制；在仓库目录首次下载时会备份当时目标板的首扇区，不能把它误认成原厂或更早的固件。
- `logs/`：驱动安装与下载日志。

## 工具来源

- [ST 官方 ST-Link 驱动说明](https://www.st.com/en/development-tools/stsw-link009.html)。仓库不分发驱动包，安装脚本使用 Windows pnputil 并检查 ST 的有效签名。原电脑当时使用的驱动获取过程见历史对话记录。
- [xPack OpenOCD 0.12.0-7](https://github.com/xpack-dev-tools/openocd-xpack/releases/tag/v0.12.0-7)，下载包已对照项目发布的 SHA256 校验。
- STM32 寄存器依据 ST RM0090 和 [STM32F405/407 数据手册](https://www.st.com/resource/en/datasheet/stm32f407ve.pdf)。

## 2026-11-03 实际进度

Windows 驱动可用，开发板重新供电后 SWD 已连接成功。上一版短时程序成功烧录，用户确认电机沿同一方向小幅旋转。本版已改为持续旋转，烧录日志显示 Verified OK。下载结束后 CPU 暂停、EN 为高电平，按开发板 RESET 开始旋转。

下载脚本使用原生 SWD，并在连接和写入期间保持 100kHz。原程序首扇区备份保留在原桌面实验目录的 `original_sector0.bin`。本次迁移只整理文件、改进工具路径配置并做离线验证，没有再次烧录或启动电机。
