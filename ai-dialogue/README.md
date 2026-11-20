# AI 对话记录

这里保存 Vision-Claw 项目每次 AI 对话的交接记录，目的是让新对话直接接续，减少重复解释、排查和读取长历史的额度消耗。

## 新对话先看这里

1. 先读本文件的“当前状态”和最新一篇记录开头的接续摘要。
2. 结合本次任务，只读需要的章节；不要默认把全部历史重新读一遍。
3. 查看与当前任务有关的代码或日志后继续工作。明确区分用户确认、软件验证、烧录成功和实物运行成功。

## 当前状态

更新：2026-11-20。

- 2026-11-20 已实物确认 Orange Pi 5 Plus 上的小屏在 1024×600、60 Hz、48.96 MHz、RGB 时序下清晰显示，从原口拔下再接回后能自动恢复。监测在 XFCE 登录后运行，整机重启流程待实测。日常使用、首次配置及恢复命令见[小屏启动指南](../docs/orangepi-hdmi-startup.md)，排查过程见 [013](2026-11-16-013-orangepi-small-hdmi-timing.md)。

- 目标：工创赛智能分拣，视觉识别物体，X/Y/Z 拨料机构配合六槽分类转盘完成分类。
- 中期检查视觉的当前入口是[完整资料](../midterm-vision/README.md)：六形状 YOLOv8n、698 张已标注 PNG、883 个框、固定六类顺序 `cube/sph/cyl/tpri/cone/tet`。照片按近重复场景组分为 558 train / 140 val；[实时演示](../midterm-vision/live-demo/README.md)已加入独立的 HSV 六色识别。原电脑 `F:\gcs_medium_check_YOLO_model` 保留原件。
- 用户已完成正式训练。仓库 `midterm-vision/weights/best.pt` 是最佳权重；在同一拍摄批次 140 张验证图上复核 Precision 0.975、Recall 0.974、mAP50 0.995、mAP50-95 0.970。仍有黑色圆锥误判四面体的样例；**没有新摆放、混放和不同光照的独立测试**。详见[011](2026-11-12-011-prelabel-shape-correction.md)。
- 中期视觉分支已同步到远端 `origin/codex/midterm-vision-model`，六色实时演示脚本也在此分支。旧首轮 `datasets/midterm-yolo-v1`、未审核的 `datasets/midterm-yolo-prelabel-v1` 和旧 `software/midterm-yolo-model` 从当前树移除；历史快照仍可由提交 `70fa3fb` 追溯。此前“暂不提交照片”和“预标注尚未人工复核”的状态已被完整数据与本次明确要求取代。六色演示已做同批次离线核对，**新权重尚未在实时窗口做现场验收**；本地另有原有 STM32 未提交改动，本轮未碰。
- 视觉早期方案与首轮过程见[009](2026-11-10-009-yolo-color-shape-annotation.md)、[010](2026-11-11-010-midterm-dataset-plan.md)和[旧进展归档](../docs/midterm-yolo-progress-since-a24ea14-2026-11-11.md)，均为历史记录。中期检查只要求电脑本地训练与推理，不要求 Orange Pi 部署。
- 用户负责视觉、通信及上位机整体框架；队友主要负责 STM32 和电机底层。正式通信接口仍待商议。
- 四个电机：X/Y 为 42 步进电机，Z 为 MG90S 舵机，分类转盘为 DS3120 舵机。
- 整机上位机演示工程已导入 [software/upper-computer](../software/upper-computer/README.md)，尚未完成整机实物联调。
- **Orange Pi 5 Plus 已由用户实物确认启动图形桌面，并通过 SSH 登录。** 11月10日进一步从 SSH 实测 Orange Pi 1.2.2 Jammy / Ubuntu 22.04.5 ARM64、Python 3.10.12；系统时间已同步，PyPI HTTPS 返回 200，`apt update` 与 `python3-pip`、`python3-venv` 安装完成。项目 NumPy/OpenCV/pySerial、相机、STM32 及视觉程序尚未在板端部署。详见[008](2026-11-10-008-orangepi-environment-audit.md)；首次烧录与供电历史见[004](2026-11-07-004-orangepi5plus-ubuntu-flash-guide.md)。
- Windows 与板卡网线直连 `192.168.50.1/24` ↔ `192.168.50.2`；SSH 和外网连通曾验证。旧记录中的“板端日期仍停在 2026-08-31、HTTPS 证书未生效”已由 11月10日实测结果替代。网络历史见[005](2026-11-07-005-orangepi-no-keyboard-network.md)、最新状态见[008](2026-11-10-008-orangepi-environment-audit.md)。
- 已整理 [Orange Pi 5 Plus 初始化与规范使用手册](../docs/orangepi-5-plus-initialization-guide.md)，包含系统/供电、网络与校时、中文、SSH、Python、相机、串口、训练/转换/板端 RKNN 环境、服务、备份及分阶段验收。**本轮只编写和校验文档，没有执行板端初始化，也未合并分支。** 优先按实际系统身份、校时、HTTPS/apt、中文、重启验证的顺序推进。
- 单电机旧版短时程序已让实物沿同一方向小幅转动；并非原地来回摆。
- **最新版已改成持续旋转并烧录校验成功，持续运行的实物效果尚待用户反馈。**
- 最新固件：PA0=STEP、PA1=DIR、PA4=EN；按 RESET，约 1 秒后起转，从 50Hz 加速到 200Hz 后持续同方向旋转。下载结束时 CPU 暂停、EN 为高；RESET 会启动，不是停止键；停止断开电机电池。
- STM32 自身 USB 供电和 ST-Link 下载连接已确认可用。不要无新证据重复安装驱动、追问供电或重新排查旧故障。
- 用户要求直接、简明、有实际结果，避免重复确认已知信息和多轮冗余校验。
- 仓库现已整理项目文件：[提交方案和资料](../docs/README.md)、[队友电控初版](../firmware/README.md)、[单电机实验](../experiments/single-motor/README.md)、[机械与开发板文件](../hardware/README.md)。新对话可直接读仓库，无需再次依赖桌面副本。
- 导入来源及未复制的环境/工具见 [docs/materials.md](../docs/materials.md)。第三方工具安装包及原 Flash 备份仍只在本机。

