# 008：Orange Pi 5 Plus 前置环境实测

- 记录日期：2026-11-10，Asia/Singapore。
- 对话编号：008。
- 关联仓库：Vision-Claw；本机工作分支 `main`，只读抓取远端 `origin/main` 供核对，未合并。
- 相关历史：[005 网线直连与时间问题](2026-11-07-005-orangepi-no-keyboard-network.md)、远端 `docs/orangepi-5-plus-initialization-guide.md`。
- 本次状态：已通过 SSH 实测基础环境；随后按用户明确要求完成 apt 更新和 Python 基础包安装，未部署项目或接入相机、STM32。

## 接续摘要

- Windows 到 `orangepi@192.168.50.2` 的 SSH 密码登录成功。实测系统是 Orange Pi 1.2.2 Jammy / Ubuntu 22.04.5 LTS、ARM64、内核 `6.1.99-rockchip-rk3588`，设备树为 `RK3588 OPi 5 Plus`。
- Python 3.10.12 已有；开始检查时缺 `pip` 和 `python3-venv`，随后已安装并验证。项目所需 `numpy`、`cv2`、`serial` 尚未安装。`git`、`curl`、`gcc`、`v4l2-ctl` 已有。
- 板上时间现在为 2026-11-10，`timedatectl` 显示已同步、NTP active；旧记录中 2026-08-31 导致 HTTPS 证书错误的当前状态已改变。`curl -I https://pypi.org/simple/pip/` 返回 HTTP 200；本次 apt 更新及安装下载成功。
- 当前没有 USB 相机的视频采集节点 `/dev/video0`，也没有 `/dev/ttyUSB*`、`/dev/ttyACM*` 或 `/dev/serial` 串口设备。用户属于 `video`、`dialout` 组。没有运行相机采集或发串口命令。
- NPU 设备在 `/sys/class/devfreq/fdab0000.npu` 出现，启动日志有 RKNPU 记录，`/lib/librknnrt.so` 存在；Python `rknnlite`/`rknn` 不存在，尚无模型推理验证。不能因 `/dev/rknpu` 未出现就断定内核驱动不存在。
- 用户第一次 `sudo apt update` 时，未使用的 Docker 软件源因缺签名公钥报 `NO_PUBKEY 7EA0A9C3F273FCD8`。确认 Docker 未安装后，将 `/etc/apt/sources.list.d/docker.list` 改名为 `docker.list.disabled`；重新运行 `sudo apt update` 成功，没有绕过签名校验。
- `sudo apt install -y python3-pip python3-venv` 成功，系统和临时虚拟环境中的 pip 均可运行。YOLO/RKNN Lite 等到有模型和版本匹配方案再装。当前上位机 README 和 `.cmd` 面向 Windows，板端部署尚未实现。

## 用户本次目标与约束

确认已连接的 Orange Pi 5 Plus 前置环境，例如 Python，以及按项目进度判断还需安装什么。用户随后明确要求把 `sudo apt update` 和 `sudo apt install python3-pip python3-venv` 完成。未要求启动硬件、烧录或部署完整项目。用户提供登录信息仅用于本次 SSH，密码不写入记录或仓库。

## 本次新增或确认的事实

| 项目 | 实测结果 |
| --- | --- |
| 系统/架构 | Orange Pi 1.2.2 Jammy，Ubuntu 22.04.5 LTS，`aarch64` / `arm64`，内核 `6.1.99-rockchip-rk3588` |
| 板型 | 设备树 `RK3588 OPi 5 Plus` |
| Python | `/usr/bin/python`、`/usr/bin/python3`；Python 3.10.12。检查开始时缺 `pip`/`venv` 包；本次安装后系统 `python3 -m pip` 为 22.0.2，临时虚拟环境中的 pip 也可运行 |
| Python 项目包 | `numpy`、`cv2`、`serial`、`ultralytics`、`torch`、`rknnlite`、`rknn` 均未找到 |
| 基础工具 | Git 2.34.1、curl、gcc、v4l2 工具可用；`python3-dev` 已安装 |
| 存储/内存 | 根分区 57G，已用 5.1G、可用 51G；内存 7.7GiB，检查时可用约 7.0GiB；Swap 3.9GiB |
| 时间/网络 | `timedatectl` 为时钟已同步、NTP active；默认路由经 `192.168.50.1`；PyPI HTTPS 返回 HTTP 200 |
| 外设 | `lsusb` 未列出 USB 相机或串口转接器；无 `/dev/video0` 与 USB/ACM 串口节点。`/dev/video-dec0` 和 `/dev/video-enc0` 是已有视频编解码节点，不作为相机成功证据 |
| NPU | sysfs 与内核日志可见 NPU，系统有 `librknnrt.so`；未实测 RKNN Python API 或模型 |

