# Vision-Claw

工创赛智能分拣项目：视觉识别、上位机通信及分拣机构控制。

Bai.Y.M,school of Computer Science and technology,HUST

## 从哪里开始

- 看提交的方案：[team.pdf](docs/competition/team.pdf)。
- 看队友的电控初版：[电控框架说明](firmware/README.md)，原始设计和源码在其下方目录。
- 运行上位机：[software/upper-computer](software/upper-computer/README.md)。
- 查看已经烧录过的单电机实验：[experiments/single-motor](experiments/single-motor/README.md)。
- 查看 Orange Pi 5 Plus 首次上电和桌面启动：[实物记录](experiments/orangepi-5-plus/2026-11-08-first-boot.md)。
- 启动项目的 7 寸 HDMI 小屏：[接线、开机和首次配置](docs/orangepi-hdmi-startup.md)。
- 找采购清单、架构图和命题草稿：[资料索引](docs/README.md)。
- 找机械模型和开发板封装：[硬件资料](hardware/README.md)。
- 换新 AI 对话接着做：[当前状态与对话索引](ai-dialogue/README.md)。

## 仓库布局

```text
Vision-Claw/
├── README.md
├── AGENTS.md                         AI 协作和对话记录约定
├── ai-dialogue/                      每次对话的摘要、详细记录和模板
├── docs/
│   ├── README.md                     项目资料入口
│   ├── materials.md                  导入来源及版本说明
│   ├── competition/                  team.pdf、命题文档草稿
│   ├── procurement/                  材料申购清单
│   └── architecture/                 队内系统架构图
├── software/
│   └── upper-computer/               Python 上位机、视觉、协议、模拟器与测试
├── firmware/
│   ├── README.md                     电控初版的范围和接入关系
│   └── stm32-motion-framework/       队友原始 Core/、设计文档和说明
├── experiments/
│   ├── single-motor/                 STM32 + A4988 持续旋转实验、固件及验证
│   └── orangepi-5-plus/             板卡首次上电与桌面启动记录
└── hardware/
    ├── README.md
    ├── stm32f407-mini/               开发板符号/封装资料
    └── mechanical/                   SolidWorks 装配体和零件
```

## 当前能做什么

上位机默认使用模拟 STM32 和合成图片，可运行识别、通信和分拣调度演示。第一次克隆后先在 `software/upper-computer/` 运行 `一键安装环境.cmd`，再运行 `启动程序.cmd`。命令行及测试方式见该目录 README。

队友的 STM32 初版仍是需要接入 CubeMX/HAL 工程的双轴控制框架。上位机的演示协议与队友当前文本命令不同，正式接口仍待双方商议，尚未完成整机实物联调。

单电机实验已完成实物短时转动；最新版持续旋转固件已烧录校验成功，持续运行的实物效果待反馈。其引脚为 PA0=STEP、PA1=DIR、PA4=EN，具体接线、启动和停止方法见实验说明。

## 文件与环境

源码、方案和硬件资料已按上述目录导入，原桌面文件保留。虚拟环境、第三方 OpenOCD/驱动包、运行日志和原 Flash 备份不纳入版本控制；Python 依赖及工具准备方式记录在各工程 README。

采购数量、草稿中的分类/尺寸、示例 GPIO 和调试默认值不等于最终实物参数。当前状态以 [对话索引](ai-dialogue/README.md) 为入口，历史记录中的旧路径可通过 [导入清单](docs/materials.md) 对应到仓库路径。
