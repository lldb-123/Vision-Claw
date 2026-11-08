# 运动控制集成进度（2026-11-07）

工程位置：D:/Users/linjiangwen/Documents/ChatGPT/工创赛。
本地工程与 GitHub main 不同：本地另有 stm32_actuators、stm32_sensors、host_protocol 模块。本次在原本地工程继续，未覆盖它们，没有提交或推送。

## 构建

在本目录执行 `./platform/build.ps1`（PowerShell 7）。复用 D:/EmbeddedDev 的 CubeIDE ARM GCC、Task1_CubeMX_Fixed 的 HAL/CMSIS 公共文件；F407 专用头文件放 platform/device，来自 STMicroelectronics/cmsis-device-f4 官方仓库。依赖目前是本机 D 盘绝对路径，换电脑需要配置。

输出 build/motion.elf、motion.hex、motion.map、build.log。编译器临时目录 D:/EmbeddedDev/motion-build-tmp，未下载安装软件到 C 盘。第三方库不复制进仓库。

## 本次实际实现

- F407VE 启动向量、512KB Flash /128KB 主 SRAM 链接布局、HAL main、中断和 SysTick。
- HSI 经 PLL 得到 84MHz，硬件 FPU，TIM6 50kHz（20us 周期）。
- STEP 拉高后保持至少一个中断周期，下一次中断拉低，避免原来的连续高低写入。原 5us 配置向上量化为 20us，必须实测中断抖动。
- 定位使用加减速，拒绝忙时覆盖目标；检查轴编号、非有限速度、位置加法溢出。
- 负限位回零：已压住先退出、寻零、退离、低速二次触发；30秒超时报故障；回零期间碰到正限位也报故障。
- STOP 减速停止定位，回零时 STOP 中止回零；ESTOP 立即停止脉冲并取消位置可信标记；CLEAR 仅在急停输入释放后清故障。
- 提供受临界区保护的轴状态快照；未回零仍允许脉冲单位手动调试，不应据此执行整机绝对坐标任务。

## 调试入口和临时接线

115200 8N1，USART2 TX=PD5、RX=PD6（避开 PA2/PA3）。X STEP=PA0 DIR=PA1 EN=PA4；Y STEP=PA2 DIR=PA3，Y EN 尚未定义。
PB0/PB1=X负/正限位，PB2/PB3=Y负/正限位，PB4=急停；默认上拉、低有效。示例电平与断线检测能力必须按实际开关接线确认。
上电 X EN 为高，首次运动前显式 `ENABLE X`。急停命令会拉高 X EN；外部急停输入首先由运动核心停止脉冲，保持力/使能释放策略待机构确认。

命令逐行发送：STATUS、ENABLE X、MOVE X 200 200、GOTO X 0 200、HOME X、STOP X、ESTOP、CLEAR。HOME 总是向负限位寻零。ACK 仅表示命令接收，执行结果通过 STATUS 查询；本入口没有任务编号、DONE、重试去重，不是最终上位机协议。

## 验证证据及剩余工作

已实际使用 ARM GCC 对 F407 编译、链接并生成 HEX，日志在 build/build.log。存在 ST HAL 未使用参数和 nosys 系统调用占位警告。编译通过不代表时序、机械或协议实物验证。本次没有烧录、启动硬件，也没有测量脉冲。

下阶段：核对接线和 Y EN → 台架测量 STEP/DIR 与低速定长移动 → 验证限位和回零 → 接舵机 → 正式任务编号/ACK/DONE/去重接口。

尚未实现：开关消抖与回零退离固定距离、回零最大步数独立限额、软件行程、双轴直线插补、正式串口中断/DMA接收、断线恢复、传感器反馈及组合分拣。当前 UART 采用轮询，适合人工调试，不适合高速连续报文。舵机和光电模块保留但没有加入此最小固件。

不能直接连接机构高速运行；先用上述台架验证步骤，确认实际细分和每毫米脉冲数。

