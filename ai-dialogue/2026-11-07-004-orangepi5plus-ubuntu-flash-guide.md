# 004：Orange Pi 5 Plus Ubuntu 22.04 TF 卡烧录指导

- 记录日期：2026-11-07，Asia/Singapore。
- 对话编号：004。
- 关联仓库：Vision-Claw。
- 相关历史记录：[002 香橙派首次连接](2026-11-04-002-orangepi-first-use.md)。
- 本次状态：本记录前半段记述初次烧录与上电阶段；后续用户确认 Etcher 验证成功、Ubuntu 桌面可运行。最终镜像文件名与供电电压未实测，见文末更新。

## 接续摘要

- **2026-11-08 最新反馈**：用户明确确认 Orange Pi 5 Plus 上的 Ubuntu 已启动、桌面能运行；首次上电与后续网络证据整理在[首次上电记录](../experiments/orangepi-5-plus/2026-11-08-first-boot.md)。以下“未装系统”“验证失败”均是此前阶段状态，不能当作当前结果。
- 用户准备给香橙派安装 Joshua Riek 的 Orange Pi 5 Plus 专用 Ubuntu 22.04 桌面版，Windows 电脑通过读卡器插了 64 GB TF 卡。
- 本机下载目录中的 `ubuntu-22.04-preinstalled-desktop-arm64-orangepi-5-plus.img.xz` 存在，大小 1,654,591,676 字节，SHA-256 与发布方提供的校验值一致。
- Windows 检测到磁盘 1 为 `Generic STORAGE DEVICE`，USB，62,534,975,488 字节，分区盘符 G:，卷标 Biwin；系统盘是磁盘 0，约 1 TB NVMe。磁盘 1 是本次 TF 卡候选设备，实际烧录界面仍需用户核对容量和设备。
- 历史只记为“香橙派 5（8GB）”；本次用户随后明确确认实体板是 **Orange Pi 5 Plus**，此前的型号疑问已解决。
- 镜像项目说明 `.img.xz` 可直接用 balenaEtcher/USBimager 烧录并验证；Ubuntu 桌面版第一次配置需 HDMI 显示器。

## 用户本次目标与约束

用户想知道已下载系统镜像且 TF 卡已插入 Windows 电脑后的下一步。当前请求是操作指导，尚未要求助手直接写入 TF 卡或启动硬件。

## 本次新增或确认的事实