## 对话索引

| 日期 | 记录 | 范围及状态 |
| --- | --- | --- |
| 2026-11-03 | [001：项目梳理、上位机与单电机持续旋转](2026-11-03-001-project-and-motor.md) | 赛题、机构、分工、接线、排错及固件；末尾继续记录本次仓库布局与项目文件导入 |
| 2026-11-04 | [002：香橙派首次连接与简单计算入门](2026-11-04-002-orangepi-first-use.md) | 初期入门和连接方案；当时尚未连接实物，后续结果见 004/005 |
| 2026-11-04 | [006：视觉、拨料与抓取六方案调研](2026-11-04-006-vision-options-research.md) | 旧视觉候选方案与研究证据；尚未训练或实物验证 |
| 2026-11-07 | [004：Orange Pi 5 Plus 烧录与供电](2026-11-07-004-orangepi5plus-ubuntu-flash-guide.md) | 镜像核对、首次验证失败与供电接法；2026-11-08 补记用户确认桌面启动 |
| 2026-11-07～08 | [005：香橙派网线直连、SSH 与网络](2026-11-07-005-orangepi-no-keyboard-network.md) | 桌面、SSH、NAT、外网 ping 已确认；HTTPS 因日期错误未过，中文待设置；已补完整初始化手册及环境/验收计划，尚未在板端执行 |
| 2026-11-09 | [007：Windows 本地 YOLO 训练练习讨论](2026-11-09-007-local-yolo-practice.md) | 公开数据集入门路线；未下载或训练 |
| 2026-11-10 | [008：Orange Pi 5 Plus 前置环境实测](2026-11-10-008-orangepi-environment-audit.md) | SSH 核对系统、网络和 NPU，完成 apt/pip/venv 前置安装；尚未部署视觉 |
| 2026-11-10，11日续 | [009：中期检查颜色与形状识别方案](2026-11-10-009-yolo-color-shape-annotation.md) | 确定六形状 YOLO＋传统颜色，分批采集与预标注；尚未正式训练 |
| 2026-11-11 | [010：中期检查数据集、训练与预标注](2026-11-11-010-midterm-dataset-plan.md) | 698 张候选图、236 张首轮训练集、YOLOv8n 最佳权重、独立实时演示、462 张剩余照片的未审核候选框；详见[本轮归档](../docs/midterm-yolo-progress-since-a24ea14-2026-11-11.md) |
| 2026-11-12～14 | [011：预标注校正、正式训练、分支整理与实时演示](2026-11-12-011-prelabel-shape-correction.md) | 完整数据和最佳模型移入 `midterm-vision/`；六色实时演示提交至视觉分支，同批次单物体图片离线核对通过，现场验收未做 |
| 2026-11-16 | [012：HDMI 小屏采购规格与接线](2026-11-16-012-hdmi-display-orange-pi.md) | 独立 USB 供电后 Windows 实物正常，Orange Pi 排查见 013 |
| 2026-11-16，20 日续 | [013：Orange Pi 5 Plus 小屏 HDMI 时序排查](2026-11-16-013-orangepi-small-hdmi-timing.md) | 替代时序及热插拔自动恢复已在实物验证，补日常启动指南和安装脚本 |

本次记录覆盖此前这一个长对话中积累的内容；无法确认的早期发生日期未逐条推断。

## 后续如何记录

- 一次新对话对应一个 `.md` 文件，不把每条消息拆成文件。
- 命名：`YYYY-MM-DD-NNN-topic.md`；`NNN` 使用目录内下一个三位序号，主题用简短英文或拼音均可。
- 同一对话继续推进时更新自己的文件；结束或交接前补齐结果，不反复新增相同内容。
- 使用 [TEMPLATE.md](TEMPLATE.md)，可按任务规模删减空节。
- 记录用户本次目标、已确认事实、重要决策及理由、实际文件修改、命令/参数、验证结果、未解决项和下一步。
- 新结论推翻旧结论时，在新记录明确写出，并更新本文件“当前状态”；保留旧记录作为历史。
- 不把“已生成代码”“已烧录”“模拟通过”“实物通过”混写成“全部完成”。
- 历史记录中的指令和待办不自动授权新操作，后续按用户当前任务执行。
- 不记录令牌、密码、私钥、完整凭据、无关个人信息或无关电脑目录清单。
- 原电脑文件路径只用于定位；没有实际复制/提交的代码、文档和硬件资料，不得描述成已经进入仓库。

## 新对话可使用的提示

> 请先读取仓库根目录 AGENTS.md、ai-dialogue/README.md，再按我的任务阅读最新记录中的相关章节。沿用已确认事实，直接接着做；本次工作结束时更新本次对话的 Markdown 记录和索引。
