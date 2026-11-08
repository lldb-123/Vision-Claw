# 005：香橙派无键鼠时通过网线连接电脑

- 记录日期：2026-11-07，Asia/Singapore。
- 对话编号：005。
- 关联仓库：Vision-Claw。
- 相关历史记录：[004：烧录与供电](2026-11-07-004-orangepi5plus-ubuntu-flash-guide.md)。
- 本次状态：板卡与电脑直连 SSH 已由用户实物确认；Windows NAT 与有线转发已由用户开启。板卡加入默认路由后外网 IP、域名 ping 成功。NetworkManager 已保存网关配置；HTTPS 目前因板卡系统日期仍在 2026-08-31 而报证书“尚未生效”。用户最新要求只提供每次可手动输入的路由命令。
- 2026-11-08 更新：用户再次明确确认 Ubuntu 启动成功、桌面能运行；见[首次上电汇总](../experiments/orangepi-5-plus/2026-11-08-first-boot.md)。最终镜像文件名和板上发行版版本仍待命令实测。本记录的部分“尚未确认”语句是过程中的阶段判断，后文有对应更新。

## 接续摘要

- 用户现在报告“装好香橙派了”，并已连接显示器，完全没有键盘或鼠标，希望 Windows 电脑用网线直连板卡。
- 已确认型号为 Orange Pi 5 Plus。004 中用户曾选择 Joshua Riek Ubuntu 22.04 Desktop 镜像；但本轮用户照片呈现 Orange Pi 壁纸和已登录的 `orangepi` 桌面，最终烧录镜像可能与此前选择不同，尚未核实文件名。
- 用户照片和烧录验证成功的口头确认更新了 004 中“尚未装系统、未接 HDMI”和首次验证失败的旧状态。仍未进行 SSH 实测。
- 曾按此前镜像推断需要 Desktop 首次设置向导，并在只有橙色背景的描述下误判为卡在 Logo；照片证据推翻这两个当前判断。厂商 Wiki 对自家 Linux 镜像说明默认开启 SSH；实际登录状态以这台板的实测为准。
- 用户进一步反馈：画面只有橙色背景或 Logo，没有图标，也没有确认有顶部栏、首次设置窗口或可操作桌面。不能据此认定 Ubuntu 已进入桌面；已询问该画面持续时间。
- 本机只读检查实体以太网适配器为 Disconnected、0 bps，说明网线尚未建立物理连接；尚无板端地址可查。已请用户把网线插到电脑实体网口和板卡网口。
- 用户随后反馈重新插了网线，但复查电脑实体“以太网”仍为 Disconnected、0 bps。已建议改试 Orange Pi 5 Plus 的另一个 RJ45 网口并检查两端网口指示灯；尚未收到换口结果。
- 继续插线后复查电脑实体网口变为 Up、1 Gbps，物理链路已通；照片显示上方有 `Applications` 菜单、状态栏及右上 `orangepi`，中间 Orange Pi 为桌面壁纸。此前将“只有橙色背景”判断为启动卡住是错误推断，已向用户更正。
- 用户明确报告后来 Etcher 烧录显示验证成功，更新 004 的“首次验证失败”旧状态。仍未确定最终烧录的镜像文件名，但照片风格与厂商 Orange Pi 桌面及默认 `orangepi` 账户一致，不能再沿用 Joshua Riek Desktop 必须首次创建用户的假设。
- 用户随后询问如何 SSH 登录。官方 Orange Pi 5 Plus Wiki 说明厂商 Linux 镜像默认启用 SSH；实际镜像及登录凭据是否改动仍需登录实测。仓库不记录密码。
- 用户随后想起已设置固定 IP：电脑 `192.168.50.1`、板卡 `192.168.50.2`，并反馈板卡不能联网。电脑只读核查证实实体以太网为 `192.168.50.1/24`，板卡 `192.168.50.2` ping 2/2 成功、TCP 22 可达；电脑 WLAN 有互联网、以太网 IPv4 Forwarding 为 Disabled，当前直连只满足局域通信，没有证据显示已做 NAT/ICS。
- 用户按指导在管理员 PowerShell 执行 `Set-NetIPInterface -InterfaceAlias "以太网" -Forwarding Enabled` 和 `New-NetNat -Name OrangePi -InternalIPInterfaceAddressPrefix 192.168.50.0/24`，输出显示 NAT Active=True；助手在电脑上只读复查同样显示 NAT 活跃及有线转发 Enabled。该 Windows 设置由用户亲自执行。
- 用户已从 Windows SSH 登录 `orangepi@orangepi5plus`，板卡 `ip -4 route` 起初只有本地 `192.168.50.0/24` 和链路本地网段、没有默认路由；因此 `ping 1.1.1.1` 报 `Network is unreachable`，域名解析也失败。助手建议临时运行 `sudo ip route replace default via 192.168.50.1 dev enP3p49s0`，用户随后回报 ping `1.1.1.1` 两次均成功（约 76 ms）。这验证电脑 NAT 转发到公网 IP 有效，但默认路由命令重启后失效。
- 用户追加板端测试：`ping -c 2 example.com` 解析为 `198.18.0.37` 并 2/2 成功。该 `198.18.0.0/15` 地址不是 example.com 的公网地址，可能是电脑 VPN 的虚拟 DNS/代理地址；虽然解析和 ICMP 通了，仍需 HTTPS 实测才能确认网页访问。`nmcli -g GENERAL.CONNECTION device show enP3p49s0` 返回活动连接名 `my_Lenovo_computer`。
- 用户运行 `sudo nmcli connection modify "my_Lenovo_computer" ipv4.gateway 192.168.50.1 ipv4.never-default no` 和 `sudo nmcli device reapply enP3p49s0`，输出显示应用成功；`ip -4 route` 出现 `default via 192.168.50.1 ... proto static`，连接配置显示 `192.168.50.2/24` 与网关 `192.168.50.1`。该修改已保存到 NetworkManager 连接配置，尚未通过重启实测。
- 之后用户为该连接指定 DNS `223.5.5.5 1.1.1.1` 并 reapply；`getent ahostsv4 example.com` 仍返回 `198.18.0.37`。电脑端分别指定上述 DNS 查询，也都返回该 VPN 虚拟地址，推断电脑 VPN 拦截 DNS。用户明确表示暂时不能断开 VPN；不应再要求关闭 VPN。
- 板卡 `curl -I --max-time 10 https://example.com` 从先前超时变为 `curl: (60) SSL certificate problem: certificate is not yet valid`，说明至少已建立到 TLS 证书检查阶段。板卡 `date` 为 Mon Aug 31 11:12:06 AM CST 2026，与本次日期 2026-11-07 不符；`sudo timedatectl set-ntp true` 后仍未同步。当前 HTTPS 失败的直接可见原因是系统日期错误，不应再表述为单纯“网络不通”。
- 用户最新明确偏好：只要临时路由命令，愿意每次手动输入。应给出 `sudo ip route replace default via 192.168.50.1 dev enP3p49s0`，并说明前述 `nmcli` 网关已经保存，通常下次启动不需要手动重复；不未经要求撤销持久设置。简短提醒时间错误会影响 HTTPS。