## Keil 集成（2026-11-07，同一对话续记）

新增 MDK-ARM/VisionClaw_Motion.uvprojx，目标 STM32F407VETx、ARM Compiler 6.24、硬件单精度 FPU、512KB Flash、128KB 主 SRAM。采用 ST 官方 ARM 汇编启动文件，4KB 栈、2KB 堆；独立 scatter 文件。GNU startup.c 和 GNU 链接脚本不加入 Keil 构建。

实际执行 MDK-ARM/build-keil.ps1，编译链接完成：0 Error(s), 0 Warning(s)。Code=12972、RO-data=716、RW-data=20、ZI-data=4340。生成 Objects/VisionClaw_Motion.axf 和 VisionClaw_Motion.hex，日志为 MDK-ARM/keil-build.log。没有烧录和实物测试。

推荐双击 MDK-ARM/open-keil.cmd 打开项目；启动脚本设置 D 盘 Pack、许可证缓存和临时目录，避免使用 C 盘构建缓存。Keil 的用户界面个人设置仍由软件自身管理，不能保证应用本身完全不写 C 盘。

项目只引用当前阶段需要的 main、motion_control、启动及 HAL 文件，舵机和传感器模块尚未接入。HAL/CMSIS 公共文件依赖 D:/EmbeddedDev/STM32_Workspace/Task1_CubeMX_Fixed；不是可直接搬到其他电脑的独立依赖包。

## 启动入口修复（同一对话续记）

用户反馈双击入口未打开。检查时 Keil 仅显示旧 FreeRTOS 工程。本次将 open-keil.cmd 写为 CRLF，并改用 D:/EmbeddedDev/VisionClawMotion 英文目录入口，该路径是指向原 D 盘项目的 Junction，不复制项目。已通过修复后的脚本启动，并在 Keil 窗口确认标题为 D:/EmbeddedDev/VisionClawMotion/MDK-ARM/VisionClaw_Motion.uvprojx。原旧工程窗口保留。

## ST-Link 默认配置修复

用户截图为 No ULINK2/ME Device found。原因是此前缺少工程 uvoptx，Keil 使用了 ULINK 默认调试器。新增 VisionClaw_Motion.uvoptx，调试器设 ST-LINK Debugger，SWD 100kHz，F407VE 512KB Flash 算法，84MHz。下载器继续使用同一 ST-Link 驱动。调试会话禁用自动加载代码和自动运行到 main，避免仅进入调试就烧录或执行。本次只改设置，未连接、下载或启动硬件。已打开的 Keil 需手动更改 Debug 设置或重新加载配置，磁盘配置不会自动覆盖当前内存设置。

## XYZ 集成（同一对话续记）

用户要求完成 XYZ 工程。沿用 X/Y 步进、Z=MG90S 的硬件记录，新增 PA5=Y EN、PA6=TIM3_CH1 Z PWM。整合 stm32_actuators 到 Keil 和 GNU 构建，新增 ENABLE Y/Z、SERVO Z us duration_ms、STOP Z 和 STATUS Z，三轴共享急停锁存及 CLEAR。Z 上电 PWM 关闭、使能后默认1500us；范围1000~2000us；busy 表示输出过程，不是实物到位。Z 支持平滑脉宽变化、忙状态拒绝、限幅及保持停止。

Keil 实际编译链接：0 Error(s), 0 Warning(s)，Code=14944 RO-data=832 RW-data=20 ZI-data=4428。GNU 同样构建成功。尝试准备软件仿真依赖时发现本机 Python 没有 pip，未执行行为仿真，不能把编译结果当成功能测试。未烧录或启动电机。说明和接线见 XYZ运动控制使用说明.md。

本次新增文件和产物位于 D 盘。现有 Keil 工程名称不变，需重新打开工程加载新增源文件。当前实现支持三个执行机构独立运动，不含三轴直线插补、机械避障、整机 SORT 和位置闭环。
