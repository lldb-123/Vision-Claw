# 项目资料

| 资料 | 文件 | 使用说明 |
| --- | --- | --- |
| 队伍已提交的方案 | [team.pdf](competition/team.pdf) | 用户指定归档的提交版本，保留原 PDF |
| 命题/方案文档草稿 | [2027 年智能分拣赛项文档](competition/2027年第十届中国工创大赛-任务命题文档模板-智能分拣赛项.doc) | 用户指出其中有粗略填写内容；不能当作最终比赛规则或类别全集 |
| 材料申购 | [原始采购清单](procurement/附件：智能分拣材料申购清单-戚翰雯.xlsx) | 保留原表，采购数量与最终上机数量可能不同 |
| 系统架构 | [队内架构图](architecture/system-architecture.png) | 早期参考架构，最终接线与四电机分工需结合当前状态 |
| 文件来源与迁移 | [materials.md](materials.md) | 旧电脑路径到仓库路径的对应关系 |

## 相关代码和硬件

- [Orange Pi 5 Plus 小屏启动指南](orangepi-hdmi-startup.md)（接线、日常开机、首次配置及黑屏检查）。
- [Orange Pi 5 Plus 初始化与规范使用手册](orangepi-5-plus-initialization-guide.md)：完整设置清单、中文、网络/校时、Python、相机/串口、RKNN 环境规划及验收；建议步骤不等于已在板端执行。
- [STM32 电控初版](../firmware/README.md)：队友原设计、接口和 Core 源码。
- [上位机说明](../software/upper-computer/README.md)、[演示通信协议](../software/upper-computer/docs/通信协议.md)：与队友固件尚未统一接口。
- [单电机实验](../experiments/single-motor/README.md)：实际已烧录过的独立实验，不能当作完整分拣固件。
- [机械和开发板资料](../hardware/README.md)。
- [最新对话状态](../ai-dialogue/README.md)：优先读取当前结论，避免重复排查旧问题。

## 架构图

![队内早期系统架构图](architecture/system-architecture.png)