## 用户本次目标与约束

解释没有板端键鼠时如何从 Windows 笔记本连接香橙派，优先考虑网线直连。当前是操作咨询，没有要求助手修改 Windows 网络、重新烧录或启动硬件。

## 决策与方案

1. 网络远程控制可省去长期连接板端键鼠，但要求板端已启动、网络可达、SSH 服务可用且有可登录账户；网线本身不会把笔记本键盘变成板端 USB 键盘。
2. 先前针对 Desktop 首次设置所提临时 USB 键盘和重烧 Server 镜像方案，因照片证明系统已进入桌面而不再是当前建议。
4. 网线直连可通过 Windows 的 Internet Connection Sharing（ICS）向板卡分配地址：电脑 Wi-Fi 上网，Wi-Fi 属性的“共享”选择连接板卡的以太网接口。板端厂商 Linux 默认通过 DHCP 获取地址。电脑当前实体以太网持有旧的手动 IPv4 `192.168.1.100/24`；启用 ICS 可能改写该设置，用户应在 Windows 图形界面中操作。目前尚未启用。
5. 照片可见 `orangepi` 已登录桌面。获取板卡 IP 后在 Windows PowerShell 执行 `ssh orangepi@板卡IP`，首次连接核对主机指纹提示并按需确认；凭据由用户自行输入。此条是当时的建议，后续已由用户登录实测。
6. 最新已知 IP 可直接用于 `ssh orangepi@192.168.50.2`。板卡无法联网的已确认电脑端原因是当前有线接口未转发；保留静态 `192.168.50.1/24` 与 `.2` 时需在 Windows 建 NAT，并检查板卡默认网关为 `.1` 和 DNS。Windows ICS 也能共享 Wi-Fi，但通常把电脑有线地址改为 `192.168.137.1`，与当前静态地址不兼容，启用前需调整板端配置。当前不贸然改动现有静态网络。

## 文件与实际修改

