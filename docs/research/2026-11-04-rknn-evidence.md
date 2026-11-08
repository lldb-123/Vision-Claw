# Orange Pi 5 / RKNN 部署证据与实施边界

调研日期：2026-11-04（Asia/Singapore）。本文件是技术调研与实施建议，未在本项目 Orange Pi 5 上运行、量化或测试任何模型。网页和源代码已联网核验；公开基准与本项目估计严格分列。

2026-11-08归档提示：后续记录已确认实际板卡为Orange Pi 5 Plus，详见[主报告归档说明](../vision-system-options-2026-11-04.md)。本文保留原研究条件；公开RK3588数据仍不等于这块实物的端到端成绩。

## 结论

本项目优先比较 **YOLOv8n 检测、YOLOv8n-seg 实例分割**；有明确方向估计需求再考虑 YOLOv8n-OBB。YOLOv5n 可作为稳定而简洁的检测基线，YOLO11n 可作为同数据集对照。四者不是四套视觉方案，只是感知模块的候选实现。真正的方案差异应来自几何定位、传感器和动作决策。

该选择的理由是 Rockchip 已提供相应转换和部署示例，能尽早验证自定义类别的导出、量化、解码和整机延迟。**不能由模型更新或参数更少直接推出在 RK3588S 上更快、更准。** 当前官方单核基准中 YOLO11n 的推理速度就低于 YOLOv8n，但本项目类别准确率仍需实际比较。

SAM3 适合在 Windows/NVIDIA PC 或云 GPU 上辅助标注、探索漏检；不建议作为 Orange Pi 5 比赛闭环的主模型。MobileSAM 有官方 RKNN 示例，必要时可作为额外轮廓提取模块，但不能独立替代类别识别、定位和动作规划。

## 1. 已核验的公开性能

