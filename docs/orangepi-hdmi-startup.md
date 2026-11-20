# Orange Pi 5 Plus 小屏启动指南

适用设备为项目的 7 寸 1024×600 HDMI 小屏和运行 Ubuntu 22.04（XFCE / X11）的 Orange Pi 5 Plus。现用板卡已配置。

## 日常开机

1. 用已验证的插排 USB 给小屏供电，屏幕输入选 **HDMI**。
2. 将 HDMI 线接到板卡此前验证过的 **HDMI OUT**（系统里是 `HDMI-1`）。板上另有标作 **HDMI IN** 的输入口。
3. 给香橙派上电，等 XFCE 桌面登录后再等几秒。小屏应以 **1024×600、60 Hz** 显示桌面。登录前可能暂时无信号。

桌面运行时，拔下 HDMI 再插回原口，等几秒即可恢复。已在实物上验证拔插后的自动恢复。

## 换卡或重装后的首次配置

在**香橙派**上以桌面用户 `orangepi` 登录。在已下载的 Vision-Claw 仓库根目录执行一次：

```sh
sh software/orangepi-display/install.sh
```

下次登录 XFCE 时会自动启动监测。如果当前已登录桌面但小屏黑屏，可以从 SSH 立即恢复画面：

```sh
DISPLAY=:0 XAUTHORITY="$HOME/.Xauthority" "$HOME/.local/bin/vision-claw-display.sh"
```

已验证脚本在当前桌面的恢复效果和热插拔行为。整机重启后从登录到自动点亮的流程还没实测。

## 黑屏时快速检查

在香橙派的 SSH 里执行：

```sh
cat /sys/class/drm/card0-HDMI-A-1/status
DISPLAY=:0 XAUTHORITY="$HOME/.Xauthority" xrandr --current
```

- 显示 `disconnected` 时，检查小屏的 USB 供电、HDMI 线和板卡输出口。
- 显示 `connected` 且 `1024x600_GTF60 60.00*` 在 `HDMI-1` 下时，正确时序已选中。如果仍无信号，先检查屏幕输入源和接线。
- 如果当前是 `1024x600 59.82*+`，板端回到了这块小屏的默认时序。运行上面的 SSH 恢复命令，再确认当前模式变为 `1024x600_GTF60`。

默认时序和可用时序的分辨率相同，但像素时钟不同。板端日志显示，默认的 50.25 MHz 时序会导致 HDMI 物理层启动失败。替代时序使用 48.96 MHz 和 RGB，已实物确认清晰显示。[排查与验证记录](../ai-dialogue/2026-11-16-013-orangepi-small-hdmi-timing.md)