- 用户给出的原电脑路径：`C:\Users\Lenovo\Downloads\ubuntu-22.04-preinstalled-desktop-arm64-orangepi-5-plus.img.xz`；文件在仓库外，没有复制到仓库。
- 用户后续明确确认板子是 Orange Pi 5 Plus，并发来 balenaEtcher 下载页截图，询问该页如何选择。截图第一行是 `ETCHER FOR WINDOWS (X86|X64) (INSTALLER)`；指导点击这一行右侧 Download。该 Windows 架构描述的是电脑端 Etcher 安装器，不影响给板卡烧录 ARM64 系统镜像。
- 用户最新截图显示 Etcher 已安装运行，界面左侧已选 `ubuntu-22...-plus.img`、显示 7.71 GB，右侧已选 `Generic S...SB Device`、显示 62.5 GB，按钮为“现在烧录！”。目标容量与之前 Windows 检测到的候选 TF 卡一致；截图未显示完整镜像路径或写入完成结果。
- 用户之后报告烧录失败，并明确是 **验证阶段** 失败。不能将此前写入视为可用系统或烧录成功。
- 用户转问 Orange Pi 5 Plus 的电池、供电模块与外接显示器接法；已有模块为“UBEC 5V5A (2-7S)”。其标称 5V/5A 输出在电压电流额定值上满足板卡 5V/4A 要求，但电池节数/电压、输出接头、线序和稳压情况尚未核实，不能据此直接指导接线通电。用户确认有显示器。
- 用户补充 UBEC 一侧是红黑裸线、带两个类似电容的元件，猜为高压输入；另一侧是红黑杜邦母头，猜为 5V 输出，询问如何对接板卡 Type-C。仅凭外观不能确认输入/输出，需看模块 IN/OUT 标识与电池参数；杜邦母头不能直接插 Type-C。官方虽允许合规 5V 线给 40pin 供电，但这组未核实的普通杜邦线不作为 4A 供电方案推荐。
- 用户明确没有 Type-C 适配器，希望用现有 UBEC/电池，询问是否能焊接。重新核对 Orange Pi 5 Plus 厂商手册：**40pin 的 5V/GND 确实可作为供电输入**，手册示例为红黑杜邦线接入，并强调电源线需满足供电要求与不得反接。因此此前一概说普通杜邦线不能用于供电过于绝对；正确表述是：物理上可用现有输出接头走 40pin，条件是确认 UBEC 输入输出、电池范围、实际 5V 极性及线材承载能力，不能仅凭颜色或电容位置猜测。
- 用户提供一张 Orange Pi 5 Plus 正面产品示意图并说实体板正面与图一致。图标注左上为 Type-C 5V/4A 供电、顶部中间两个 HDMI Out、一个 HDMI In，右边竖排为 40pin。该图不展示清晰的排针 1 号针标识或用户实物接线，不能仅凭此图直接给出杜邦线在实际板上的孔位；仍需实物近照、UBEC 标识、电池参数与电压极性实测。
- 用户随后自行接线通电，报告先亮红灯、后亮蓝绿色灯；进一步明确 **未接 HDMI、未装系统**。这只是用户实物观察到板子得电和指示灯变化，不是 Ubuntu 启动成功或供电稳定性验证。用户尚未反馈排针位置照片、UBEC 实测输出电压和线材/模块温升。
- 镜像 SHA-256：`1974a4d1ffeebf868f8527d0e51f6ab63f5da2b4a1a6f24ee6c2f0a38ae61fea`，与 [v2.4.0 发布校验文件](https://github.com/Joshua-Riek/ubuntu-rockchip/releases/download/v2.4.0/ubuntu-22.04-preinstalled-desktop-arm64-orangepi-5-plus.img.xz.sha256) 一致。
- [Orange Pi 5 Plus 下载页](https://joshua-riek.github.io/ubuntu-rockchip-download/boards/orangepi-5-plus.html)对应 Ubuntu 22.04 桌面版/Linux 5.10。该仓库于 2026-04-29 被所有者归档；不据此推断镜像无法使用。
- [项目安装说明](https://github.com/Joshua-Riek/ubuntu-rockchip/blob/main/README.md)说明直接烧录 xz 文件、首启可能约两分钟、桌面版首次设置需 HDMI。
- [Orange Pi 5 Plus 官方产品页](https://www.orangepi.org/html/hardWare/computerAndMicrocontrollers/details/Orange-Pi-5-plus.html)标注独立 5V/4A Type-C 供电；板上有多个 Type-C/HDMI 接口，连接前看丝印区分。
- [Orange Pi 5 Plus 官方 Wiki](https://www.orangepi.org/orangepiwiki/index.php/Orange_Pi_5_Plus)说明供电 Type-C 靠近网口，另一 Type-C 不负责供电；仅接受固定 5V，不支持 PD 协商。板卡有两个 HDMI 输出和一个 HDMI 输入；外接显示器接 HDMI 输出。

## 决策与方案

1. 用户已确认实体板是 Orange Pi 5 Plus；确认 G: 对应的是可清空的目标 TF 卡，烧录会覆盖整卡。
2. Windows 使用 balenaEtcher：Flash from file 选择原 `.img.xz`，Select target 按约 64 GB 容量选择读卡器，Flash 后等待验证通过；无需预解压或预格式化。
3. 安全弹出 TF 卡后，板卡断电插入卡槽；显示器接 HDMI **输出**，接键鼠、独立 5V/4A Type-C 电源；首次启动走桌面向导。
4. 若没有 HDMI 显示设备，桌面版首次向导暂不能按该项目标准流程完成；后续可借显示器或改用同型号 Server 镜像走无屏设置，具体由用户当时选择。

## 文件与实际修改

| 路径 | 修改 | 实际状态 |
| --- | --- | --- |
| `ai-dialogue/2026-11-07-004-orangepi5plus-ubuntu-flash-guide.md` | 记录本次只读核对和操作指导 | 已落盘，未提交 |
| `ai-dialogue/README.md` | 更新当前状态及本次索引 | 已落盘，未提交 |

仓库外镜像没有修改。助手未向 TF 卡写入数据；用户自行用 Etcher 烧录，验证阶段失败，卡的分区结构已被改写。

## 验证与证据

- Windows `Get-Item`、`Get-Disk`、`Get-Partition`、`Get-Volume` 核对本地文件与候选 TF 卡；`Get-FileHash -Algorithm SHA256` 与发布方 `.sha256` 文件对比一致。
- 查阅项目下载页、README、balenaEtcher 官方页面和 Orange Pi 5 Plus 官方产品页。
- 用户已口头确认实体板型号为 Orange Pi 5 Plus；未通过板身照片独立核查。
- 用户实物确认接线通电后指示灯先红后蓝绿色；当时无 HDMI、无系统，不能记为板端启动成功。需后续核实 UBEC 输出电压/极性及线材温升。
- Etcher 已通过用户截图确认安装运行；尚未验证：TF 卡原数据是否已备份、烧录结果、显示器和电源连接、板卡实际启动。
- 验证失败后只读检查：Windows 磁盘 1 仍为 `Generic STORAGE DEVICE`、62,534,975,488 字节、在线、健康、非只读；分区表已变为 GPT，分区 1 约 7.69 GB，说明烧录曾改写卡的分区结构，但不能证明全部写入正确。Etcher 的用户配置目录未找到可用的本次烧录错误日志；近期 Windows System 日志未筛出存储设备错误。不据此排除读卡器、USB 口或 TF 卡问题。
- [Etcher 官方常见问题](https://etcher.balena.io/)建议失败后重试，再换读卡器、卡或 USB 口。原镜像 SHA-256 已匹配，无需优先重新下载。

## 未解决的问题与下一步

首次 Etcher 验证阶段失败。先安全弹出并重插 TF 卡、换电脑 USB 口，重新选原 `.img.xz` 和 62.5 GB 目标烧录一次，须等验证通过才启动板卡；不用先格式化。若再失败，获取完整报错截图，并尝试另一个读卡器或 TF 卡。桌面版首启需 HDMI 显示设备；后续按实际条件继续协助。

供电/显示接续：用户已有 UBEC 5V5A(2-7S) 和显示器。先核对电池节数/电压、UBEC 输出接头与线序，确认后才能给具体电池接线；不将电池原始电压直接送入板卡。显示器自供电，HDMI 线从板卡 HDMI OUT 接显示器，键鼠接板卡 USB。TF 卡验证失败尚不能声称桌面系统能启动。

对接建议更新：用户没有 Type-C 适配器。可走官方允许的 40pin 供电路径，无需先焊 Type-C：UBEC 已核实的 +5V 输出接 40pin 物理针 2 或 4，GND 输出接物理针 6；针脚方向须根据实体板照片确认，不凭口述盲插。先确认电池在 UBEC 2–7S 输入范围、IN/OUT 标识、接线极性、万用表实测约 5V，评估现有输出导线与接头是否可承受板端电流；不同时接其他供电，避免反接。若制作 Type-C 路线，则使用标称支持所需电流的预接线 Type-C 供电尾线并核验 VBUS/GND，不能凭线色剪接任意数据线。厂家手册：[Orange Pi 5 Plus 用户手册](https://orangepi.net/wp-content/uploads/2023/07/OrangePi_5_Plus_RK3588_user-manual_v1.5.1.pdf)，供电与 40pin 章节；[官方 Wiki](https://www.orangepi.org/orangepiwiki/index.php/Orange_Pi_5_Plus)。

可用的厂商手册镜像：[Orange Pi 5 Plus 用户手册 PDF](https://manuals.plus/m/78a40710607e12ea2c0374d621cd2e7a4be3e145542de3c1a8b1fb73c87185ed_optim.pdf)，印刷页 139–140 为 40pin 供电说明和图片；前述 orangepi.net 链接当前在线打开返回 404，后续引用可用镜像或官方 Wiki。用户产品示意图只能确认板型/接口，不能替代实物针脚标记和 UBEC 电压测量。

最新实物状态：用户已接线通电，红灯后出现蓝绿色灯；无 HDMI、无已安装系统。下一步不能依据 LED 认定系统成功；需确认供电无异常发热，并待 TF 卡验证通过后接 HDMI OUT 观察 Ubuntu 首次设置界面。

## 2026-11-08 接续更新

- 上段“无 HDMI、未安装系统”是 2026-11-07 当时的观察。后来用户反馈 Etcher 验证成功，照片显示已登录的图形桌面；2026-11-08 用户再次明确确认 Ubuntu 启动成功且桌面可运行。
- 之前下载的 Joshua Riek Ubuntu 22.04 镜像 SHA-256 匹配发布文件，但最终写入并运行的镜像文件名、板上系统版本均未实测，不能直接认定是该镜像。
- 用户自行接线完成供电；电池节数、UBEC 输出极性与带载电压、线材温升尚无测量证据。LED 变化与桌面运行分别记录，不把灯色当作系统验证。
- 本次已获用户授权将首次上电记录整理到 GitHub 的独立硬件分支；不启动板卡或改动其系统。