以下来自 [Rockchip Model Zoo 固定版本 README](https://github.com/airockchip/rknn_model_zoo/blob/837db8e992815ff8647eadb709f07067f4bc3a71/README.md#model-performance-benchmarkfps)。固定提交为 `837db8e992815ff8647eadb709f07067f4bc3a71`，日期 2026-10-13，版本 2.5.0。全部 YOLO 行条件为 **RK3588、单 NPU 核、平台最高 NPU 频率、输入 [1,3,640,640]、INT8、仅模型推理**，不含摄像头、预处理、后处理。不是 Orange Pi 5 的板级实测。右列由 `1000/FPS` 换算，并非另一次测量。

| 模型 | 官方模型推理 FPS | 换算毫秒/次 |
| --- | ---: | ---: |
| YOLOv5n | 84.6 | 11.82 |
| YOLOv5s | 49.1 | 20.37 |
| YOLOv5s_relu（不同激活版本，不能混称普通 v5s） | 66.5 | 15.04 |
| YOLOv8n | 76.3 | 13.11 |
| YOLOv8s | 38.6 | 25.91 |
| YOLO11n | 64.0 | 15.63 |
| YOLO11s | 34.6 | 28.90 |
| YOLOv5n-seg | 71.5 | 13.99 |
| YOLOv8n-seg | 63.2 | 15.82 |
| YOLOv8s-seg | 29.4 | 34.01 |
| YOLOv8n-OBB | 77.1 | 12.97 |

RK3588 与 RK3588S 同系列的公开结果可用于选型量级判断，不能照抄为本机结果：板级散热、电源、DDR、调频、SDK、输出布局和图优化版本会改变速度。6 TOPS 也不是每个网络都能获得的吞吐量。三核并发通常优化吞吐，不能简单把单张延迟除以三；需区分同一模型的多核执行与多个上下文流水线。

[RKNN C API 头文件](https://github.com/airockchip/rknn-toolkit2/blob/master/rknpu2/runtime/Linux/librknn_api/include/rknn_api.h) 提供单核与组合核掩码、运行性能查询和 SDK/驱动版本查询。首次评测先固定单核、batch=1，减少比较变量；需要时另测组合核。

## 2. 兼容性与模型选择

| 模型/任务 | 官方证据 | 本项目判断 |
| --- | --- | --- |
| YOLOv5 检测/分割 | Model Zoo 提供 FP16/INT8 示例和基准 | 成熟备选；不要混淆旧 YOLOv5、v5u 和 relu 优化版的输出 |
| YOLOv8 检测 | [官方示例](https://github.com/airockchip/rknn_model_zoo/tree/main/examples/yolov8) | 推荐首个部署闭环；先 n 后 s，以现场数据决定 |
| YOLOv8 实例分割 | [官方示例及输出说明](https://github.com/airockchip/rknn_model_zoo/blob/main/examples/yolov8_seg/README.md) | 支持 RK3588，FP16/INT8；轮廓提升决策信息，但需额外 CPU 预算 |
| YOLOv8 OBB | [官方示例](https://github.com/airockchip/rknn_model_zoo/blob/main/examples/yolov8_obb/README.md) | 支持 RK3588；该示例的 C demo 明确仅支持 8 位量化；OBB 是平面旋转矩形，不是三维姿态 |
| YOLO11 检测 | [官方示例及输出说明](https://github.com/airockchip/rknn_model_zoo/blob/main/examples/yolo11/README.md) | 已有成熟入口，不应因较新而否定；但无本项目精度收益证据前不必迁移 |
| YOLO11 分割/OBB | Ultralytics 目前通用 RKNN 路径覆盖对应任务；本次核验的 Model Zoo 未列独立 YOLO11-seg/OBB 基准 | 可做后续候选，不能拿 YOLO11 检测 demo 直接证明自定义分割部署已通过 |

Rockchip 的 [YOLOv8 优化导出说明](https://github.com/airockchip/ultralytics_yolov8/blob/main/RKOPT_README.md) 指出：为了量化和推理效率，将部分末端解码移出网络，在 CPU 上完成，并增加分数汇总输出。**训练权重、导出器、ONNX 输出、RKNN 模型和 CPU 后处理必须成套匹配**。不能拿普通 Ultralytics 单输出 ONNX 直接配 Rockchip 多输出后处理。

### 当前 Ultralytics 一键导出的特别边界

[Ultralytics RKNN 文档](https://docs.ultralytics.com/integrations/rockchip-rknn/) 已更新为 YOLO26 主示例，支持多任务、FP16 和 INT8。因而旧文章中的“只支持检测”“不能 INT8”已经不能无条件沿用。

但同页也明确：当前新版 INT8 路径使用主机端 `tail.onnx` 解码；检测、分割、姿态与 OBB 自定义运行时须执行该尾图或等价实现。其当前 INT8 精度在 Toolkit2 模拟器上验证，尚未在 Rockchip 硬件验证，表中的 INT8 基准待按新路径刷新。这里的版本状态是本次选择固定 Rockchip 链路、而非直接追随最新版 exporter 的理由，不代表永久不支持。该页 Radxa Rock 5B 基准与 Rockchip 优化图不是同一比较口径，不混表排名。

## 3. 推荐部署流程

1. **训练阶段**：Windows RTX 5060 或 AutoDL NVIDIA GPU 上训练 `.pt`，保存类别顺序、训练版本、输入尺寸和数据集划分。训练 GPU 不决定板端推理性能。
2. **转换环境**：使用与选定 SDK 匹配的 x86 Linux/Python 环境；Windows 可通过 WSL2 或容器准备该环境。先按实际软件支持情况验证；不用“Windows 装好训练环境”推断它能原生完成 RKNN 转换。
3. **ONNX**：按选定 Rockchip 导出脚本导出固定输入、batch=1、640×640，检查输出张量名称/数量/形状。ONNX 是本推荐路径的中间格式；不代表所有 RKNN 工作流只能接受 ONNX。
4. **先 FP16 再 INT8**：先建立 `.pt → ONNX → RKNN FP16` 的同图结果基线，再用比赛场景校准成 INT8。不要同时改变输入尺寸、阈值、模型版本和量化方式。
5. **转换核心操作**：`RKNN.config(target_platform='rk3588', ...) → load_onnx → build → export_rknn`。RGB/BGR、归一化、letterbox、输入 NHWC/NCHW 要与对应接口约定一致，不能在 RKNN 和应用层重复除以 255。示例 [convert.py](https://github.com/airockchip/rknn_model_zoo/blob/main/examples/yolov8/python/convert.py) 默认使用 COCO 小校准集，本项目应换为训练集内有代表性的比赛图像。
6. **板端运行**：原型用 RKNN-Toolkit-Lite2 的 Python API，性能瓶颈清晰后可把推理、解码或掩膜计算改 C/C++ Runtime。上位机流程和通信仍可留 Python。[官方 SDK 分工说明](https://github.com/airockchip/rknn-toolkit2#description)
7. **版本固定**：记录 Toolkit2、Lite2/Runtime、NPU 驱动、Model Zoo/exporter 提交和系统镜像。使用相容整套版本；不要盲目替换系统共享库。若板上仅能运行旧 SDK，就固定对应旧 Model Zoo 并重新评测，不能继续引用新版本结果为本机速度。
8. **先静态图片，再实时摄像头**：同一测试图在 PC 与板端比框、类别、轮廓、坐标回映射；随后接真实图像采集，再接规划和动作反馈。模型能加载只是部署检查的一步。

### 常见转换难点

- 自定义注意力、动态 shape、数据相关索引、GridSample、特殊 NMS、某些 TopK/三角函数或组合算子，可能产生不支持、回退或低效图。应检查**具体 SDK 版本、算子参数和转换报告**，不能只查算子名字就保证兼容。
- Toolkit2 2.5.0 的更新中仍分别列明 GPU/CPU 支持的算子；例如 GridSample 的 GPU 支持、部分 Pow/TopK 的 CPU 支持，说明“能转换”不等于“全在 NPU”。[SDK 当前说明](https://github.com/airockchip/rknn-toolkit2)
- 类别数变化可能要求同步修改 C/C++ 后处理常量；量化输出可能需要按张量各自 scale/zero-point 反量化。反量化、DFL 解码、NMS、OBB 角度约定错了，会出现模型运行正常但位置完全错误。
- 摄像头坐标回映射必须撤销 letterbox padding 与缩放，再去畸变/映射工作平面；禁止直接把 640×640 网络坐标当原图或毫米。

## 4. 实例分割的真实开销与数据陷阱

分割输出包括检测结果、实例系数和原型特征。需要先筛选/NMS，再执行系数与原型相乘、裁剪、阈值化、缩放，并计算接触边界和安全区域。工作量随保留实例数、原型分辨率和最终 mask 面积增加，CPU 后处理可能超过 NPU 推理时间。

核验 [官方 RK3588 分割后处理源码](https://github.com/airockchip/rknn_model_zoo/blob/837db8e992815ff8647eadb709f07067f4bc3a71/examples/yolov8_seg/cpp/rknpu2/postprocess.cc) 可见默认路径用 CPU 矩阵运算和 OpenCV 缩放；虽有 NPU matmul、RGA 函数，相关调用有注释，不能宣称默认已全硬件加速。

**对本项目尤其重要：**示例最终显示图将实例按 `class_id+1` 合并。相邻同类物块可能成为同色区域，独立实例身份不再可靠。正式接口必须在合并前保存每个候选的 `instance_id、mask、bbox、score`，不能把可视化合成图当实例标签图。

建议只计算通过筛选的前若干候选；规划可使用裁剪 ROI 或低分辨率 mask，精定位时再恢复到原图。不要为每个物体复制整张 1080p 浮点 mask。例如 20 个 640×640 float32 mask 单一缓冲区就约 31.25 MiB，系数乘法输出、原图、显示图和模型内存还要另计。这是内存容量计算，不是板端 RSS 实测。

## 5. INT8、分辨率与验收

量化会改变细小目标分数、轮廓、边缘及候选排序，不能假设固定损失百分比。建议从训练集采样 **200～500 张**有代表性的校准图作为起点，覆盖暗亮、污渍、遮挡、各类物块及空盘；该数目是本项目建议，不是官方最低要求。校准集不要用最终独立测试集。

比较同一冻结测试集的 PT、ONNX、RKNN FP16、RKNN INT8：类别召回、误分类、box/mask AP、选中目标正确率、目标位置误差和真实分拣成功率。建议验收门槛可暂设 INT8 相对 FP16 的关键类召回下降不超过 2 个百分点，并且位置误差不超机构余量；阈值须依据比赛需求调整。若不满足，先检查预处理和导出一致性，再调整校准图/混合精度；无需立即换大模型。

输入先从 640 开始：若所有物块在缩放后仍有清晰轮廓，可对比 512/416；若小二维码或小类别特征模糊，优先原图 ROI 二阶段处理，避免每帧把所有检测都升到 1280。OBB 输入尺寸也要与导出/量化固定一致。640 对 1280 面积比为 1:4，但实际延迟不必线性。

## 6. 时间、资源和长期运行：计划预算而非测试成绩

必须分别记录：

\[
T_{vision}=T_{capture/age}+T_{pre}+T_{NPU}+T_{post}+T_{geometry}+T_{decision}
\]

\[
T_{cycle}=T_{move/settle}+T_{vision}+T_{command}+T_{action}+T_{verify},\quad
T_{mission}=T_{navigation}+\sum T_{cycle}+T_{recovery}
\]

摄像头是 30 FPS 不代表有效视觉决策有 30 FPS；流水线吞吐也不等于单帧从曝光到决策延迟。机械臂/拨料机构的数秒动作不能用 YOLO FPS 换算。

以下只供首次实现安排预算：固定相机 30 Hz、最新帧队列深度 1、640 输入、nano/small INT8、小量候选、已配置散热、无高清显示录制。**不是公开测量，也不是本项目实测；USB MJPEG 解码、低照度曝光、Python实现或高候选数可超出范围。**

| 环节 | 首轮预算/估计 | 需要实测的原因 |
| --- | --- | --- |
| 图像曝光/传输/帧龄 | 约 5～40 ms；30 Hz 等待下一帧本身可达约 33 ms | 相机格式、曝光和缓存未知；普通 `read()` 耗时不等于完整帧龄 |
| 预处理 | 约 3～15 ms | 原图大小、色彩转换、resize 和 RGA 接入 |
| NPU | 参考公开基准量级约 12～35 ms | 模型、NPU 频率、版本、内存、实际板差异 |
| 检测后处理+几何/选择 | 约 3～20 ms | Python/C++、候选数、NMS、轮廓算法 |
| 分割后处理+几何/选择 | 约 15～120 ms | 实例数量、mask分辨率与矩阵运算实现 |
| 完整视觉检测路径 | 首轮约 40～150 ms | 包含余量；不含机构停稳 |
| 完整视觉分割路径 | 首轮约 80～300 ms | 包含余量；不含机构停稳 |

CPU 占用、RSS 内存、整板功耗和温度在现有证据下**没有可直接套用的可靠数值**。预计 CPU 瓶颈主要来自采集解码、分割后处理、GUI 和日志；8GB 是否足够要看进程 RSS/PSS 和缓冲区，而不是 `.rknn` 文件大小。NPU 标称 TOPS、额定电源瓦数均不是实际运行功耗。用整板输入功率计记录含相机/不含相机两种口径；温度同时记录频率及是否降频。

建议一次有意义的验收：预热后采样至少 1,000 次，记录各阶段中位数/p95/max、输入输出版本、对象数；再连续运行 1～2 小时覆盖真实比赛周期多次，观察 FPS 漂移、RSS 增长、相机断帧、NPU 报错、串口超时和热降频。不必每个动作做复杂诊断；长测是开发验收，比赛主循环只留必要状态与超时。

## 7. SAM3、MobileSAM 与其他模型

[SAM3 官方仓库](https://github.com/facebookresearch/sam3) 描述模型规模为 848M 参数，官方安装要求 CUDA GPU、Python/PyTorch 环境。其输出 mask/box/score 不是物体三维高度、受压状态或抓取成功概率。本次没有找到官方 Orange Pi/RKNN 转换部署示例，因此不能承诺板端实时速度。可在 PC/云 GPU 上给比赛图像做交互分割、生成候选标注并由人工修正，再训练小分割模型；不将网络云调用纳入比赛必须成功的闭环。

[MobileSAM 官方 RKNN 示例](https://github.com/airockchip/rknn_model_zoo/tree/main/examples/mobilesam) 支持 RK3588。上面的固定 Model Zoo 基准另给出 FP16 encoder 在 448×448 时 10.3 FPS（约 97.1 ms），decoder 119.4 FPS（约 8.38 ms）；两者分别计时，不能声称整套 119 FPS，还要考虑检测提示、编码缓存、多个候选和后处理。它可用于类别检测后修边或离线标注；简单比赛类别通常训练专用 YOLO-seg 更直接。

点云模型或学习抓取网络的算子可移植性必须独立验证，不能因为前端 YOLO 已 RKNN 化就推断整套三维模型也能上 NPU。先用深度图的平面拟合、高度阈值、局部法向和几何候选在 CPU 上做可解释的三维基线，再决定是否需要网络。单目相对深度也不能未经尺度标定直接输出毫米。

## 8. 尚缺的本项目验证

- 板卡系统、NPU 驱动与 Runtime 状态；现有历史只确认规划使用 Orange Pi 5，未完成实际 SSH/部署。
- 采购表已列微雪 OV2735，但实物型号/安装、镜头、实际分辨率、曝光/白平衡控制、安装高度和物块像素大小仍待核实。
- 自定义类别/掩膜数据集、训练模型和端到端运行日志。
- 执行机构最终工作方式；仓库已有 X/Y 拨料 + Z 舵机挡板，应按已有事实定义动作预算，不把尚未证实的多关节机械臂抓取周期当已知参数。

本调研没有修改程序、安装依赖、烧录、访问板卡或启动机构。下一步最有价值的工程验证是：固定一种导出链，使用少量真实托盘图片在目标板比较检测和分割的完整视觉延迟及目标位置误差。
