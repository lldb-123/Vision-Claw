# 硬件与机械资料

## STM32F407VET6-Mini

[stm32f407-mini/](stm32f407-mini/) 保留原开发板资料的两个文件：

- `鹿小班--STM32F407VET6-Mini款PCB封装.schdoc`
- `STM32F407VET6-Mini开发板封装.pcbdoc`

此前读取结果是整板符号/封装资料，不等于完整内部电路原理图。实际引脚按板上丝印核对；当前可工作的实验接线见 [单电机说明](../experiments/single-motor/README.md)。

## 分拣机构

[mechanical/](mechanical/) 包含 `分拣机.SLDASM` 和 18 个零件文件。打开装配体时让零件保留在同一目录。原名称全部保留，包括 `支撑板..SLDPRT`；本次没有用 CAD 软件调整结构或验证装配引用。

当前讨论的执行机构是 X/Y 两个步进轴、Z 轴 MG90S 和六槽分类转盘 DS3120。文件反映其提供时的机械设计版本，最终尺寸、行程和动作仍以队友确认及实物为准。

## 配套资料

- [采购清单](../docs/procurement/附件：智能分拣材料申购清单-戚翰雯.xlsx)
- [队内架构图](../docs/architecture/system-architecture.png)
- [资料来源及版本说明](../docs/materials.md)
