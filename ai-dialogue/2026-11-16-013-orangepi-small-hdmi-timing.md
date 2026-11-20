# 013：Orange Pi 5 Plus 小屏 HDMI 时序排查

- 记录日期：2026-11-16，Asia/Singapore。
- 对话编号：013。
- 相关历史记录：[012](2026-11-16-012-hdmi-display-orange-pi.md)。
- 当前状态为小屏 1024×600@60 Hz 实物显示正常、拔插后自动恢复。整机重启流程待实测。[日常启动指南](../docs/orangepi-hdmi-startup.md)

## 接续摘要

- 用户保持插排 USB 给 7 寸小屏供电，并将 Windows HDMI 改接 Orange Pi 5 Plus；此前小屏红灯、无信号。本次经 `orangepi@192.168.50.2` SSH 登录，确认板端 `HDMI-1` 已检测到小屏及其 EDID，且 EDID 首选 1024×600@59.82 Hz。
- 板端在 EDID 首选时序下，HDMI PHY 报 `hdptx phy lane can't ready`、`phy poweron failed --> -22`、`hdmi set operation mode failed`，小屏保持红灯。仅将色彩格式改成 RGB 没有恢复；用 1280×720@60 Hz、RGB 则 PHY `lane locked`，用户实物确认有画面。
- 再试原 EDID 1024×600@59.82 Hz、RGB，PHY 再次报错。改用 GTF 1024×600@60 Hz、像素时钟 48.96 MHz 后，PHY `lane locked`，用户实物确认小屏清晰显示桌面。因此问题在这块板当前驱动与小屏 EDID 首选 50.25 MHz 时序的组合；这不等于屏幕未被检测或 HDMI 口损坏。
- 已在板卡原电脑远程环境路径 `/home/orangepi/.local/bin/vision-claw-display.sh` 和 `/home/orangepi/.config/autostart/vision-claw-display.desktop` 配置 XFCE 登录后应用该模式。脚本已手动执行、语法检查通过，`xrandr` 显示 `1024x600_GTF60 60.00*`；尚未重启验证自动启动。

## 用户本次目标与约束

查明 Windows 能正常显示、换接 Orange Pi 后小屏无信号的原因，并使 Orange Pi 能在小屏显示。用户给出 SSH 连接方式；密码不记录在本文件中。未请求启动其他项目硬件。

## 验证与证据

- Windows 路由本次经实体以太网 `192.168.50.1/24` 到板卡 `192.168.50.2`，SSH 登录成功；旧记录的 VPN 选路障碍本次已消失。
- `/sys/class/drm/card0-HDMI-A-1/status` 为 `connected`，`edid` 为 256 字节，`modes` 包含 1024×600；`card0-HDMI-A-2` 同时为 `connected`，对应另一台 1080p 显示器。本次操作对象为小屏对应的 X11 `HDMI-1`。
- 初始 `xrandr --verbose`：`HDMI-1` 为 1024×600@59.82 Hz、50.25 MHz，色彩格式 `ycbcr444`。切 RGB 后小屏仍红灯。
- 1280×720@60 Hz、RGB：内核报告 TMDS 74.25 MHz、PHY `lane locked`，用户确认有画面。
- 再切回 EDID 首选 1024×600@59.82 Hz、RGB：内核报告 TMDS 50.25 MHz、PHY `lane can't ready` 和启动失败。
- `gtf 1024 600 60` 给出的替代 Modeline：`48.96 1024 1064 1168 1312 600 601 604 622 -HSync +VSync`。以 `xrandr --newmode/--addmode/--output` 应用后内核报告 TMDS 48.96 MHz、PHY `lane locked`；用户确认原生分辨率清晰显示。

## 文件与实际修改

| 路径 | 修改 | 实际状态 |
| --- | --- | --- |
| 板卡原电脑远程路径 `/home/orangepi/.local/bin/vision-claw-display.sh` | 登录后创建并应用替代 Modeline，设置 `HDMI-1` 为 RGB | 已落盘，手动运行通过 |
| 板卡原电脑远程路径 `/home/orangepi/.config/autostart/vision-claw-display.desktop` | XFCE 自动启动入口 | 已落盘，未重启验证 |
| `ai-dialogue/2026-11-16-013-orangepi-small-hdmi-timing.md` | 本次记录 | 已落盘 |
| `ai-dialogue/README.md` | 当前状态及索引 | 已更新 |

## 未解决的问题与下一步

- 板上还有另一条 SSH 会话，本次未重启以免中断；之后重启可验证 XFCE 自动应用是否稳定。开机到桌面登录前可能短暂红灯，登录后脚本才会应用模式。
- 若以后换显示屏或把小屏改接另一个 HDMI OUT，应重新确认 X11 输出名和模式。当前配置只针对 `HDMI-1`。

## 2026-11-20 续：拔插后自动恢复

- 用户报告小屏接香橙派又不亮，接笔记本则亮。沿用原 SSH 地址登录板卡成功。故障当时 `HDMI-A-1` 已连接、EDID 256 字节，`xrandr` 当前模式又是 EDID 首选 `1024×600@59.82 Hz`，内核在 50.25 MHz 再次报 `phy lane can't ready`。旧脚本只在 XFCE 登录时运行一次，无法在桌面会话内重新接屏后恢复模式。
- 手动运行原脚本后，当前模式切到 `1024x600_GTF60 60.00*`，48.96 MHz 的 HDMI PHY 锁定。用户确认桌面正常。
- 更新板端 `/home/orangepi/.local/bin/vision-claw-display.sh` 和 `/home/orangepi/.config/autostart/vision-claw-display.desktop`，XFCE 登录时启动监测。仅在 `HDMI-1` 接上 EDID 校验值匹配的小屏、当前模式或色彩格式不符时重新应用已验证时序。监测每 2 秒检查一次，随 XFCE 会话结束退出。两份旧文件在板端各保留一份 `.before-hotplug` 备份，板端文件未复制进仓库。
- 新脚本通过 `sh -n`，并在当前桌面会话启动监测。用户保持 USB 供电，拔下 HDMI 再插回原口，实物确认桌面自动恢复。板端日志同步记录 `Applied 1024x600_GTF60 (RGB) to HDMI-1`，`xrandr` 确认该模式为当前模式。此次已完成真实热插拔测试，尚未重启验证登录时自动启动。

## 2026-11-20 续：整理 GitHub 启动指南

- 用户要求把显示变化更新到 GitHub，提供简洁的日常开机步骤。已整理[小屏启动指南](../docs/orangepi-hdmi-startup.md)及[一次性安装脚本](../software/orangepi-display/install.sh)，首页和资料索引均可进入。
- 已实物验证的监测脚本归档为 `software/orangepi-display/vision-claw-display.sh`。安装脚本把它复制到用户目录并注册 XFCE 登录自启。现用板卡在前次排查时已配置。