远端 `origin/main` 当前为 `a3b1ccc24e4f5528588b87f84bb4277774520a17`，`software/upper-computer/requirements.txt` 仍为 `numpy>=2.0,<3`、`opencv-python>=4.10,<6`、`pyserial>=3.5,<4`。本机工作树有此前未提交内容，未执行拉取合并或覆盖；远端初始化手册与首次上电记录仅通过 `git show origin/main:...` 查阅。

## 决策与方案

1. 用户第一次 `sudo apt update` 的报错来自未使用的 Docker 软件源。确认 Docker 未安装后，把 `/etc/apt/sources.list.d/docker.list` 改名为 `.disabled`，保留原配置以便后续需要 Docker 时按[Docker 官方说明](https://docs.docker.com/engine/install/ubuntu/)配置签名密钥并恢复。未绕过 apt 签名校验。
2. 重新执行 `sudo apt update` 成功；`sudo apt install -y python3-pip python3-venv` 成功。刷新包索引后的安装计划是新增 6 包，将 7 个 Python 3.10 相关包从 `3.10.12-1~22.04.17` 更新至 `.18`。没有执行全系统 `apt upgrade`。
3. 部署项目时在板端使用独立虚拟环境，逐项验证 NumPy、OpenCV、pySerial 的 ARM64 兼容版本；不要直接运行 Windows `.cmd`。当前仓库尚无已验收的板端依赖锁定与启动脚本。
4. 相机和 STM32 接上后再检查设备节点、权限和实际采集/通信。当前 `video`、`dialout` 组已具备，但不能代替外设实测。
5. RKNN 模型转换与板端推理按实际模型再配套选择工具链、Lite2 wheel 和 Runtime 版本；已有 NPU 内核/共享库不等于推理验收。[Rockchip 官方 RKNN 说明](https://github.com/airockchip/rknn-toolkit2)。
6. 目前不建议为了环境清单直接安装 ROS、Docker、全套 PyTorch/YOLO 或改动厂商内核；Windows 训练和板端推理是后续不同阶段。

## 文件与实际修改

| 路径 | 修改 | 实际状态 |
| --- | --- | --- |
| `ai-dialogue/2026-11-10-008-orangepi-environment-audit.md` | 新增本次实测记录 | 已落盘，未提交 |
| `ai-dialogue/README.md` | 更新当前状态和索引 | 已落盘，未提交 |

板上已禁用未使用的 Docker apt 源，执行 apt 更新及 Python 基础包安装；未部署项目、重启、相机读帧、串口写入或电机操作。本机只执行了 Git fetch 更新远端跟踪引用，没有合并或改动项目源码。

## 验证与证据

- SSH 登录成功，执行 `cat /etc/os-release`、`uname`、设备树、`python3 --version`、`python3 -m pip --version`、Python `importlib.util.find_spec`、`dpkg-query`、`df`、`free`、`timedatectl`、`ip -4 route` 等只读命令。
- `curl -IsS --max-time 8 https://pypi.org/simple/pip/`：HTTP/2 200，证明本次 PyPI HTTPS 可达。
- `v4l2-ctl --list-devices`：无法打开 `/dev/video0`；`lsusb` 与设备节点检查无相机或 STM32 串口证据。
- `ls /sys/class/devfreq`、`ldconfig -p`、`journalctl -k -b`：看到 NPU 节点、`librknnrt.so` 和 RKNPU 启动记录；未执行模型推理。
- 首轮 `apt-get -s install` 是模拟；后续用户明确要求安装后，`sudo apt update` 成功，`sudo apt install -y python3-pip python3-venv` 下载 16.3 MB 包并完成配置。
- `dpkg-query` 显示 `python3-pip`、`python3-venv`、`python3.10-venv` 均为 `install ok installed`；系统 `python3 -m pip --version` 返回 22.0.2。
- `python3 -m venv` 临时创建环境后，其中的 `python -m pip --version` 返回 22.0.2，检查退出码 0；临时环境已删除。`sudo apt-get check` 退出码 0。

## 未解决的问题与下一步

- Python 基础包已安装；OpenCV/NumPy/pySerial 的板端版本及项目运行仍需在后续部署时实测，现有要求面向 Windows 原型。
- Docker 软件源当前处于禁用状态；如以后需要 Docker，按官方文档配置其签名密钥后再启用，不能直接绕过签名校验。
- 相机、STM32 尚未连接；真实视觉与串口联调要等接线和正式协议确认。
- RKNN Runtime 的具体版本及模型兼容性尚未核实，尚无 `.rknn` 模型推理测试。
- 旧记录中时间错误已被本次同步状态替代；是否在后续断网冷启动仍能保持准确时间，未验证。
