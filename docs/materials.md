# 文件导入来源与版本说明

导入日期：2026-11-03。本次按项目模块复制到仓库，原桌面和下载目录的文件保留。

## 来源映射

| 仓库位置 | 原电脑来源 | 内容 |
| --- | --- | --- |
| `docs/competition/team.pdf` | `C:/Users/Lenovo/Desktop/team.pdf` | 用户指定的已提交方案 |
| `docs/competition/2027年第十届中国工创大赛-任务命题文档模板-智能分拣赛项.doc` | 原电脑 Downloads 同名文件 | 命题/方案草稿 |
| `docs/procurement/附件：智能分拣材料申购清单-戚翰雯.xlsx` | `C:/Users/Lenovo/Desktop/工创赛/` 同名文件 | 原始申购表 |
| `docs/architecture/system-architecture.png` | 本对话用户上传的架构图，原临时附件名 `codex-clipboard-ce92ca71-7b50-4858-bb2c-d46fef0e3e48.png` | 原图，不改像素内容 |
| `firmware/stm32-motion-framework/` | `C:/Users/Lenovo/Desktop/电控框架初版（只有框架版/` | `Core/`、原设计文档和 `README_MOTION.md`，共 8 个原文件 |
| `software/upper-computer/` | `C:/Users/Lenovo/Desktop/智能分拣上位机/` | 应用、配置、测试、协议说明、启动/安装脚本及旧交接 |
| `experiments/single-motor/` | `C:/Users/Lenovo/Desktop/单电机试转/` | 持续旋转汇编、构建和模拟检查、HEX/BIN、下载脚本及说明 |
| `hardware/stm32f407-mini/` | `C:/Users/Lenovo/Desktop/工创赛/STM32F407VET6-Mini开发板封装/` | `.schdoc` 和 `.pcbdoc` |
| `hardware/mechanical/` | `C:/Users/Lenovo/Desktop/工创赛/分拣机/` | 装配体及其 18 个零件文件，保留全部文件名 |

## 保留和调整

- `team.pdf`、命题文档、采购表和架构图按原字节复制并核对 SHA256。
- 电控初版的 8 个设计/源码文件保持原内容，没有借导入之机修改队友控制逻辑。
- 机械文件名不改，包括原来带双句点的零件名，避免破坏装配引用。未使用 SolidWorks 验证装配或修复外部引用。
- 开发板文件是现有符号/封装资料；不能仅凭它们推断完整供电原理图或排针方向。
- 上位机主要更新首次克隆的环境说明；应用逻辑沿用原工程。
- 单电机增加 Python 构建依赖表、工具准备说明及可指定 OpenOCD 路径的下载入口。持续旋转的运动参数不变，本次不重新给实物烧录。
- 上位机内 `项目交接说明.md` 是旧快照，其中原电脑路径和进度以仓库当前说明及对话索引补充。

## 未导入的本机内容

- `.venv/`、Python 缓存和机器相关标定文件：在目标电脑重新安装/生成。
- 运行日志、队友目录下 `tmp/pdfs/` 的渲染截图和重复 PDF：正式原件按资料目录归档。
- 单电机 `tools/` 中的第三方 OpenOCD、Windows 驱动及下载包：从实验 README 指向的来源准备。
- `original_sector0.bin`：本机原 Flash 首扇区备份，继续留在原实验目录，不公开上传。
- 与本项目无关的桌面文件。

## 接下来如何维护

仓库中的对应模块作为后续协作入口。新增或修改工作优先落在仓库，不再依靠桌面多个副本相互覆盖。队友提供新版本时注明来源及变更；更新方案、图纸或采购表时保留清楚的版本说明。每次对话记录继续写在 `ai-dialogue/`，不将程序日志混入其中。
