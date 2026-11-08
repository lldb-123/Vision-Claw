# Orange Pi 5 Plus 初始化与规范使用手册

> 项目：Vision-Claw 工创赛智能分拣。整理日期：2026-11-08。维护分支：`codex/orangepi-bringup`。
>
> 本文是针对当前实物状态编写的设置清单和操作指南。**写进文档不代表已经在板上执行或验收。** 当前证据见[首次上电汇总](../experiments/orangepi-5-plus/2026-11-08-first-boot.md)和[005 对话记录](../ai-dialogue/2026-11-07-005-orangepi-no-keyboard-network.md)。

## 目录

- [1. 当前状态与执行原则](#s01)
- [2. 总清单与执行顺序](#s02)
- [3. 供电、散热、存储与实物检查](#s03)
- [4. 确认系统身份与镜像来源](#s04)
- [5. 网线直连、Windows 共享网络与 DNS](#s05)
- [6. 校准时间、时区与 HTTPS](#s06)
- [7. 软件源、更新与基础工具](#s07)
- [8. 用户、SSH、公钥与远程维护](#s08)
- [9. 中文、字体、输入法与桌面](#s09)
- [10. 目录、Git、配置与数据规范](#s10)
- [11. Python 环境与现有上位机](#s11)
- [12. 摄像头、OpenCV 与图像采集](#s12)
- [13. STM32 串口、权限与协议](#s13)
- [14. YOLO 训练、转换与板端运行环境](#s14)
- [15. RK3588 NPU 与 RKNN 检查](#s15)
- [16. 性能、电源管理与存储寿命](#s16)
- [17. 程序配置、日志与开机服务](#s17)
- [18. 安全、备份、恢复与离线使用](#s18)
- [19. 分阶段验收与三条主线合并](#s19)
- [20. 日常使用与故障定位](#s20)
- [21. 环境记录模板与资料入口](#s21)

<a id="s01"></a>
## 1. 当前状态与执行原则

### 1.1 已知状态：后续不要从头猜测

| 项目 | 当前事实 | 证据或限制 |
| --- | --- | --- |
| 开发板 | Orange Pi **5 Plus**，RK3588 | 不能套用 Orange Pi 5、5B、5 Max 或树莓派的镜像/引脚说明 |
| 内存 | 尚未读取实际容量 | 不从下载页标题、采购设想推定容量 |
| 启动盘 | 64 GB TF 卡 | 用户反馈后来 Etcher 验证成功；实际分区容量待查 |
| 系统 | 已进入图形桌面，用户称 Ubuntu | 照片有 Applications 顶栏；发行版、版本、桌面类型、内核仍需命令确认 |
| 输入设备 | 板端无键盘、鼠标，有显示器 | 已能 SSH，初始化可主要通过电脑完成 |
| 登录 | `orangepi@192.168.50.2` 已成功 | 密码由用户保管，不写入仓库 |
| 电脑有线地址 | `192.168.50.1/24` | Windows；无线网络提供上网出口 |
| 板端地址 | `192.168.50.2/24` | 当前接口 `enP3p49s0` |
| 板端连接配置 | `my_Lenovo_computer` | NetworkManager 管理 |
| 电脑共享 | WinNAT `OrangePi` 已创建，Active=True | 以太网 IPv4 转发已开启，不需重复创建 |
| 网关 | 已保存 `192.168.50.1` | `nmcli device reapply` 成功；尚未通过重启验证 |
| DNS | 已保存 `223.5.5.5 1.1.1.1` | 电脑 VPN 可能拦截 DNS，返回 `198.18.0.37` 等虚拟地址 |
| 外网验证 | `ping 1.1.1.1`、域名 ping 成功 | 不等于 HTTPS、apt、Git、pip 全部可用 |
| 时间 | 最近输出仍为 2026-08-31 | 与实际日期不符；已执行启用 NTP，但没有同步成功证据 |
| HTTPS | 最近 `curl` 报证书尚未生效 | 首要处理时间，之后再次验证证书及网络 |
| 中文 | 用户已提出需求 | 尚未安装/配置或验证 |
| Python、相机、串口、NPU | 尚无本板验收记录 | 不把电脑模拟成功记成板端实物成功 |
| 供电 | 用户使用标称 5V/5A 的 UBEC | 接线、极性、带载电压、温升仍需实测 |

### 1.2 命令在哪里执行

- **板端 Bash / SSH**：先在 Windows 输入 `ssh orangepi@192.168.50.2`，登录后执行标为 `bash` 的命令。不要在 Windows PowerShell 里直接粘贴 Linux 命令。
- **Windows PowerShell**：标为 `powershell`。修改 NAT/转发通常需要管理员窗口，普通 SSH、Git、文件传输不需要。
- **训练/转换电脑**：对应章节另行说明，不能一律复制到香橙派。
- `REPLACE_...`、`<实际值>` 都是占位符，必须替换；本文不是可整篇执行的安装脚本。
- 现有接口名、用户名和 IP 适用于目前这台板。换网口、重刷镜像或换电脑后先查询，不能假定名称仍相同。

### 1.3 操作约束

1. 先检查，再改一项，再验证；保留当前 SSH 会话，涉及网络/SSH 的变更用第二个窗口验证。
2. 先解决时钟和 HTTPS，再安装语言包、Python 包、Git 依赖。不要用跳过证书验证掩盖问题。
3. 先建立能恢复的系统基线，再更新厂商内核、NPU Runtime、设备树或启动配置。
4. 摄像头采集、串口读写和运动启动是不同阶段。初始化阶段不发送电机动作，不开启真实运动自启动。
5. 三条分支按用户计划，等初始化整理好后、正式 YOLO 开发和模型部署前再合并。本文不执行合并。

<a id="s02"></a>
## 2. 总清单与执行顺序

标记含义：**必做**是基础使用必需；**按需**取决于实际硬件/使用方式；**后续**在进入对应开发阶段时执行。复选框表示验收，不表示“命令已经提供”。

| 阶段 | 要做的事情 | 优先级 | 验收依据 |
| --- | --- | --- | --- |
| A | 核实供电、散热、固定、TF 卡和启动稳定性 | 必做 | 上电稳定，无异常掉电/存储错误 |
| A | 记录板型、RAM、发行版、内核、架构、镜像来源 | 必做 | 真实命令输出及镜像文件信息 |
| A | 核实直连 IP、默认网关、NAT、DNS | 必做 | SSH、公网 IP、域名、HTTPS 分层通过 |
| A | 修复时间与时区，确认冷启动后的校时 | **当前最优先** | 时间正确，NTP 同步或有可靠离线校时方案 |
| A | 核查 apt 源，安装基础维护工具 | 必做 | `apt update` 无关键错误 |
| A | 修改出厂密码、配置 SSH 密钥和恢复入口 | 必做 | 新会话登录成功，主机指纹可核对 |
| A | 中文 locale、字体、桌面翻译 | 用户已要求 | 新会话中文显示正常；桌面另行确认 |
| A | 重启恢复测试、备份第一份系统基线 | 必做 | 关机再上电能恢复 SSH/路由/时间 |
| B | 建立代码、数据、模型、日志目录 | 必做 | 不混入虚拟环境、凭据和实物标定 |
| B | 建立板端 Python venv，验证已有上位机模拟 | 必做 | 依赖检查及模拟输出通过 |
| B | USB 摄像头识别、固定设备名、采集参数 | 按实际采购 | 图像可读，颜色/曝光/帧率记录完整 |
| B | STM32 串口设备识别与用户权限 | 接入前必做 | 非 root 能访问约定设备；不触发运动 |
| B | 明确正式通信协议与安全停机行为 | 联调前必做 | 双方确认，不能混用演示协议/旧固件 |
| B | NPU 驱动与 Runtime 盘点、版本选型 | YOLO 前必做 | 驱动/Runtime/wheel/模型格式兼容有依据 |
| C | 训练电脑 Python/PyTorch/YOLO 环境 | 后续 | 实际训练设备、包版本和数据划分记录 |
| C | ONNX/RKNN 转换、INT8 校准环境 | 后续 | 固定版本、输入输出和转换日志 |
| C | 板端 RKNN 官方样例与项目模型推理 | 后续 | 本板输出正确，性能与精度有数据 |
| C | 相机到 STM32 的整机联调 | 后续 | 视觉坐标、运动协议、停止与反馈实测 |
| D | 稳定运行服务、离线启动、异常恢复 | 正式部署前 | 不依赖 SSH 窗口，不因重启意外运动 |
| D | 发布版本、整卡备份、恢复演练 | 正式部署前 | 能从备份重建并复验 |

**现在建议先做：系统身份 → 校时 → HTTPS/apt → 中文 → SSH 维护 → 重启验收。** 不必为了“环境齐全”立刻安装 Docker、ROS、CUDA、全部深度学习框架或完整桌面远控套件。

<a id="s03"></a>
## 3. 供电、散热、存储与实物检查

### 3.1 电源和接线

- 核对是 5 Plus 的电源接口和引脚图。厂商文档说明使用固定 5V/4A 或 5V/5A 供电，也可通过指定 40pin 的 5V/GND 供电；电源需要能持续提供所需电流，接头和线材同样要匹配。板子不能靠 PD 协商自动把任意高电压变为 5V。[Orange Pi 5 Plus 官方手册](https://orangepi.net/wp-content/uploads/2023/07/OrangePi_5_Plus_RK3588_user-manual_v1.5.1.pdf)
- 现有 UBEC 标称 5V/5A 只是铭牌，需测输出极性、空载与板端带载电压、接线压降、启动和外设接入时的稳定性。无法确定测量方法时，先使用匹配的可靠电源和线材。
- 明确电池、降压模块和板端各段额定电压；禁止把电机电源电压直接送到板端 5V 或 GPIO。
- 大电流电源线应可靠固定，不把细杜邦线、松动面包板接点当作整机长期供电路径。
- 不同时接两路可能互相回灌的板端供电；接 USB 串口/STM32 时核实是否会经 VCC 回灌。
- 电机/舵机的瞬态电流应由适当的电源支路承担。共地、滤波、保险和急停按电气设计确定；不要让电机大电流经板卡地线回流。
- 记录散热器、风扇电压/接口、线序和安装。不要把任意风扇直接接到信号引脚。
- GPIO/UART 等逻辑接口的电平按 5 Plus 文档核对；TTL UART 不是 RS-232，不能直接连 RS-232 电压。

验收时先保持电机不动作，只接当前必要外设。然后按“板卡空载 → 相机 → 运算负载 → 整机电气联调”递进，记录是否重启、USB 掉线、供电线温升或存储报错。

### 3.2 存储与分区

板端只读检查：

```bash
lsblk -o NAME,SIZE,FSTYPE,MOUNTPOINTS,MODEL
findmnt /
df -hT /
df -ih /
free -h
swapon --show
sudo journalctl -b -k --no-pager | grep -Ei 'mmc|I/O error|ext4.*error|read-only' | tail -n 50
```

- 64GB 厂商容量与 Linux 显示的 GiB 不相等，不能把正常单位差异误判为丢容量。
- 如果根分区只占几 GB，先核对分区布局和镜像扩容机制；不要对猜测的 `/dev/mmcblk0` 直接执行分区/格式化命令。
- 留足可用空间，建议日常至少留约 15%～20% 余量作为本项目维护目标；同时查看 inode，避免大量小日志耗尽。
- 优先把大数据集、训练输出和长期录像放电脑或适当的 SSD；TF 卡不承担当作训练缓存盘的持续高写入。
- NVMe/eMMC 迁移是可选事项。迁移会涉及启动顺序、固件和分区，需独立备份与验证，不是首次初始化必选项。
- TF 卡健康不能仅凭 `smartctl` 判定；很多读卡路径不提供 SMART。关注 I/O 错误、文件系统只读、异常重启及备份可恢复性。

<a id="s04"></a>
## 4. 确认系统身份与镜像来源

### 4.1 先保存真实环境信息

板端执行：

```bash
cat /etc/os-release
uname -a
uname -m
dpkg --print-architecture
tr -d '\0' < /proc/device-tree/model
printf '\n'
hostnamectl
lscpu
free -h
python3 --version
nmcli --version
systemctl status display-manager --no-pager
ls /usr/share/xsessions/ /usr/share/wayland-sessions/ 2>/dev/null
```

预期 64 位板端用户空间通常显示 `aarch64` / `arm64`，不能给它安装 Windows、x86_64 或 armhf 的二进制包。若实际结果不同，按实测环境重新选软件包。

SSH 中 `echo "$XDG_CURRENT_DESKTOP"` 为空并不能证明没有桌面；SSH 会话不等于显示器上的桌面会话。通过 display-manager、会话文件及必要时桌面本身确认 XFCE/GNOME 等。

### 4.2 镜像来源档案

用户提供的[镜像下载页面](https://www.fujianleji.com/orange/Orange_Pi_5_Plus_download.html?utm_source=chatgpt.com)需要保留。它是入口页面，**不是已经核实的某个 `.img` 文件直链**。当前不要为了补档重新烧录。

后续补齐：

| 字段 | 要记录什么 |
| --- | --- |
| 来源 | 页面 URL、实际下载入口及获取日期 |
| 原始文件 | 完整文件名、压缩格式、大小 |
| 校验 | 官方提供的校验值（若有）、本地 SHA256；区分压缩包和解压后的镜像 |
| 镜像标识 | 适用板型、发行版、桌面/Server、发布版本和内核 |
| 烧录证据 | Etcher 版本、目标 TF 卡、Flash/验证结果 |
| 实际启动信息 | `/etc/os-release`、`uname -r`、设备树 model |
| 本地保存位置 | 明确是原电脑路径；不声称镜像已上传到仓库 |

Windows 本地校验示例，替换路径后执行：

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath 'D:\实际目录\实际镜像.img.xz'
```

此前曾核对过 Joshua Riek Ubuntu 镜像，但不能据此认定现在运行的就是它。若缺少最终文件，只记录“最终文件待核实”，不要编造版本或散列值。

<a id="s05"></a>
## 5. 网线直连、Windows 共享网络与 DNS

### 5.1 当前拓扑

```text
互联网 / 校园网络
       │
Windows 笔记本：WLAN + 现有 VPN
       │ WinNAT OrangePi，192.168.50.0/24
       │ 以太网 192.168.50.1/24
       └──────── 网线 ──────── Orange Pi 5 Plus
                              enP3p49s0：192.168.50.2/24
                              默认网关：192.168.50.1
```

SSH 只需两台机器互通；板子访问互联网还依赖电脑转发/NAT、电脑上网出口、DNS 和可能存在的 VPN 策略。电脑关机、睡眠、WLAN 断开后，板端路由正确也可能无法上网。

目前电脑有线口不需要再把自己 `192.168.50.1` 设置成默认网关。上网出口由电脑的 WLAN/VPN 路由决定。

### 5.2 只读检查

Windows PowerShell：

```powershell
Get-NetAdapter
Get-NetIPAddress -InterfaceAlias '以太网' -AddressFamily IPv4
Get-NetIPInterface -InterfaceAlias '以太网' -AddressFamily IPv4
Get-NetNat
Test-NetConnection 192.168.50.2 -Port 22
```

板端：

```bash
ip -br link
ip -4 addr show enP3p49s0
ip -4 route
nmcli device status
nmcli -g GENERAL.CONNECTION device show enP3p49s0
nmcli -g ipv4.method,ipv4.addresses,ipv4.gateway,ipv4.dns,connection.autoconnect connection show "my_Lenovo_computer"
```

要看到 `.2/24`、默认路由经 `.1`、连接配置启用自动连接。两个 RJ45 网口是不同接口；换口后要重新查看，不能继续硬套旧接口名。不要把两个网口同时随意配置成同一子网。

### 5.3 用户需要的手动恢复命令

仅当默认路由缺失时，在板端输入：

```bash
sudo ip route replace default via 192.168.50.1 dev enP3p49s0
```

这是临时修改，重启或连接被重新应用后可能失效。它不设置 Windows NAT，不修 DNS，也不修时钟。此前已保存持久网关，所以正常重启后不应需要每次重复。

### 5.4 持久配置：先确认现状，再按缺失项补齐

这几项此前已经执行，不需要无故反复修改：

```bash
sudo nmcli connection modify "my_Lenovo_computer" ipv4.gateway 192.168.50.1 ipv4.never-default no
sudo nmcli connection modify "my_Lenovo_computer" ipv4.dns "223.5.5.5 1.1.1.1"
sudo nmcli device reapply enP3p49s0
```

若检查发现自动连接关闭，可单独设置：

```bash
sudo nmcli connection modify "my_Lenovo_computer" connection.autoconnect yes
```

目前 `.2/24` 已有效，不需要为补默认路由而改 IP 或断开网卡。`device reapply` 是否支持全部变化取决于版本和属性；若提示不支持，先准备回退入口，再安排重新激活连接。不要在唯一 SSH 会话中直接执行 `nmcli connection down`。[NetworkManager 官方 nmcli 文档](https://networkmanager.dev/docs/api/latest/nmcli.html)

修改前可将连接配置备份到板端受限目录；文件可能含其他网络凭据，不上传：

```bash
sudo install -d -m 700 /root/vision-claw-backup
sudo cp -a /etc/NetworkManager/system-connections "/root/vision-claw-backup/system-connections-$(date +%Y%m%d-%H%M%S)"
```

大改 IP/网口前，应准备可用的本地键鼠或经验证的串口控制台，或按本机 `nmcli device checkpoint --help` 支持的方式设置自动回滚。没有可靠恢复入口时，先维持目前可用的 SSH 地址。

### 5.5 Windows NAT 的维护

现有 NAT 已创建成功。只有电脑配置丢失或换电脑，才重新核查并在管理员 PowerShell 中配置：

```powershell
Get-NetNat
Set-NetIPInterface -InterfaceAlias '以太网' -AddressFamily IPv4 -Forwarding Enabled
# 仅在确认没有现有冲突 NAT、且 OrangePi 对象不存在时执行：
# New-NetNat -Name OrangePi -InternalIPInterfaceAddressPrefix 192.168.50.0/24
```

不要反复执行 `New-NetNat`，不要为香橙派删除 WSL/Docker/虚拟机使用的 NAT。出现冲突时先列出已有对象和地址范围。NAT 命令参数见 [Microsoft New-NetNat](https://learn.microsoft.com/en-us/powershell/module/netnat/new-netnat)。

当前方案不需要再同时开启 Windows ICS。ICS 可能改变有线口地址，与现有 `192.168.50.0/24` 方案冲突。也不需要把两块网卡桥接，更不应关闭整个防火墙来尝试联网。

### 5.6 分层验证，保留 VPN

板端依次测试：

```bash
ping -c 2 192.168.50.1
ping -c 2 1.1.1.1
getent ahostsv4 example.com
date -Is
curl -I --connect-timeout 5 --max-time 15 https://example.com
curl -I --connect-timeout 5 --max-time 15 https://github.com
```

- 第一层失败：看网线、接口、两端静态 IP、防火墙；部分主机不回应 ICMP，结合 SSH/TCP 测试判断。
- 第一层通而公网不可达：看默认路由、Windows NAT、WLAN、VPN 对来自局域网流量的处理。
- 公网 IP 通但域名失败：查 DNS。`resolvectl status` / `nmcli device show` 有助于确认实际 DNS；系统没有 `resolvectl` 时继续查 `ls -l /etc/resolv.conf` 与文件内容。
- 当前 `198.18.0.37` 与电脑 VPN 的虚拟 DNS 行为一致。出现该地址本身不等于失败；必须看 TCP/HTTPS 是否真的能用。更换公网 DNS 不一定绕过电脑的拦截。
- 用户不能断开 VPN：保留它，在客户端支持范围内检查局域网访问、TUN/路由和 DNS 转发设置。不要臆测 VPN 软件选项名或端口。
- 如果必须用显式代理，先确认电脑客户端的监听地址/端口、局域网访问及防火墙范围，再为需要的进程配置。板端 `127.0.0.1` 指板子自己，不能直接照抄电脑代理地址。
- 不把含账号口令的代理 URL 写入 Git、命令示例或日志。设置代理后注意 `NO_PROXY` 包含 `localhost,127.0.0.1,192.168.50.1,192.168.50.2`，并按工具支持方式填写。

验收要分别记录 Windows 重启、板端重启、VPN 重连后的结果。以后接路由器上网时另建/调整对应网络配置，不在别的子网继续固定使用 `.1` 网关。

<a id="s06"></a>
## 6. 校准时间、时区与 HTTPS

### 6.1 为什么当前要先处理

已见到的 `certificate is not yet valid` 与板端日期落后相符。先校时再重测；校时后仍有证书问题，再检查 CA、代理证书链或目标服务。不能直接认定一切 TLS 错误都只由时间导致。

禁止把 `curl -k`、关闭 Git SSL 校验、pip `--trusted-host` 或关闭 apt 时间/签名检查当作长期解决方案。

### 6.2 查看时区和校时服务

板端：

```bash
date -Is
date -u
timedatectl status
systemctl is-active systemd-timesyncd chrony ntp ntpsec
```

某些服务显示 `inactive` 或 `unknown` 正常，重点是识别实际使用哪一个。不要为了“齐全”同时启用多个校时守护进程。不同 Ubuntu/厂商镜像默认服务可能不同。[Ubuntu 时间同步说明](https://ubuntu.com/server/docs/about-time-synchronisation/)

按实际所在地选择一个时区。中国大陆可用：

```bash
sudo timedatectl set-timezone Asia/Shanghai
sudo timedatectl set-ntp true
timedatectl status
```

若采用 `Asia/Singapore` 也为 UTC+8，但应在环境档案中统一记录。改时区只改显示规则，不能把落后两个月的系统时钟修正确。

### 6.3 若实际服务是 systemd-timesyncd

```bash
systemctl status systemd-timesyncd --no-pager
timedatectl timesync-status
sudo journalctl -u systemd-timesyncd -b --no-pager -n 60
```

关注服务运行、所选服务器、网络请求是否超时、`System clock synchronized: yes`。旧版本不支持某个子命令时用状态和日志交叉验证。NTP 通常使用 UDP/123，HTTPS 通不能证明 NTP 通。[Ubuntu timesyncd 配置说明](https://ubuntu.com/server/docs/use-timedatectl-and-timesyncd/)

只有默认服务器确实不可用时，才在 `/etc/systemd/timesyncd.conf.d/` 建独立配置，填写网络中可达、可信的 NTP 地址，然后重启此服务。不要直接复制未经验证的陌生时间服务器列表。

### 6.4 若实际服务是 chrony

```bash
chronyc tracking
chronyc sources -v
sudo journalctl -u chrony -b --no-pager -n 60
```

检查选中的时间源与同步状态。需要立即校正明显偏差时，在没有运动任务、采集和计时任务运行的维护阶段，根据 chrony 配置使用 `sudo chronyc makestep`，随后再次查看状态。来源：[Ubuntu chrony 文档](https://ubuntu.com/server/docs/how-to/networking/chrony-client/)。

### 6.5 NTP 暂时不通：用可信电脑时间临时校准

先确认 Windows 的日期、时区和自动时间同步正确。然后在 **Windows PowerShell** 执行，下列命令从当前电脑生成 Unix 时间，不会把某一天硬编码进脚本：

```powershell
Get-Date -Format o
$opiUnixTime = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
ssh -t orangepi@192.168.50.2 "sudo timedatectl set-ntp false && sudo date -u -s '@$opiUnixTime' && sudo timedatectl set-ntp true"
```

这是维护时的应急校时，可能有输入密码所耗的数秒偏差；它不能证明 NTP 已恢复。命令中任何一步失败，先看输出，不要假定后续已执行。若系统根本没有可用 NTP 服务，先手动校时、修复包下载，再根据实际发行版安装一个合适的校时服务。

回到板端验证：

```bash
date -Is
timedatectl status
curl -I --connect-timeout 5 --max-time 15 https://example.com
```

HTTP 状态码可能因站点策略不同而异；至少需完成可信 TLS 握手。真正安装依赖前还要验证相应软件源。

### 6.6 断电后的时间保持

- 记录板上是否有可用 RTC、是否接了匹配的后备电池及其极性，按该型号手册处理。
- 可用 `ls -l /dev/rtc*`、`sudo hwclock --show` 查看；设备存在不代表电池有效。
- 不把重启后偶尔看似正确当成断电保持成功。冷启动再核对时间和同步状态。
- 如果有可用 RTC，系统时间校准后才考虑 `sudo hwclock --systohc --utc`；没有确认 RTC 时不盲目写入。
- 正式离线比赛需要可靠时间策略。实时动作超时应在程序中使用单调时钟，避免系统校时改变墙上时间造成计时跳变。

<a id="s07"></a>
## 7. 软件源、更新与基础工具

### 7.1 包管理前置检查

先确认第 4 节的发行版和第 6 节的时间/HTTPS。查看源及锁定包：

```bash
grep -RhsE '^(deb |Types:|URIs:|Suites:|Components:|Signed-By:)' /etc/apt/sources.list /etc/apt/sources.list.d/ 2>/dev/null
apt-mark showhold
sudo apt update
apt list --upgradable
apt-get -s upgrade
```

- Ubuntu 和 Debian 的源不能混用；发行版代号、ARM64 架构、厂商内核源需对应真实系统。
- 不因某个源下载慢就替换成随机镜像；换镜像前备份源配置，保持发行版和签名校验正确。
- 若出现锁，先确认是否有正常更新进程，不能直接删锁文件或杀包管理器。
- 系统用户空间安全更新应维护，但涉及内核、设备树、启动固件、Mesa/RGA/NPU 等时，先看升级清单与兼容性并备份。
- 不在刚能 SSH 时盲目执行 `full-upgrade`、发行版大版本升级或替换主线内核。板级驱动支持可能受影响。
- 不把“保留可用内核”变成永远不打安全补丁；记录暂缓项目、原因和以后复核时间。

### 7.2 分组安装，不必一次装满

**基础维护与项目运行**，在已确认是兼容的 Ubuntu/Debian 后：

```bash
sudo apt install ca-certificates curl wget git openssh-server rsync tmux nano htop unzip zip
sudo apt install python3 python3-venv python3-pip
```

**开发编译工具**，只有缺少 wheel、编译扩展或开发 C/C++ 时才加：

```bash
sudo apt install build-essential cmake pkg-config python3-dev
```

**设备诊断**，接相机/串口时加：

```bash
sudo apt install usbutils v4l-utils
```

**图形界面与字体**，需要当前 Python 桌面原型时：

```bash
sudo apt install python3-tk fonts-noto-cjk
```

`libGL`、GLib、GStreamer 等依赖按具体 OpenCV 构建和报错处理，不硬套不同发行版的同名库包。未使用桌面程序时，不必为了 SSH 安装整套桌面。

### 7.3 软件安装习惯

- 系统包用 apt；项目 Python 包用 venv；NPU SDK 和模型按固定版本目录保存。
- 不改 `/usr/bin/python3` 的软链接，不卸系统 Python，不在系统环境执行 `sudo pip install`。
- 遇到 `externally-managed-environment`，创建 venv；不把 `--break-system-packages` 当标准做法。
- 安装脚本要先读内容与来源；不把不明来源 `curl ... | sudo bash` 作为初始化捷径。
- 若软件源要求新发行版而当前系统太旧，先评估换镜像/迁移，不混装其他代号的软件包凑依赖。
- 每次关键更新后记录改变的包、是否重启、相机/串口/NPU 回归结果。

<a id="s08"></a>
## 8. 用户、SSH、公钥与远程维护

### 8.1 账户和 SSH 基础

继续使用已登录的普通用户 `orangepi` 即可，不必为形式统一立即改用户名或家目录。先确认：

```bash
whoami
id
sudo -v
systemctl status ssh --no-pager
sudo ss -lntp | grep ':22'
```

修改仍在使用的出厂口令：

```bash
passwd
```

口令现场输入，不写进命令参数、聊天记录或仓库。核查镜像是否存在不需要的默认账户、root 远程登录、无密码 sudo 和桌面自动登录；逐项调整，避免先锁死唯一管理员。

### 8.2 配置专用 SSH 密钥

Windows PowerShell，先检查文件是否已存在：

```powershell
Test-Path "$env:USERPROFILE\.ssh\id_ed25519_orangepi"
```

若返回 True，先确认是否已经可用；不要覆盖。若没有该密钥，可生成带口令的专用密钥：

```powershell
ssh-keygen -t ed25519 -f "$env:USERPROFILE\.ssh\id_ed25519_orangepi" -C 'vision-claw-orangepi'
```

只把 **`.pub` 公钥**追加到板端，私钥留在电脑：

```powershell
Get-Content "$env:USERPROFILE\.ssh\id_ed25519_orangepi.pub" | ssh orangepi@192.168.50.2 "umask 077; mkdir -p ~/.ssh; tr -d '\r' >> ~/.ssh/authorized_keys; chmod 700 ~/.ssh; chmod 600 ~/.ssh/authorized_keys"
ssh -o PasswordAuthentication=no -i "$env:USERPROFILE\.ssh\id_ed25519_orangepi" orangepi@192.168.50.2
```

第二条在新会话成功后，才算密钥登录已验证。后续可用电脑的 SSH agent 管理密钥口令。

第一次连接或重刷后，核对主机公钥指纹。板端可查询：

```bash
sudo ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
```

`REMOTE HOST IDENTIFICATION HAS CHANGED` 时先核实是否重刷或 IP 被另一台设备占用，再处理对应 `known_hosts` 条目，不关闭主机身份检查。

### 8.3 可选强化：必须在第二条登录通道验证后做

- 保留原 SSH 会话；备份 `/etc/ssh/sshd_config` 和实际生效的 drop-in 配置。
- 确认镜像支持 `Include` 后，使用独立 `.conf` 配置，避免多处互相覆盖。
- 可考虑 `PermitRootLogin no`；只有公钥与恢复通道可靠后才考虑 `PasswordAuthentication no` 和按需关闭键盘交互认证。
- 不把仅修改某一行视为已生效；先运行 `sudo sshd -t` 检查语法，再用 `sudo sshd -T` 查看最终设置，确认无误才 `sudo systemctl reload ssh`。
- 重新开窗口验证普通用户登录及 sudo；确认后才退出旧窗口。

依据：[Ubuntu OpenSSH 管理说明](https://ubuntu.com/server/docs/how-to/security/openssh-server/)。

### 8.4 电脑端便捷配置和文件传输

可在 Windows 用户的 `.ssh/config` 添加以下条目；已有文件时只追加/编辑对应主机，不覆盖其他配置：

```sshconfig
Host vision-claw-pi
    HostName 192.168.50.2
    User orangepi
    IdentityFile ~/.ssh/id_ed25519_orangepi
    IdentitiesOnly yes
    ServerAliveInterval 30
    ServerAliveCountMax 3
```

之后使用 `ssh vision-claw-pi`。文件传输用 SCP/SFTP；例如：

```powershell
scp '.\实际配置文件.json' vision-claw-pi:/home/orangepi/
```

不要把 Windows `.venv`、绝对路径配置、设备口名 `COM3` 原样复制后当作 Linux 环境。

### 8.5 无键鼠的长期维护方式

- 命令行：SSH + `tmux`。启动 `tmux new -s setup`；按 `Ctrl+B` 再按 `D` 脱离；`tmux attach -t setup` 回到会话。
- 代码编辑：可按需使用电脑编辑器的 SSH 远程功能，先评估板端内存与插件依赖。
- 图形桌面：VNC/RDP 属于可选项。先确认桌面是 X11/Wayland、需要“共享显示器现有会话”还是“新建远程会话”，再选服务器；两种效果不同。
- 图形远控只对可信局域网开放，优先经 SSH 隧道，不把未认证的桌面端口暴露到公网。
- 无显示器启动时的分辨率/EDID 与当前接显示器情况不同，需另测；不要直接套用树莓派配置文件。
- 建议保留一个实际可用的救援办法：临时 USB 键鼠，或按本板手册核对电平/针脚/波特率的串口控制台。没有实测串口前，不能记为“救援通道已完成”。

<a id="s09"></a>
## 9. 中文、字体、输入法与桌面

### 9.1 三个不同目标

1. **字符可显示**：UTF-8 locale 和中文字体。
2. **界面变中文**：翻译包、用户语言和桌面会话配置。
3. **能输入中文**：输入法框架与拼音引擎。

在 Windows SSH 窗口输入中文通常使用 Windows 自己的输入法；只做 SSH 维护时，板端不一定需要安装中文输入法。

### 9.2 Ubuntu 路线：确认 `/etc/os-release` 后选用

先通过时间和 apt 检查，再在板端执行：

```bash
sudo apt install locales language-pack-zh-hans fonts-noto-cjk
sudo locale-gen zh_CN.UTF-8 en_US.UTF-8
sudo update-locale LANG=zh_CN.UTF-8 LANGUAGE=zh_CN:zh LC_ALL
```

最后的 `LC_ALL` 没有赋值，是清除该全局覆盖项；不建议长期设置 `LC_ALL` 压住所有分类。包名参考 [Ubuntu 简体中文语言包](https://packages.ubuntu.com/jammy/language-pack-zh-hans)，实际可用版本由本机发行版的软件源决定。

若确认为 GNOME/相关桌面且需要其翻译，再按包可用性安装 `language-pack-gnome-zh-hans`。XFCE 等桌面的翻译来源与包组合需按实际镜像核实，不应只凭 Applications 菜单判断是 GNOME。

### 9.3 Debian 路线：不要安装 Ubuntu 专属语言包

```bash
sudo apt install locales fonts-noto-cjk
sudo dpkg-reconfigure locales
```

在 SSH 中的文本选择界面启用 `zh_CN.UTF-8 UTF-8`，保留需要的 `en_US.UTF-8 UTF-8`，选择默认 locale。随后可明确设置：

```bash
sudo update-locale LANG=zh_CN.UTF-8 LANGUAGE=zh_CN:zh LC_ALL
```

`update-locale` 修改系统默认 locale，新登录会话才会加载；命令的变量清除语义见 [Debian update-locale 手册](https://manpages.debian.org/bookworm/locales/update-locale.8.en.html)。

### 9.4 验证与桌面仍为英文时的处理

退出 SSH 再登录后检查：

```bash
locale
locale -a | grep -Ei 'zh_CN|en_US'
cat /etc/default/locale
fc-list :lang=zh | head -n 5
printf '中文显示测试：香橙派智能分拣\n'
```

- 桌面需要注销原图形会话再登录，或在完成网络/SSH 检查后重启；仅新开 SSH 不会改变已运行桌面。
- 用户级 `~/.profile`、`~/.pam_environment`、显示管理器/AccountsService 的语言设置可能覆盖系统值，先查明确切来源再改，不盲目往所有文件追加 `LANG`。
- SSH 客户端发送的 locale 也可能覆盖服务器默认值；出现不支持的 locale 时查 `AcceptEnv`/客户端环境，不直接重装系统。
- 字体方框与界面仍为英文是两类问题，分别检查字体和翻译/会话语言。
- 项目目录建议保持 ASCII 名称；桌面提示是否将 Documents 等目录重命名为中文时，考虑已有脚本路径，避免无意改路径。
- 程序读写文件指定 UTF-8；需要稳定英文诊断输出时，对单条命令用 `LC_ALL=C 命令`，不必把全系统切回英文。

### 9.5 输入法：仅在操作板端桌面时按需安装

先查桌面现有 IBus/Fcitx，选择一套，不同时启用多套框架。若本机源提供 Fcitx5 且桌面适用，可选：

```bash
sudo apt install fcitx5 fcitx5-chinese-addons im-config
im-config
```

在用户会话选择 Fcitx5，注销再登录，在输入法配置中添加拼音。X11/Wayland 与不同桌面的环境集成方式不同；先使用发行版提供的配置工具，不盲目全局添加 `GTK_IM_MODULE`、`QT_IM_MODULE` 等变量。

已有 IBus 的桌面也可沿用 IBus 并安装源内对应拼音引擎，不需要为中文强行换框架。远程图形会话和显示器上的本地会话都应分别试输入。

<a id="s10"></a>
## 10. 目录、Git、配置与数据规范

### 10.1 建议目录

这是板端建议布局，不代表这些目录已经存在：

```text
/home/orangepi/vision-claw/
├── src/Vision-Claw/       # Git 源码；分支/commit 可追溯
├── venvs/
│   ├── upper-computer/    # 现有上位机运行环境
│   └── rknn-runtime/      # 后续 NPU 环境，兼容验证前保持独立
├── models/               # .pt/.onnx/.rknn 与发布说明
├── data/                 # 原始图片、评估样本；不默认上传
├── config/               # 本机配置、相机参数、标定
├── logs/                 # 后续正式程序日志
├── reports/              # 环境快照、验收报告、性能记录
├── packages/             # 本平台离线 wheel/安装包
└── backups/              # 临时备份；还要复制到其他物理设备
```

可在板端创建空目录：

```bash
mkdir -p ~/vision-claw/{src,venvs,models,data,config,logs,reports,packages,backups}
```

当前上位机实际仍读取源码下 `configs/default.json`、`configs/calibration.json` 并写源码下 `logs/`。上面外部目录是后续规范，**仅创建目录不会让现有程序自动改路径**；迁移配置需要相应代码改动及测试。

### 10.2 获取仓库与版本管理

如果板上尚无仓库，才执行：

```bash
cd ~/vision-claw/src
git clone --branch codex/orangepi-bringup https://github.com/lldb-123/Vision-Claw.git
cd Vision-Claw
git status --short --branch
git log -1 --oneline
```

已有仓库时先 `git status`、`git branch --show-current`、`git remote -v`，不覆盖工作目录，不默认 `reset --hard`。当前初始化记录在 `codex/orangepi-bringup`，合并后部署的分支/commit 再按届时决定更新。

规范：

- 阅读 `AGENTS.md` 和 `ai-dialogue/README.md`；每次对话更新对应记录。
- 源码改动优先在开发分支完成；板端部署记下 `git rev-parse HEAD`，避免运行中无记录地修改代码。
- 正式运行时不自动 `git pull`。先停止任务、备份本地配置、审查差异，再切换已验证版本。
- 公开仓库只读克隆不需在板上放 GitHub 凭据；确需推送时使用合适权限和独立认证，不把 token 写入 remote URL。
- Git 用户名/邮箱只在需要提交的机器配置为用户自己的身份，不使用示例身份冒充。
- Windows/Linux 脚本分别使用正确路径、解释器和换行；Bash 脚本用 LF，新增脚本注意 Git 执行位。
- 大图片集、模型、镜像与发布包采用明确的仓库外存储/Release/LFS 策略后再上传，不能默认全部 `git add .`。

### 10.3 本地配置和依赖快照

应提交：代码、配置模板、依赖声明、运行文档、去敏后的验证摘要。不要提交：密码/私钥、`.env`、虚拟环境、缓存、原始运行日志、机器标定、系统镜像、第三方安装包和 `original_sector0.bin`。

现有 `.gitignore` 已覆盖部分项目，但不能假定任何新目录或扩展名都会被忽略。提交前检查 `git status --short` 和暂存差异；需要时用 `git check-ignore -v 实际文件` 检查。

模型/数据/配置文件记录版本与 SHA256；归档日志时明确采集条件、代码 commit、配置版本，避免只写“最新版”。

<a id="s11"></a>
## 11. Python 环境与现有上位机

### 11.1 当前仓库的真实依赖

已读取 [requirements.txt](../software/upper-computer/requirements.txt)：

```text
numpy>=2.0,<3
opencv-python>=4.10,<6
pyserial>=3.5,<4
```

图形界面使用 **Tkinter**，不是 PyQt/PySide；系统包 `python3-tk` 可能需要补装。现有识别器是颜色/轮廓原型，并不是已接入 YOLO 的程序。电脑已验证的 Python/包版本，不能直接等同于板端支持的 ARM64 wheel 组合。

### 11.2 创建隔离环境

先确认 `python3 --version` 与依赖支持范围。以下操作假设仓库位于第 10 节的目录：

```bash
python3 -m venv ~/vision-claw/venvs/upper-computer
source ~/vision-claw/venvs/upper-computer/bin/activate
python -m pip install --upgrade pip
cd ~/vision-claw/src/Vision-Claw/software/upper-computer
python -m pip install --only-binary=:all: -r requirements.txt
python -m pip check
```

首次明确要求 wheel，是为了及时发现平台/版本不支持，避免在 TF 卡上意外开始长时间源码编译。若报 `No matching distribution found`，先核查 Python 版本、ARM64、索引源和包范围；不要立刻换成 `sudo pip`。

虚拟环境基于创建它的解释器，不能把 Windows venv 搬到板上，也不能在升级 Python 大版本后保证旧 venv 继续可用。[Python venv 官方文档](https://docs.python.org/3/library/venv.html)

### 11.3 OpenCV 的几条安装路线只能明确选一种

| 路线 | 适用情况 | 注意 |
| --- | --- | --- |
| venv 中 `opencv-python` | 按现有 requirements 运行 | 先确认 ARM64 wheel、系统图形库；实际能力看构建信息 |
| venv 中 `opencv-python-headless` | 后续纯后台应用，不需要 OpenCV GUI | 不能与普通/`contrib` 变体同时混装；采用前要调整依赖并验证 |
| apt 的 `python3-opencv` | 需要发行版集成的特定视频功能 | 普通 venv 默认不可见；若用 `--system-site-packages` 会降低隔离性，必须记录 |
| 自编译 OpenCV | 明确需要特定 GStreamer/RGA 等能力 | 后续专项工作，记录源码/编译参数，不作为第一次初始化默认步骤 |

apt 的 NumPy/OpenCV 可能不满足当前 requirements 的版本范围，不能简单装完 apt 包就宣称现有工程依赖通过。若 SDK 需要旧 NumPy，把 RKNN 放独立环境，之后再决定兼容版本或进程间接口。

### 11.4 最小验证：只运行模拟器

在上位机目录和对应 venv 中执行：

```bash
python -c "import sys, platform, cv2, numpy, serial; print(sys.version); print(platform.machine()); print('OpenCV', cv2.__version__, 'NumPy', numpy.__version__, 'pyserial', serial.__version__)"
python -m sorting_app --headless
python -m sorting_app --headless --drop-first-ack
python -m unittest discover -s tests -v
```

目前代码的 `--headless` 路径明确创建 `MockSTM32`/`MockTransport`，用于模拟，不连接真实串口。正常演示预期输出包含 `"simulated": true`，完整处理 12 件；`physical_sort_calls` 字段此时统计模拟器执行次数，**不是实物分拣次数**。以当前 commit 和实际输出记录结果。

这些命令是后续板端验收步骤；本手册编写时没有在板端执行它们。已有测试数量会随代码改变，记录执行时的数量，不固定写“永远九项”。

图形程序需进入有效桌面会话：

```bash
python -c "import tkinter; print(tkinter.TkVersion)"
python -m sorting_app
```

普通 SSH 没有 `DISPLAY` 时，第二条可能报无显示环境，这是会话问题，不等于依赖安装失败。不要对所有 SSH 连接强制 `export DISPLAY=:0`，也不要 `sudo` 启动 GUI 来绕过权限。

### 11.5 固化可复现环境

验证通过后，在激活的环境记录：

```bash
python -m pip freeze > ~/vision-claw/reports/upper-computer-pip-freeze.txt
python -m pip check
python -c "import cv2; print(cv2.getBuildInformation())" > ~/vision-claw/reports/opencv-build.txt
git rev-parse HEAD
```

`pip freeze` 是当前安装快照，不等于含系统库、wheel 哈希和 SDK 的完整锁定方案；上传前去掉本机路径或私有源信息。项目后续应提交经过验证的依赖锁定/约束文件，并分别记录训练、转换、板端环境，不能共用一份模糊的“总 requirements”。

<a id="s12"></a>
## 12. 摄像头、OpenCV 与图像采集

### 12.1 先确定相机类别

- USB UVC 摄像头：通常先按 V4L2 路线检查；仍需验证带宽、格式、曝光和稳定性。
- MIPI CSI：必须核对传感器型号、接口/排线方向、镜像驱动、设备树和 ISP 支持。不是任何排线相机都可直接用。
- 工业相机：先确认厂家有对应 Linux ARM64 SDK、许可证/驱动及 Python 支持。
- HDMI 输入、板载编解码器和相机节点可能都表现为视频设备，不能只看到 `/dev/video0` 就认定它是目标相机。

不要为了试 CSI 任意写入树莓派的 `config.txt` 或启用不匹配 overlay。具体设备树修改属于另一个有备份的硬件适配步骤。

### 12.2 枚举和稳定命名

相机已按规范接入后，板端：

```bash
lsusb
lsusb -t
v4l2-ctl --list-devices
ls -l /dev/v4l/by-id/ /dev/v4l/by-path/ 2>/dev/null
```

选中正确设备后，替换下面路径：

```bash
v4l2-ctl -d /dev/REPLACE_WITH_CAMERA --all
v4l2-ctl -d /dev/REPLACE_WITH_CAMERA --list-formats-ext
v4l2-ctl -d /dev/REPLACE_WITH_CAMERA --list-ctrls-menus
```

优先保存 `/dev/v4l/by-id/...`；没有唯一序列号时考虑固定 USB 物理口和 `by-path`。同一相机可能有多个节点，核对实际视频采集能力。现有程序是否接受设备路径需检查实现，不能只改文档就假定已支持。

### 12.3 权限与单帧检查

先查看设备节点属组。若确实由 `video` 组控制且用户未加入：

```bash
sudo usermod -aG video orangepi
```

退出重新登录后用 `id` 验证；systemd 服务也需重启才能获得新组。不要用 `chmod 777 /dev/video*` 或长期 root 运行。

以下是**接相机后才执行**的单帧检查；只打开相机，不控制 STM32。替换设备路径，在已装 OpenCV 的 venv 中执行：

```bash
python - <<'PY'
from pathlib import Path
import cv2

device = "/dev/v4l/by-id/REPLACE_WITH_CAMERA"
out = Path.home() / "vision-claw/data/camera-check.jpg"
cap = cv2.VideoCapture(device, cv2.CAP_V4L2)
try:
    if not cap.isOpened():
        raise RuntimeError(f"无法打开相机：{device}")
    ok, frame = cap.read()
    if not ok or frame is None:
        raise RuntimeError("相机已打开，但没有有效帧")
    out.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(out), frame):
        raise RuntimeError("保存图像失败")
    print("backend=", cap.getBackendName(), "shape=", frame.shape, "saved=", out)
finally:
    cap.release()
PY
```

取回图片目视检查清晰度、方向、色彩和视野，不以文件非空作为图像正确的唯一依据。`VideoCapture` 的格式/属性支持取决于后端和设备，`set` 调用成功也需读取实际值和图像确认。[OpenCV VideoCapture 文档](https://docs.opencv.org/4.x/d8/dfe/classcv_1_1VideoCapture.html)

### 12.4 为视觉建立固定采集条件

记录并在稳定后固定：

- 相机型号、镜头/焦距、安装高度、俯仰角、视野覆盖、USB 口/Hub。
- 分辨率、帧率、像素格式（MJPEG/YUYV 等）、采集后端、解码方式。
- 曝光时间、增益、白平衡、自动对焦是否关闭；实际控制名和值以 `v4l2-ctl` 输出为准。
- 光源位置、色温、遮光/反光处理、背景颜色和工作距离。
- 图像方向、畸变校正、标定分辨率、图像坐标与机构坐标的单位/原点。
- 静态/运动模糊、连续帧是否滞后、断开重连后是否读到旧帧。

当前上位机做平面四点映射；实际物体高度、镜头畸变、相机移动或改分辨率都可能改变坐标误差。以已知实测点验收，不能把默认 260×260mm 视为已量好的托盘尺寸。

相机测试先短时连续采集，再测计划工作时长和高负载下的丢帧/延迟；原始图像与标定结果不默认提交 Git。

<a id="s13"></a>
## 13. STM32 串口、权限与协议

### 13.1 三种通信背景必须分开

1. `software/upper-computer/docs/通信协议.md`：上位机模拟器的协议提案。
2. `firmware/stm32-motion-framework/`：队友初版 HAL 框架，命令与提案尚未统一，也尚非完整可烧录工程。
3. `experiments/single-motor/`：独立 A4988 电机实验，不是完整分拣固件，不能当作已支持串口协议。

因此“USB 插上了”“串口能打开”“电机实验能转”都不代表整机协议已经打通。

### 13.2 枚举设备、确定连接方式

连接前先确认当前 STM32 固件的上电行为；旧单电机固件可能按自身逻辑启动运动。初始化识别串口时保持执行器处于经过确认的安全状态。

板端只读枚举：

```bash
lsusb
ls -l /dev/serial/by-id/ /dev/serial/by-path/ 2>/dev/null
python -m serial.tools.list_ports -v
```

最后一条需在有 pyserial 的 venv 中。它用于列出端口，不主动发送运动指令。[pySerial 端口枚举文档](https://pyserial.readthedocs.io/en/latest/tools.html)

- 通过板载 USB 通信，需 STM32 固件确实实现 USB CDC 等接口；USB 供电成功不等于出现串口。
- 通过 USB 转 TTL，核对电平、TX/RX、GND及 VCC 是否连接；调试接口与通信接口不要混淆。
- 通过 40pin UART，先核对 pinmux/设备树/控制台占用/电平与针脚。不在未确认的 UART 上直接发送协议数据。

### 13.3 访问权限与固定设备名

查看实际节点属组：

```bash
ls -l /dev/ttyUSB* /dev/ttyACM* 2>/dev/null
id
```

Ubuntu/Debian 常见串口属组为 `dialout`；确认后加入：

```bash
sudo usermod -aG dialout orangepi
```

重新登录后检查 `id`。使用 `/dev/serial/by-id/...` 避免 `/dev/ttyUSB0` 变号；没有唯一序列号时，按 USB 物理路径区分并记录插口。

需要自定义 udev 规则时，先用 `udevadm info --attribute-walk --name=/dev/实际设备` 查真实属性，再按唯一序列号/物理位置匹配。不要只凭同一 VID/PID 匹配所有转接器，不直接给所有串口 `0666` 权限。

若发现 ModemManager 实际抢占目标端口，再考虑只对该设备排除；没有证据时不全局禁用它。打开串口可能改变 DTR/RTS 或使 MCU 复位，即使不发字节也要先确认设备行为。

### 13.4 正式协议需要写清的内容

| 类别 | 必须协商并记录 |
| --- | --- |
| 物理参数 | 串口设备、波特率、数据位、校验、停止位、流控、电平 |
| 编码与帧 | ASCII/二进制、帧头尾、长度、转义、字节序、CRC 类型 |
| 单位 | mm/脉冲/角度、坐标原点、正方向、限位范围 |
| 任务身份 | 命令编号、会话编号、重复命令去重、版本协商 |
| 状态反馈 | ACK 和动作完成的区别、错误码、传感器、位置可信度 |
| 超时与重试 | 丢 ACK、丢完成回复、断线、设备重启的处理 |
| 安全 | STOP、硬件急停、看门狗、掉线状态、恢复后是否允许动作 |
| 业务 | 回原点、路径、拨料、转盘到位、落料确认、计数依据 |

先做双方约定的只读版本/状态查询，再做仿真、限能单动作和整机联调。不要在双方尚未约定时“试着发 HOME/SORT”。软件 STOP 不能替代硬件急停。

<a id="s14"></a>
## 14. YOLO 训练、转换与板端运行环境

### 14.1 把环境按职责划分

| 环境 | 建议位置 | 主要内容 | 当前阶段 |
| --- | --- | --- | --- |
| 系统维护 | 香橙派系统 | apt、SSH、NetworkManager、时间、驱动 | 现在完成 |
| 上位机原型 | 香橙派独立 venv | NumPy、OpenCV、pySerial、按需 Tkinter | 初始化验证 |
| 数据采集/标注 | 电脑为主，板端采集 | 图片、类别定义、标注工具、数据版本 | 需求明确后建立 |
| YOLO 训练 | 合适的电脑/GPU 服务器 | Python、PyTorch、对应训练代码 | 正式开发阶段 |
| 模型转换 | 优先独立 x86_64 Linux 环境 | ONNX、RKNN-Toolkit2、匹配依赖 | 选择版本后建立 |
| NPU 推理 | 香橙派 ARM64 | RKNPU 驱动、Runtime、Lite2 或 C/C++ | 驱动先盘点，推理后验收 |
| 应用部署 | 香橙派经验证环境 | 相机、预处理、推理、后处理、串口、状态机 | 整合时建立 |

不要把全部框架塞进一个 venv。尤其现有上位机要求 NumPy 2，而某个 RKNN wheel 可能限制其他版本，必须看实际发行包要求。

### 14.2 训练电脑需要设置什么

- 确认电脑 OS、CPU 架构、RAM、磁盘空间、GPU 型号/显存；没有 GPU 时明确 CPU 训练的代价，或选择可用训练服务器。
- 使用 NVIDIA GPU 的训练电脑才考虑对应驱动和 CUDA 版 PyTorch；版本组合按该次 PyTorch 官方安装说明选择。
- **香橙派的 RK3588 NPU 不是 NVIDIA CUDA 设备**，不通过安装 CUDA/cuDNN/TensorRT 获得 NPU 加速。
- 为训练建立独立环境，例如 `vision-claw-train`，固定 Python、PyTorch、Ultralytics/训练仓库的版本或 commit。
- 先确认选定模型能走通到 RK3588 的导出与后处理路线，再大量投入训练；当前研究候选 YOLOv8n 不因最新网页改版自动替换成其他模型。
- 数据集记录类别 ID/名称、标注格式、训练/验证/测试拆分、采集条件和授权；同一连续拍摄场景避免跨集合泄漏。
- 记录随机种子、输入尺寸、batch、epochs、增强、损失/指标、最佳权重判据；验证集不替代独立测试集。
- 记录代码、数据、配置和权重 SHA256。训练平台账号、数据下载凭据不进仓库。
- 标注/训练前先确认实际赛题类别、视觉任务和可评估指标；不把早期方案中的演示六类当作最终全部类别。

### 14.3 转换环境需要设置什么

采用单独的 Linux venv/容器/虚拟机，不在系统 Python 里凑转换依赖。Windows 用户可评估 WSL2，但需确认目标工具版本与环境支持；转换成功不意味着 WSL 可以直接访问板端 NPU。

以下矩阵先填完整，再安装：

| 必记字段 | 示例含义，不是固定版本要求 |
| --- | --- |
| 转换平台 | x86_64 Linux，发行版/版本/容器镜像摘要 |
| Python | wheel 所支持的具体次版本，如 `cp310` 对应 CPython 3.10 |
| Toolkit2 | release/tag/commit、wheel 文件名、SHA256 |
| 依赖 | ONNX、NumPy、框架依赖及约束 |
| 模型 | 来源 commit、权重、输入输出、导出方法 |
| 目标 | `rk3588`，精度/量化方式、输入尺寸 |
| 板端匹配 | Runtime/Lite2/内核驱动支持关系 |

Rockchip 的不同版本可能提供不同平台能力；不能把某个版本的 ARM64 wheel 能力推广到所有导出路线。当前 Ultralytics 的 RKNN 集成页面明确要求其导出流程使用 x86 Linux；若采用这一流程，就遵循该限制。采用 Rockchip 自己的转换 API 时，则按所选 SDK 的支持矩阵。[Ultralytics RKNN 集成说明](https://docs.ultralytics.com/integrations/rockchip-rknn/)

### 14.4 模型转换必须保留的语义

转换链可能是 `.pt → ONNX → .rknn`，但具体导出图及输出布局必须与板端后处理匹配。不能把任意 Ultralytics 导出的 ONNX 与任意 Model Zoo 解码器拼接后就当作正确。

逐项记录：

- 模型任务：检测/分割/分类；类别数、类别顺序。
- 输入：尺寸、batch、NCHW/NHWC、RGB/BGR、dtype、归一化和量化参数。
- 缩放：letterbox 比例、填充值、是否保持长宽比、输出坐标逆变换。
- 输出：张量数量、shape、布局、是否含 sigmoid/DFL/NMS、置信度定义。
- 阈值：置信度和 NMS IoU；是否跨类抑制、最大检测数。
- 量化：FP16/INT8、代表性校准数据、随机抽样策略和精度变化。
- 验证：同一批真实图片上比较训练框架、ONNX、RKNN 输出；不能只比较一张演示图。

INT8 校准集应覆盖真实光照、尺寸、背景和物体分布，独立测试集保留作验收。模型能 `load` 并不代表类别映射和坐标正确。

<a id="s15"></a>
## 15. RK3588 NPU 与 RKNN 检查

### 15.1 分清四层

1. 内核 RKNPU 驱动：与硬件交互。
2. RKNN Runtime：用户空间执行库。
3. Python Lite2 或 C/C++ API：应用调用接口。
4. 已转换的 `.rknn` 模型和对应预/后处理。

RKNN-Toolkit2 用于转换/评估，RKNN-Toolkit-Lite2 用于板端 Python 部署；这些组件不是“装一个 pip 包就全部具备”。应使用支持 RK3588 的 Toolkit2 系列，不能混用旧的 RKNN-Toolkit 路线。[Rockchip RKNN-Toolkit2 仓库](https://github.com/airockchip/rknn-toolkit2)

### 15.2 先盘点当前镜像，不直接替换库

板端检查：

```bash
uname -r
sudo dmesg | grep -Ei 'rknpu|npu' | tail -n 50
ls -l /dev/dri/ 2>/dev/null
lsmod | grep -i rknpu
ldconfig -p | grep -i rknn
find /usr/lib /usr/local/lib /lib -name 'librknnrt.so*' -print 2>/dev/null
```

- `lsmod` 没有输出不代表驱动不存在，驱动可能编入内核；结合启动日志和实际示例判断。
- `/dev/dri/renderD*` 可能属于不同设备，不能硬认定 `renderD128` 就是 NPU。
- `ldconfig` 没列出库也可能是 SDK 使用私有目录；需查实际应用加载路径。
- 部分内核可从 `/sys/kernel/debug/rknpu/` 读取版本/负载，路径与可用项依具体内核；不存在时不要凭空创建或据此认定硬件损坏。
- 读取/修改 debugfs、频率和驱动参数的权限不同；日常应用不应靠 root 绕过设备权限。

若缺驱动，优先评估当前镜像的厂商支持方案。不要仅复制 `librknnrt.so` 就宣称修好了内核驱动，也不要从不明教程替换整个启动分区。

### 15.3 选定 SDK 版本后建立独立 venv

核对实际 wheel 的架构、Python ABI、glibc 和依赖要求。需要其他 Python 次版本时，以并存解释器建环境，不替换系统 Python。下面是占位示例，不能原样安装：

```bash
# 将解释器和文件名替换为已选定、校验过的实际版本。
REPLACE_WITH_PYTHON -m venv ~/vision-claw/venvs/rknn-runtime
source ~/vision-claw/venvs/rknn-runtime/bin/activate
python -m pip install /实际路径/REPLACE_WITH_ARM64_LITE2_WHEEL.whl
python -m pip check
python -c "from rknnlite.api import RKNNLite; print('Lite2 import OK')"
```

最后一条只验证 Python 导入，不初始化硬件，也不证明模型能运行。若需要与上位机合并环境，先求解双方依赖并回归；不强行忽略版本冲突。

驱动、Runtime、Lite2、转换器不一定要求版本字符串全部完全相同，但必须符合该 SDK 文档说明的兼容关系。升级前记录旧库路径/包归属/版本/校验值，准备可恢复副本。不要无备份覆盖 `/usr/lib/librknnrt.so`，也不要长期靠多处重复库文件碰运气。

### 15.4 验证顺序

1. 选择明确支持 RK3588 的官方样例及匹配模型，固定仓库 commit；模型和样例输入也记录来源。
2. 按该样例 README 运行，检查返回值、实际 Runtime/Driver 版本、输出是否符合参考结果。
3. 确认真正调用 NPU，排除静默 CPU fallback；保存实际日志中的后端证据。
4. 再测本项目导出的模型，验证图像前处理、类别、坐标、置信度和后处理。
5. 最后接入实时相机和上位机状态机，不把首次 SDK 测试与运动控制混在一起。

YOLOv8 路线可从 [Rockchip Model Zoo YOLOv8 示例](https://github.com/airockchip/rknn_model_zoo/blob/main/examples/yolov8/README.md)核对导出与后处理。示例文档会变化，实际选用时记录 commit，不把网页上的最新模型作为本项目自动升级目标。

### 15.5 性能验收范围

分别统计相机采集、解码、预处理、NPU 推理、后处理、坐标换算、串口往返和动作完成时间。官方模型推理耗时不是整个分拣系统一帧延迟。

至少记录：输入尺寸、量化方式、NPU 核使用方式、warmup 次数、样本数、平均/p95 延迟、有效 FPS、CPU/RAM、温度、功耗/稳定性。先建立默认配置基线，再尝试零拷贝、RGA、多线程/多核；每次优化同时复测输出正确性。

<a id="s16"></a>
## 16. 性能、电源管理与存储寿命

### 16.1 温度、内存和进程基线

板端检查：

```bash
uptime
free -h
swapon --show
df -h /
systemctl --failed
ps -eo pid,comm,%cpu,%mem --sort=-%cpu | head -n 15
for zone in /sys/class/thermal/thermal_zone*; do
    [ -r "$zone/type" ] && [ -r "$zone/temp" ] || continue
    printf '%s: ' "$(cat "$zone/type")"
    cat "$zone/temp"
done
```

Linux thermal 节点通常以毫摄氏度表示温度，例如 `55000` 为 55°C；确认节点语义后再换算。不同节点可能是 SoC、CPU、GPU 或其他传感器，不只盯一个数字。

记录空闲与实际程序负载下的温度、RAM、频率变化、USB 稳定性。持续升温、异常掉电、I/O 错误、明显降频或电源线异常温升时停止负载并排查。温度上限以 SoC/板级资料和实际散热设计为准，不随意关闭热保护。

### 16.2 性能模式不是首次初始化必选项

- 先用默认 CPU/NPU 调频策略跑通，建立可对比基线。
- 不直接照搬网上 `performance`、超频、电压或 devfreq 路径；这些设置与内核/镜像有关。
- 不为追求 FPS 先关闭所有系统服务。逐项确认服务用途，改变后记录资源改善与功能影响。
- NPU 推理仍需要 CPU 做采集、解码和后处理；高 CPU 占用不自动说明 NPU 失效。
- ZRAM/swap 是否启用先检查现状。swap 可以缓解内存耗尽，但不能替代足够 RAM，也不适合用大量 TF 卡 swap 掩盖环境过重。
- 若需要压力测试，先验证电源/散热并保存数据，在电机不动作时使用限时测试；不要无限满载后离开。

### 16.3 防休眠与主机依赖

- 笔记本分享网络时，接电源、合盖和睡眠策略要与使用方式匹配。电脑合盖睡眠后，板端 NAT 出口可能消失。
- 板端桌面的锁屏、息屏、自动挂起是不同功能。可允许息屏，是否关闭自动挂起按长期服务需求决定。
- 先在桌面电源管理或发行版支持的方式中调整，不一开始就全局 mask 所有 sleep target。
- 正式比赛尽量使采集、识别和控制不依赖互联网；若仍依赖笔记本，要把笔记本供电与连接列入设备清单。
- 第二网口、Wi-Fi/蓝牙仅按实际需要启用并测试。5 Plus 的无线能力取决于实际安装模块和驱动，不因板名推定已有可用无线网卡。

### 16.4 日志容量和磁盘维护

```bash
journalctl --disk-usage
du -sh ~/vision-claw/logs ~/vision-claw/data ~/vision-claw/models 2>/dev/null
```

确定保留周期、单文件上限、总容量上限和导出位置。建议初期为 system journal 设一个可承担的总量，如 200MB～500MB，具体按磁盘余量决定；先查看当前 journald 配置，再用独立 drop-in 设置 `SystemMaxUse`、`RuntimeMaxUse` 等，不覆盖整个配置文件。

应用日志采用轮换，普通运行不持续输出每帧所有张量，不无限保存原始录像。遇到故障先保留现场日志再清理；不要在初始化过程中执行无差别删除或格式化。

<a id="s17"></a>
## 17. 程序配置、日志与开机服务

### 17.1 初始化阶段先手动运行

当前上位机的 `--headless` 是一次模拟流程，完成后会退出，**不是生产后台服务入口**。不要把它配置成开机无限重启的“分拣服务”。

进入正式部署前，应用应具备：

- 配置校验、日志路径、版本输出、明确退出码和单实例约束。
- 相机/模型/串口不可用时的受控等待或退出，而非无限高速报错。
- 接收停止信号，释放相机、关闭串口、保存必要状态。
- 启动后默认待命，确认设备状态与操作授权后才允许运动。
- 连接丢失、进程重启或 MCU 重置后不自动重放不确定的运动任务。
- 操作界面、后台状态机和维护入口职责明确；远程桌面退出不应意外改变设备状态。

这些属于后续应用实现要求；本次只记录，不声称现有程序已经全部具备。

### 17.2 配置项规范

| 配置组 | 应包含的内容 |
| --- | --- |
| 运行模式 | simulation / hardware，启动默认待命，版本/配置 schema |
| 相机 | 稳定设备路径、后端、尺寸、格式、曝光、白平衡 |
| 模型 | 路径、SHA256、类别表、输入尺寸、预处理、阈值、NPU 设置 |
| 标定 | 标定文件、分辨率、单位、坐标方向、验证误差、更新时间 |
| 串口 | 稳定设备路径、波特率、帧格式、超时、协议版本 |
| 业务 | 类别规则、盒号映射、任务超时、恢复和停止规则 |
| 运行资源 | 日志目录/级别/轮换、数据目录、保存图像策略 |

默认模板可入 Git；实物标定、机器路径和凭据留在本机。启动时记录配置版本或摘要，但不要把全部敏感环境变量打印进日志。

### 17.3 systemd 服务设计模板：后续有真实入口再使用

以下仅展示结构，`REPLACE_WITH_REAL_SERVICE_MODULE` 当前不存在。不要直接安装启用：

```ini
[Unit]
Description=Vision-Claw application
After=network.target
StartLimitIntervalSec=60
StartLimitBurst=3

[Service]
Type=simple
User=orangepi
Group=orangepi
WorkingDirectory=/home/orangepi/vision-claw/src/Vision-Claw/software/upper-computer
ExecStart=/home/orangepi/vision-claw/venvs/upper-computer/bin/python -m REPLACE_WITH_REAL_SERVICE_MODULE
Environment=PYTHONUNBUFFERED=1
Environment=PYTHONIOENCODING=utf-8
Restart=no
TimeoutStopSec=15
UMask=0027
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

- 直接使用 venv 的 Python 绝对路径；systemd 不会自动执行交互 shell 的 `activate`。
- `WorkingDirectory`、用户/组、模型/配置路径必须与实际部署一致。不要为了文件权限把整个服务改为 root。
- 初始化默认 `Restart=no`；只有安全恢复语义验证后才考虑 `Restart=on-failure`、`RestartSec` 和重启限额。
- 仅使用本地相机与串口的应用不应无必要等待互联网。确需网络地址时可评估 `network-online.target`，但它也不保证互联网、DNS或 NTP 一定成功；应用仍需处理重试/离线。
- `SupplementaryGroups` 按实际设备组添加，不能照抄不存在的组。设备在启动时未出现、稍后插入时也要有明确行为。
- 不把 GUI 程序直接当普通系统服务启动；图形会话、权限和生命周期要单独设计。
- 停止超时被 systemd 强制结束时，不能保证串口 STOP 已发出；安全停机最终还需下位机看门狗、急停和明确的失联策略。

对应配置语义见 [systemd.service 官方手册](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html)。

真实服务完成后，先做静态检查和单次手动启动，再考虑 enable：

```bash
# 只有真实 unit 已准备好并审核后才执行这些命令。
sudo systemd-analyze verify /etc/systemd/system/vision-claw.service
sudo systemctl daemon-reload
sudo systemctl start vision-claw.service
systemctl status vision-claw.service --no-pager
journalctl -u vision-claw.service -b --no-pager -n 100
sudo systemctl stop vision-claw.service
# 冷启动安全行为验证通过后，才执行：
# sudo systemctl enable vision-claw.service
```

### 17.4 验证异常恢复

至少覆盖相机未插、串口未插、模型文件缺失、配置错误、磁盘不足、程序退出、网络丢失、STM32 重启。验证时采用仿真或已限制风险的硬件条件。

当前原型没有完整的跨进程自动任务恢复。结果未知时先核对实物与盒内状态，不通过重新启动程序把未知任务当作从未执行。

<a id="s18"></a>
## 18. 安全、备份、恢复与离线使用

### 18.1 最小安全基线

- 修改仍在使用的默认口令，关闭不用的账户/远程服务，保留可靠管理员与救援路径。
- SSH 主机指纹和用户公钥分别管理；不泄露用户私钥、GitHub token 或完整 `.env`。
- 板端不需要为这套直连拓扑向公网开放 SSH/VNC，也不需要无条件开启端口转发。
- 不全局关闭防火墙、AppArmor 或其他保护来解决单个端口/路径问题。
- 检查 `ss -lntup` 和开机服务，理解哪些端口确实需要监听。
- 更新策略、账户权限、数据脱敏与备份应同时维护，不依赖“这是局域网所以不用管”。

若决定启用 UFW，先检查现有规则、确认唯一 SSH 来源，并允许当前管理通道；下面只适合当前 `.1 → .2` 的直连关系：

```bash
sudo ufw status verbose
# 确认采用 UFW 且原管理连接仍保留后，再按需执行：
# sudo ufw allow in on enP3p49s0 from 192.168.50.1 to any port 22 proto tcp
# sudo ufw enable
```

更换电脑地址、网口或路由器后规则也要调整。不要直接复制一个只允许旧地址的规则集后关闭原 SSH；不为开放网页面板而允许全部入站流量。

### 18.2 需要备份的内容

| 内容 | 备份方式与注意事项 |
| --- | --- |
| 代码 | 已提交 commit/分支、未提交补丁；远端确认同步 |
| 系统身份 | 镜像来源、OS/内核/架构、磁盘布局、软件包列表 |
| 网络 | NetworkManager 配置和需要的 Windows NAT 说明；配置可能含密钥，受限保存 |
| SSH | 服务器配置、必要主机密钥；用户私钥单独安全保管，不上传 Git |
| 应用 | 依赖锁定、配置、标定、模型、类别表、校验值 |
| 服务 | systemd/udev/日志轮换等实际配置及恢复说明 |
| 数据 | 有价值的原始图片、标注与验收样本，不无差别归档所有临时日志 |
| 整卡 | 初始化稳定后制作离线整卡镜像，注明版本、大小和 SHA256 |

### 18.3 备份位置与一致性

- 同一 TF 卡上的 `backups/` 只是暂存，不是抵抗卡损坏的备份。至少复制一份到电脑/其他物理存储。
- 备份目录设合适权限。含网络连接密钥、SSH 主机密钥或个人数据的归档应加密保存；不作为公开文档附件。
- 备份运行中的数据库或正在写入的应用文件可能不一致。先停应用或使用对应一致性备份机制。
- 需要保持 Linux 权限、软链接、ACL/xattr 时，使用适当的 tar/rsync 参数或镜像方案；普通拖到 Windows 目录不保证保留全部元数据。
- 整卡镜像优先正常关机后将卡交给电脑读取；确认备份工具的“读取源”与“写入目标”，不要误覆盖原卡。
- 还原镜像到另一张卡时注意目标实际扇区容量可能比同标称卡略小；先验证可还原性。
- 完整镜像克隆到第二块板时，检查重复的静态 IP、hostname、machine-id 和 SSH 主机密钥等身份，不让两台设备冒用同一身份。

### 18.4 备份之后必须做恢复验收

尽量使用备用 TF 卡演练：从归档恢复 → 启动 → SSH → 网络/时间 → 环境导入 → 模拟器 → 必要外设。保留原可用卡，验收成功再替换。

关键变更回退表：

| 变更 | 变更前保存 | 失败后的处理 |
| --- | --- | --- |
| IP/网关/SSH | 旧配置、第二会话、救援入口 | 回滚对应配置，验证登录，不先重刷整卡 |
| Python 依赖 | 旧 venv 的依赖记录、wheel、代码 commit | 重建旧版本环境，避免盲目降级系统 Python |
| NPU Runtime | 版本、路径、包归属、原文件/镜像 | 恢复已验证组合并重跑样例 |
| 内核/设备树/启动固件 | 可启动备份和完整操作记录 | 使用已验证恢复方案或备用启动卡 |
| 标定/模型 | 上一版文件和散列、对应输入条件 | 一起恢复模型/配置/标定，不能只换权重 |

### 18.5 离线安装与比赛运行

- 验收通过后留存本平台所需的 wheel、SDK、模型与文档。Windows x86 下载的 wheel 不能自动当作 Linux ARM64 包使用。
- 可在板端的已验证 venv 中按固定依赖下载 wheel，保存到仓库外目录；注意 `pip freeze` 可能含本地路径，先整理为可重建清单。
- 离线安装用 `--no-index --find-links=...` 配合固定依赖，单独测试是否缺少系统库；仅保存 Python 包不等于保存了 apt 依赖和驱动。
- 正式启动不应临时下载模型、检查远端最新版本或依赖在线鉴权后才能执行核心分拣。
- 离线时要有正确时间来源/策略，确认图形界面、相机、模型和串口能全部本地启动。
- 备用物资至少考虑已验证启动卡、电源/线材、网络线、必要相机/串口转接件及恢复文档；按实际使用和预算准备，不为清单形式盲目采购。

<a id="s19"></a>
## 19. 分阶段验收与三条主线合并

### 19.1 A：系统初始化完成

- [ ] 已记录实际 OS、内核、架构、RAM、启动介质和镜像来源；无法确定的字段明确标注。
- [ ] 电源极性/带载供电和散热经过实物检查，TF 卡没有持续 I/O 错误。
- [ ] SSH 登录可重复，账户口令/密钥和恢复入口已处理。
- [ ] 板端重启后仍为预期地址，默认网关和 DNS 配置自动恢复。
- [ ] Windows 重启/网络重连后的共享行为已确认，维护说明已保存。
- [ ] 时间正确，HTTPS 和 apt 通过；NTP/冷启动校时有实际证据。
- [ ] 中文字体、locale 和所需桌面语言可用；若输入法不需要则标记“不适用”。
- [ ] 必要工具安装，更新策略与本地配置备份明确。
- [ ] 正常关机再上电能够恢复维护，不依赖板端键鼠。

### 19.2 B：开发准备完成

- [ ] 仓库路径/分支/commit 已记录，源码和本地数据分离。
- [ ] 上位机 venv 建立，`pip check`、导入、模拟流程和现有测试实际通过。
- [ ] 摄像头与 STM32 的选型/连接方式明确；已到货设备完成相应基础检查。
- [ ] 未到货或暂不接入的设备标注阻塞/延期原因，不能打勾假装通过。
- [ ] 正式串口协议尚未达成的部分列成双方待确认项。
- [ ] NPU 驱动/Runtime 现状已盘点，后续转换和板端环境方案有版本依据。
- [ ] 文档、对话记录、依赖计划和备份信息已整理，可由新对话接续。

**建议将 A 全通过、B 的基础开发项通过且硬件延期项有明确记录，作为“初始化整理完成”的检查依据。** 具体未到货外设可由用户决定是否阻塞合并；不用等正式 YOLO 训练和部署全部结束才合并，这与用户的计划顺序一致。

### 19.3 三条主线合并前检查

当前计划涉及 `main`、`codex/vision-yolo`、`codex/orangepi-bringup`。真正合并时另行执行：

1. 更新各分支状态，检查未提交变更和最新远端差异；保留各自已确认的结论。
2. 对齐目录、依赖声明、接口文档和 `ai-dialogue/README.md` 的当前状态。
3. 区分研究结论、电脑模拟、板端验证和实物验证，不把三个分支的不同阶段写成“全部部署完成”。
4. 冲突按实际最新事实处理，特别注意依赖版本、相机配置、协议定义和机器路径。
5. 运行合并后相关测试，记录基线 commit/必要 tag，再开始正式 YOLO 开发与模型部署。

本手册提交/同步不等于三条分支已经合并。

### 19.4 C/D：模型部署与整机完成，后续另行验收

- [ ] 训练、转换与运行的版本矩阵固定并可重建。
- [ ] 官方 NPU 样例、本项目模型和真实图片精度对比通过。
- [ ] 相机固定条件、标定误差和模型输入输出一致。
- [ ] 串口协议与固件匹配，停止/超时/去重/掉线恢复通过。
- [ ] 端到端延迟、分拣正确率、工作时长与温度实测。
- [ ] 自启动/待命/启动授权/停止行为符合整机要求。
- [ ] 断网、进程退出、MCU 重启、设备断开等异常经过可控测试。
- [ ] 发布版本与整卡/应用备份完成，恢复演练通过。

### 19.5 建议的记录粒度

每项写“日期、执行者、命令/操作、实际结果、证据位置、是否通过、剩余问题”。一条示例：

```text
项目：默认路由重启恢复
状态：待验证
已知：NetworkManager 已保存网关 192.168.50.1，reapply 成功
验收：正常关机再上电，重新 SSH，查看 ip -4 route 并验证 HTTPS
禁止替代证据：不能用重启前的 route 输出声称重启持久性已通过
```

<a id="s20"></a>
## 20. 日常使用与故障定位

### 20.1 每次开始工作

1. 检查接线与电源；需要只做软件初始化时保持执行器不动作。
2. 电脑连好网络和直连网线，确认不会在维护过程中自动睡眠。
3. `ssh orangepi@192.168.50.2` 登录。
4. 快查时间、路由、磁盘、失败服务和代码版本；缺少默认路由时才用临时命令补。
5. 激活对应环境；先模拟/只读检查，再按本次任务范围接设备或运行程序。
6. 记录改变了什么，避免一次同时改系统、模型、相机曝光和协议而无法定位问题。

板端常用只读快查：

```bash
date -Is
ip -4 route
df -h /
free -h
systemctl --failed
```

### 20.2 每次结束工作

1. 停止应用/采集/运动流程，确认设备处于已定义的安全状态。
2. 保存必要配置与日志摘要，更新本次对话记录。
3. 查看 Git 差异，确认没有误加入凭据、模型、日志或标定。
4. 不再使用板子时正常关机：

```bash
sudo shutdown -h now
```

SSH 断开不是立即断电的充分条件。等系统完成关机和存储写入，结合本板显示/指示状态判断后再断电；不要在更新、写卡或文件写入时直接拔电。

### 20.3 常见问题对照表

| 现象 | 首先看什么 | 对应处理 |
| --- | --- | --- |
| 电脑连不上 `.2` | 网线、接口 Up、两端 IP、是否换网口 | 先恢复局域链路，不先重装系统 |
| SSH `Connection refused` | 地址是否正确、ssh 服务是否运行 | 本地/救援通道查看服务，不等同于密码错误 |
| SSH `Permission denied` | 用户名、认证方式、公钥权限 | 使用已授权账户；不反复改网络 |
| SSH 主机指纹改变 | 是否重刷/换板/IP 冲突 | 核实身份后更新对应记录 |
| `Network is unreachable` | `ip -4 route` 是否有默认网关 | 本例用临时 route 命令补，再查持久配置 |
| 公网 IP 通、域名不通 | 实际 DNS 与 VPN 转发 | 检查解析链路；不要认定是网线坏 |
| 域名解析到 `198.18.x.x` | 当前 VPN 虚拟 DNS 行为 | 用真实 HTTPS 请求判断可用性 |
| HTTPS 证书尚未生效/过期 | 板端时间、证书有效期 | 先校时，之后检查证书链；不关闭校验 |
| `curl` 超时 | 目标、TCP、VPN 路由、代理地址 | 分层测试，不由单个站点推定全部断网 |
| apt 找不到包 | OS 代号、源、架构、包名 | 不混 Ubuntu/Debian 或其他版本源 |
| pip 无兼容发行包 | Python ABI、ARM64、索引、包版本 | 选兼容版本/环境，不用系统 root pip 绕过 |
| OpenCV 导入失败 | 混装变体、NumPy ABI、系统库 | 在独立 venv 对齐组合并 `pip check` |
| GUI 报 `$DISPLAY` 不存在 | 是否在普通 SSH 会话 | 用 headless 模拟或进入有效桌面会话 |
| 相机黑屏/无帧 | 设备节点、占用、格式、供电、权限 | 先 V4L2 单帧，再查 OpenCV 后端 |
| 串口消失/编号变化 | USB 供电、线、固件、by-id | 固定身份，区分 USB 供电与 CDC 功能 |
| 串口权限不足 | 用户组、会话是否重新登录 | 正确组权限，避免 `chmod 777` |
| 串口通但设备不执行 | 协议版本/参数/状态/固件 | 不混三套工程，不发送随机动作试错 |
| Lite2 能导入但推理失败 | 驱动、Runtime、模型版本/目标 | 按兼容矩阵与官方样例隔离问题 |
| NPU 输出框错位 | 颜色/布局/letterbox/坐标逆变换 | 对照同一输入的各阶段输出 |
| 高负载重启/USB 掉线 | 电源压降、线材、温度、内核日志 | 先排查硬件稳定性，再讨论模型优化 |
| 重启后时间回退 | RTC/电池、NTP、电脑出口 | 冷启动复测并建立离线校时方案 |
| 空间满、系统只读 | 磁盘/inode、TF I/O 错误、日志 | 先保留证据/备份，查存储与日志策略 |

### 20.4 必须等具体需求再做的设置

以下项目已经纳入考虑，但不应一律安装或启用：

- Docker/Podman：有可复现环境需求时评估；还需考虑 ARM64 镜像、设备透传、权限、存储和网络，不能替代 NPU 内核驱动。
- ROS/ROS 2：只有项目架构明确采用才建立对应发行版环境；当前 Python 上位机并不因此缺少必需环境。
- Jupyter：探索/调试工具，可按需经 SSH 隧道访问；不作为生产自启动核心。
- Web 控制台/数据库/消息队列：由实际接口与状态持久化需求决定。
- SPI/I²C/PWM/GPIO：只有新增传感器/外设明确型号和针脚后，才启用对应总线与驱动；当前电机控制职责在 STM32。
- 蓝牙、Wi-Fi、音频、额外 HDMI：按实际模块、用途和镜像支持验收，不作为所有机器必须配置项。
- NVMe/eMMC 启动迁移、容器化、只读根文件系统、看门狗、UPS：是稳定性增强方向，需要各自的恢复与故障测试。
- 内核重编译、交叉编译工具链、RGA/MPP 深度优化：遇到明确性能/驱动需求再做，不妨碍先完成可运行基线。

<a id="s21"></a>
## 21. 环境记录模板与资料入口

### 21.1 可复制的本机环境记录模板

以下内容可另存为去敏后的板端验收记录；未知就填“未验证”，不要填想当然的版本。

```yaml
record_date: "实际日期"
board:
  model: "Orange Pi 5 Plus"
  soc: "RK3588"
  ram_observed: "未验证"
  power_supply: "标称 UBEC 5V/5A，带载验证待补"
  cooling: "未验证"
storage:
  boot_medium: "64GB TF，实际分区待补"
  root_filesystem: "未验证"
image:
  source_page: "https://www.fujianleji.com/orange/Orange_Pi_5_Plus_download.html?utm_source=chatgpt.com"
  filename: "未核实"
  sha256: "未核实"
os:
  id_version_codename: "以 /etc/os-release 为准"
  kernel: "以 uname -r 为准"
  architecture: "未验证"
  desktop: "未验证"
  locale: "中文待设置"
  timezone: "待确认采用 Asia/Shanghai 或 Asia/Singapore"
  time_sync: "曾启用 NTP，尚无同步成功证据"
network:
  host_ipv4: "192.168.50.1/24"
  board_ipv4: "192.168.50.2/24"
  interface: "enP3p49s0"
  profile: "my_Lenovo_computer"
  gateway: "192.168.50.1"
  configured_dns: ["223.5.5.5", "1.1.1.1"]
  windows_nat: "OrangePi，已确认 Active"
  vpn_constraint: "保留电脑 VPN，虚拟 DNS 需实测 HTTPS"
  reboot_verified: false
python:
  executable: "未验证"
  version: "未验证"
  environment: "计划使用独立 venv"
  requirements_snapshot: "未生成"
vision:
  camera_model_device: "待接入确认"
  capture_format: "未验证"
  calibration: "未验证，不提交机器标定"
serial:
  device_identity: "待接入确认"
  protocol_version: "待与 STM32 队友统一"
rknn:
  driver: "未验证"
  runtime: "未验证"
  lite2: "未安装或未核实"
  toolkit2_conversion_version: "待选型"
  model_sha256: "未部署"
validation:
  desktop_boot: "用户实物确认"
  ssh: "用户登录成功"
  public_ip_ping: "用户反馈通过"
  https: "最近报证书尚未生效，待校时后重测"
  upper_computer_on_board: "未执行"
  camera_serial_npu: "未验收"
git:
  repository: "https://github.com/lldb-123/Vision-Claw"
  branch: "codex/orangepi-bringup"
  deployed_commit: "板端实际部署后填写"
backup:
  location: "本地受限记录，不放凭据"
  restore_verified: false
```

### 21.2 仓库中的相关资料

- [当前对话索引与项目状态](../ai-dialogue/README.md)
- [首次上电与镜像来源](../experiments/orangepi-5-plus/2026-11-08-first-boot.md)
- [网线直连、SSH 与联网实测记录](../ai-dialogue/2026-11-07-005-orangepi-no-keyboard-network.md)
- [上位机原型及实际运行方式](../software/upper-computer/README.md)
- [上位机演示协议](../software/upper-computer/docs/通信协议.md)
- [队友固件说明](../firmware/README.md)
- [独立单电机实验](../experiments/single-motor/README.md)

### 21.3 外部资料使用规则

本文在相应章节链接了厂商/项目官方说明。系统包、SDK wheel、模型示例和网页会变化；实际安装前以**当前板端环境与选定 release**为准，并记录版本。某个新版本支持更多平台，不代表旧镜像、旧 Python 或旧 Runtime 自动兼容。

后续更新本文时保留“现状、建议、已执行、已验证”的区别。初始化项目只在取得对应证据后打勾；不要因为生成了文档、写好了命令或提交了 Git 就写成板端设置完成。