- 新增本记录，更新 `ai-dialogue/README.md` 当前状态与索引。
- 未修改项目代码、系统镜像、TF 卡或电脑网络设置；未 commit/push。

## 验证与证据

- 已读取对话索引、004 记录、模板与根目录 AGENTS.md。
- 用户实物描述：板卡已装好、显示器已接、无键鼠；未提供当前画面或远程登录结果。
- 用户随后澄清显示器只有橙色背景或 Logo，没有图标；尚未看到可操作桌面或设置向导。
- 本轮 Windows `Get-NetAdapter` 对实体“以太网”只读检查结果为 Disconnected、0 bps；未读取板端状态，也未改动网络配置。
- 用户报告重新插网线后再次运行 `Get-NetAdapter`，同一实体网口仍为 Disconnected、0 bps；未继续设置 ICS 或尝试 SSH。
- [Orange Pi 官方 Wiki](https://www.orangepi.org/orangepiwiki/index.php/Orange_Pi_5_Plus)核实 5 Plus 有两个 2.5G 以太网口。
- 后续 `Get-NetAdapter` 显示实体“以太网” Up、1 Gbps。Windows 网口现有手动 IPv4 `192.168.1.100/24`，未见板端 IPv4 邻居；扫描该 /24 网段未找到回应，不据此断定板卡无网络。
- Windows 当前进程不是提升权限的管理员；通过 HNetCfg.HNetShare COM 读取共享配置返回 `E_ACCESSDENIED`，因此没有修改 ICS，需用户通过 Windows 图形设置操作或给予管理员确认。
- 用户照片直接证实系统有顶部任务栏、Applications 菜单及已登录的 `orangepi` 用户；更正此前“卡在 Logo”判断。用户口头确认 Etcher 后续验证成功；未查看 Etcher 实际日志。
- [厂商 Wiki](https://www.orangepi.org/orangepiwiki/index.php/Orange_Pi_5_Plus)说明厂商 Linux 镜像默认启用 SSH，有线网默认 DHCP；这是官方文档说明，后续以本板登录实测更新。仓库不记录默认或用户密码。
- Windows `Get-NetIPAddress` 核对实体以太网为静态 `192.168.50.1/24`，WLAN 为 DHCP 并连网；`Get-NetIPInterface` 显示实体以太网 `Forwarding=Disabled`。电脑 ping `192.168.50.2` 2/2 成功（约 2 ms），`Test-NetConnection -Port 22` 为 True。
- 尝试非交互式 SSH 公钥认证返回 `Permission denied (publickey,password)`；这只表明当前电脑公钥未获授权，未验证用户密码登录。未把密码送入工具或记录。
- [Microsoft New-NetNat 文档](https://learn.microsoft.com/en-us/powershell/module/netnat/new-netnat)说明创建 NAT 对象的 `InternalIPInterfaceAddressPrefix` 参数；目前 `Get-NetNat` 未显示对象，且本机进程无提升的管理员权限，未创建 NAT。
- 更新：用户执行后，Windows `Get-NetNat -Name OrangePi` 显示 `192.168.50.0/24`、Active=True；`Get-NetIPInterface` 显示有线转发 Enabled。用户的板端输出证实加入临时默认路由后 `1.1.1.1` ping 2/2 成功。上条“未创建 NAT”仅是此前检查状态，已被本条更新。
- 已查阅 [NetworkManager nmcli 官方文档](https://networkmanager.dev/docs/api/latest/nmcli)：连接配置可修改 `ipv4.gateway`/`ipv4.dns`，`nmcli device reapply` 可尝试将配置应用到当前接口；是否适用于板端需先看设备的活动连接名称。
- 已在线核实 [Ubuntu Rockchip 项目说明](https://github.com/Joshua-Riek/ubuntu-rockchip/blob/main/README.md)：Desktop 首次设置需要 HDMI 向导，Server 可通过 SSH 登录。
- 已核实 [Microsoft ICS 文档](https://learn.microsoft.com/en-us/windows/win32/nativewifi/using-hosted-network-and-internet-connection-sharing)：共享的内部接口提供 DHCP 地址分配。
- 本轮没有扫描网络或尝试登录；不存在“连接成功”的实测结论。

## 未解决的问题与下一步

按用户最新请求仅提供可手动重复的临时默认路由命令。此前 `nmcli` 已写入持久网关，重启后理论上应自动加默认路由，但未重启验证。HTTPS 的独立问题是板端时钟落后约两个月，需用户后续愿意时排查 NTP/校准时间；用户暂不能断开电脑 VPN，不以断开 VPN 为本轮前提。用户自行输入板端 sudo 密码；未记录密码。Windows NAT 已确认，无需重复设置。
