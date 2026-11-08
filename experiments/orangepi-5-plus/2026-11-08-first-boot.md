# Orange Pi 5 Plus 首次上电与桌面启动

- 记录日期：2026-11-08，Asia/Singapore。
- 状态：**用户确认 Ubuntu 已启动，桌面能运行**；尚未在板上核对发行版版本、内核及最终烧录镜像文件名。
- 范围：本记录只涉及 Orange Pi 5 Plus 上电、TF 卡系统启动及初步连接，不代表视觉程序、STM32 或整机分拣已部署或联调。

## 设备与接法

- 板卡：用户确认是 Orange Pi 5 Plus。
- 启动介质：64 GB TF 卡。用户最初下载 Joshua Riek 的 Ubuntu 22.04 桌面镜像；最终成功烧录的镜像文件名**未核实**，不能据此断定板上一定是该镜像。
- 镜像下载入口：用户提供的 [Orange Pi 5 Plus 镜像下载页](https://www.fujianleji.com/orange/Orange_Pi_5_Plus_download.html?utm_source=chatgpt.com)。2026-11-08 只读查看页面可见“ubuntu镜像”等入口，Ubuntu 入口通向百度网盘；此 URL 是下载页面，**不是单个 `.img` 文件直链**。未核实网盘中的具体文件、最终写卡文件名或 SHA-256，不把早先校验过的 Joshua Riek 镜像当作本次实际运行镜像。镜像文件未上传仓库。
- 供电：用户描述使用电池和标称 `UBEC 5V/5A（输入 2–7S）` 降压模块，自行完成接线。实际电池节数、板端接入针脚、输出极性和带载电压没有照片或万用表结果，均待核实。
- 显示：用户后来接上 HDMI 显示器；照片显示 `orangepi` 图形桌面，2026-11-08 又明确反馈 Ubuntu 桌面能运行。

## 过程与验证

| 阶段 | 观察或证据 | 结论 |
| --- | --- | --- |
| 镜像准备 | Windows 上下载的 `.img.xz` 的 SHA-256 与发布方校验文件一致 | 仅证明当时下载文件完整；不证明最终使用的是该镜像 |
| 首次写卡 | Etcher 选中约 62.5 GB USB 目标，第一次在验证阶段失败 | 该次不能算烧录成功 |
| 后续写卡 | 用户后来报告 Etcher 验证成功 | **用户反馈烧录验证成功**；未保存 Etcher 日志或卡的逐字节复核结果 |
| 首次供电 | 用户观察到先红灯、后蓝绿色灯；当时还没接 HDMI 或安装系统 | 当时只能确认板卡通电有反应，不能凭 LED 判断系统启动 |
| 桌面运行 | 用户提供已登录图形桌面照片，之后明确确认 Ubuntu 桌面能运行 | **用户实物确认桌面启动成功** |
| 网络连接 | 用户从 Windows 通过网线直连并 SSH 登录板卡；后续外网 IP 和域名 ping 成功 | 远程登录与基本网络链路已由用户实测；细节见[连接记录](../../ai-dialogue/2026-11-07-005-orangepi-no-keyboard-network.md) |

## 当前接续：联网与初始化

- 电脑网线口 `192.168.50.1/24`，板卡 `192.168.50.2`、接口 `enP3p49s0`；用户已从 Windows SSH 登录。电脑开启以太网 IPv4 转发，并建立 `OrangePi` WinNAT，内部网段 `192.168.50.0/24`；助手在电脑只读复查 NAT 为 Active。
- 板卡起初没有默认路由，用户执行 `sudo ip route replace default via 192.168.50.1 dev enP3p49s0` 后，`1.1.1.1` ping 2/2 成功。用户随后在 NetworkManager 连接 `my_Lenovo_computer` 中保存网关 `192.168.50.1`，`nmcli device reapply` 成功，路由显示 `default via 192.168.50.1`；**尚未重启验证持久性**。手动路由命令可作为启动后未出现默认路由时的临时补救，通常无需每次都输入。
- 用户为该连接配置 DNS `223.5.5.5 1.1.1.1`。`example.com` 可解析并 ping 通，但解析到 `198.18.0.37`；电脑上的 VPN 对指定 DNS 服务器的查询也返回该虚拟地址。用户当前不能断开 VPN，不以断开 VPN 为后续前提。
- 板卡日期仍显示 2026-08-31；`curl -I https://example.com` 已到达证书检查，但报 `certificate is not yet valid`。因此不能把 HTTPS 或软件包下载写成已通过；先校准时间并重新测试。`sudo timedatectl set-ntp true` 已执行，随后日期仍未同步。
- 用户询问如何将桌面语言设为中文。**尚未执行语言包安装、locale 更改或重启验证**；需先用 `cat /etc/os-release` 核实板端发行版，再给出相应命令。早先下载的 Ubuntu 镜像不能代替板端实测。

## 分支与合并时机

- 当前远端分支有 `main`、`codex/vision-yolo`、`codex/orangepi-bringup`；初始化记录继续放在后者。用户计划等香橙派彻底初始化、整理完成后，**在正式开发 YOLO 和部署模型之前**再合并三条开发主线；目前不创建合并提交，也不把本分支当作已经进入 `main`。

## 待核实与后续文件

- 完整的设置顺序、命令、环境划分和验收清单见 [Orange Pi 5 Plus 初始化与规范使用手册](../../docs/orangepi-5-plus-initialization-guide.md)。该文档是后续执行指南，不新增板端实测结论。
- 在板上执行 `cat /etc/os-release`、`uname -r`，记录实际发行版和内核；不要用下载文件名替代板上实测。
- 用万用表和实物接线照片核对 UBEC 带载输出、极性、接头与线材温升。当前只记录用户描述，不把供电长期稳定性写成已验证。
- 板上日期在后续网络调试中曾落后，HTTPS 因证书日期报错；网络和时钟问题见[连接记录](../../ai-dialogue/2026-11-07-005-orangepi-no-keyboard-network.md)。
- 后续可复现的板端脚本、依赖清单和配置模板放 `software/orangepi-5-plus/`；不提交 TF 卡镜像、虚拟环境、运行日志、密码或机器专属配置。

相关过程：[烧录与供电记录](../../ai-dialogue/2026-11-07-004-orangepi5plus-ubuntu-flash-guide.md)、[网线直连与 SSH 记录](../../ai-dialogue/2026-11-07-005-orangepi-no-keyboard-network.md)。
