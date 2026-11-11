# 010：中期检查 YOLOv8n 数据集拍摄方案

- 记录日期：2026-11-11，Asia/Singapore。
- 对话编号：010。
- 关联仓库/分支：Vision-Claw / 当前本地分支。
- 相关历史记录：[009：中期检查颜色与形状方案](2026-11-10-009-yolo-color-shape-annotation.md)。
- 本次状态：已写拍摄方案；尚未用正式相机拍摄、标注、训练或验证。

## 接续摘要

- 用户为中期检查准备 YOLOv8n 初级模型，照片预算不超过 1000，期望约 800；检测六形状（正方体、球体、圆柱体、四面体、圆锥体、三棱柱），六色为黑、白、红、黄、深蓝、浅蓝，颜色由传统视觉判断。
- 已新增[800 张上限的分批数据集方案](../docs/midterm-yolov8n-dataset-800-plan-2026-11-11.md)：先拍 96 张打通链路，约 400 张检查效果，最多 690 张开发＋110 张独立盲测；每张为独立重新摆放的正式相机原图。800 不是必须拍满的门槛。
- 理想情况下 36 个形状×颜色实物组合各拍 8 张单件，共 288 张；另有 312 张稀疏多件、60 张有限难例、30 张空盘/非目标干扰，最终 110 张新摆放测试。缺少实物组合时按实际覆盖重排，不宣称未采组合效果。
- 当前最先完成正式相机、灯光和机位的可辨性试拍；用户提供的手机参考照片仍只作定性参考。尚无正式数据或模型结果。

## 用户本次目标与约束

阅读 GitHub 仓库，为 YOLOv8n 六形状检测＋传统六色判断写一份可直接执行的 `.md` 数据集构建方案，明确照片类型、数量、拍法、划分和标注。优先得到初级模型；可接受 1000 张以内，最好约 800 张。

## 本次新增或确认的事实

- 用户本次明确六种颜色名称：黑、白、红、黄、深蓝、浅蓝；替代旧 009 中“颜色名称未确定”的状态。
- 公开 GitHub `main` 仓库仍介绍项目目标、上位机演示代码及材料位置；本地已有 009 中期检查方案与训练清单。本轮阅读仓库和相关方案，没有实物采集、环境安装或训练。
- 尚不知 36 种形状×颜色组合是否全部有实物、正式相机最终视角和灯光设置；方案对缺项设了记录和配额调整规则。

## 决策与方案

- YOLO 保持 6 个形状类，颜色真值另记，不建立 36 个 YOLO 类。每件物体的颜色信息与标注框关联，供后续 HSV/亮度/饱和度校准及联合测试。
- 约 800 张预算包含独立测试，分批为 96 → 400 → 690 张开发图，再补 110 张冻结后的新摆放盲测；达到中期演示要求可提早停拍并另留相应测试图。
- 拍前先用正式相机和已有灯带检查可见侧面、暗部及高光；同一摆放的连拍不计独立场景。按会话/摆放组划分数据，预标注需逐张人工复核。

## 文件与实际修改

| 路径 | 修改 | 实际状态 |
| --- | --- | --- |
| `docs/midterm-yolov8n-dataset-800-plan-2026-11-11.md` | 新增拍摄配额、36 格清单、阶段和划分、颜色数据复用 | 已落盘，未拍摄/训练 |
| `docs/README.md` | 增加方案入口 | 已落盘 |
| `docs/midterm-yolo-shape-color-plan-2026-11-10.md` | 补充本次确认的六色和新配额方案入口 | 已落盘 |
| `ai-dialogue/2026-11-11-010-midterm-dataset-plan.md` | 本次对话记录 | 已落盘 |
| `ai-dialogue/README.md` | 更新当前状态和索引 | 已落盘 |

## 验证与证据

- 阅读本地 `AGENTS.md`、`ai-dialogue/README.md`、009 接续记录、既有中期方案和训练清单，并浏览公开 [Vision-Claw 仓库](https://github.com/lldb-123/Vision-Claw)。
- 核对 [Ultralytics 检测数据格式](https://docs.ultralytics.com/datasets/detect/)、[训练模式](https://docs.ultralytics.com/modes/train/)和[增强说明](https://docs.ultralytics.com/guides/yolo-data-augmentation/)；配额算术和文档链接做静态检查。
- 本次只写文档；没有正式采集、标签、模型权重或检测指标。

## 未解决的问题与下一步

现场核对 36 格的实物覆盖、正式机位及灯光；按方案阶段 A 拍 96 张，再标注/短跑 YOLOv8n。若缺组合，以实际物料清单修订配额。用户目前仅请求方案，本记录中的下一步不代表自动执行硬件操作。

## 2026-11-11 续：AnyLabeling 首张图片操作

- 用户提供 AnyLabeling 空白主界面截图，表示已准备使用该软件标注；桌面有 `C:\Users\Lenovo\Desktop\image.jpg`（原电脑路径，未进入仓库）。本次只读确认文件存在并查看：托盘内有多件物体，黑/红/深蓝正方体、橙色圆柱、粉色球体清晰可见，黄色及浅蓝件需要按实物确认形状。没有修改该图或实际操作标注软件。
- 指导步骤：`File → Open` 打开该单图；截图顶部提示矩形快捷键 `R`，逐物体拖可见外接矩形，输入固定六形状英文类名；`File → Save` 保存原生标注；`Tools → Export Annotations → YOLO` 导出检测标签。多件图要每件一框，不标托盘和机构。颜色不写进 YOLO 类名，另记六色真值。橙色、粉色不属于本次六目标颜色，不拿它们标定六色阈值。
- 已核对 AnyLabeling 官方数据导出文档：YOLO 导出生成每图归一化框 `.txt` 和 `classes.txt`；本次尚未产生实际 `.json`、`.txt`、`classes.txt`、`data.yaml` 或训练数据。

## 2026-11-11 续：标签改用短英文名

- 用户希望 AnyLabeling 标签缩为 3–4 个字母。统一采用 ID 0–5：`cube` 正方体、`sph` 球体、`cyl` 圆柱体、`tpri` 三棱柱、`cone` 圆锥体、`tet` 四面体；旧长名 `sphere/cylinder/triangular_prism/tetrahedron` 不再用于新标签。类别 ID 顺序不变。
- 已同步修改 `docs/midterm-yolo-shape-color-plan-2026-11-10.md`、`docs/midterm-yolov8n-dataset-800-plan-2026-11-11.md` 的标签表及 `data.yaml` 示例、`docs/local-yolo-six-shape-training-checklist-2026-11-10.md` 的类名说明，并更新 `ai-dialogue/README.md`。当前未实际操作用户的 AnyLabeling 文件；若已有旧名标签，需在导出/训练前统一改名并复核 `classes.txt` 与 `data.yaml` 的 0–5 顺序。

## 2026-11-11 续：黑色正方体被遮挡的标注口径

- 用户截图显示红色正方体遮挡黑色正方体下半部，问黑色目标怎么画框。按既定“可见部分外接框”口径：黑色目标仍有清楚的顶面、侧面，可标 `cube`；矩形紧包可见黑色区域，不向下猜测被红色物体盖住的底部。矩形内部不可避免含少量红色遮挡物不影响形状框标注，两目标框允许重叠。
- 这只是对用户截图的指导，没有在 AnyLabeling 中替用户画框或保存标注。若今后只有极小碎片、无法从图像可靠判形，应把整图暂放审核集，不让明显物体作为未标注背景进入训练。

## 2026-11-11 续：AnyLabeling YOLO 导出设置

- 用户发来 Export Annotations 对话框截图，询问各项如何选择。只读确认原电脑桌面 `image.jpg` 和 `image.json` 均存在；JSON 中 7 个 `rectangle` 框，类别为 `cube`×3、`sph`×1、`cyl`×1、`tpri`×1、`cone`×1。尚无 `tet` 实例；未修改或导出标签。
- 对该单图建议 `YOLO (.txt)`、`Detection (Bounding Boxes)`；源文件夹最好是仅含这张图和对应 JSON 的专用文件夹，不直接递归扫描整个桌面；输出到另一个专用文件夹；UUID 随机命名关闭；只有一图时关闭自动 train/val/test 划分。完整数据集仍按拍摄场景组人工分 train/val/test，避免相邻近重复跨组。
- 此单图导出仅供格式检查，不能据其只有 5 类的 `classes.txt` 直接声称最终六类配置完备。最终导出后核对 `classes.txt` 与 `data.yaml` 的 ID 0–5 对应关系。

## 2026-11-11 续：Windows RTX 5060 训练代码准备

- 用户说当前标签已导出到原电脑桌面 `C:\Users\Lenovo\Desktop\tttest_yolo`，正式数据仍要一段时间才能拍完；指定原电脑工程目录 `F:\gcs_medium_check_YOLO_model`，希望先写 YOLOv8n 训练代码，并说明后续需要确认的信息。
- 只读核对：导出实际位于 `tttest_yolo/yolo_first`，含 1 张图片、1 个 YOLO 标签和 `classes.txt`；导出类序为 `cone, cube, cyl, sph, tpri`，与既定 `cube, sph, cyl, tpri, cone, tet` 不同。现有 7 框：`cube` 3，`sph/cyl/tpri/cone` 各 1，`tet` 0。若直接套既定 `data.yaml` 训练会错位，因此导入脚本按类名重映射并拒绝未知类或缺失的 train/val 类别。
- 本机只读实测：RTX 5060 Laptop GPU 8151 MiB、驱动 582.05；默认 Python 3.14.2 的 `torch 2.14.0+cpu` 无 CUDA。uv 管理的 Python 3.12.13 路径存在且有 pip，但 `py -3.12` 无法选中它；README 改用实际解释器完整路径。尚未创建虚拟环境、安装 GPU PyTorch/Ultralytics 或启动训练。
- 在**仓库外、用户指定的原电脑路径** `F:\gcs_medium_check_YOLO_model` 已写 `prepare_dataset.py`（审计、重映射、按 `scene_id` 明确划分 train/val/test）、`train.py`（六类校验、CUDA 实际运算预检、YOLOv8n 微调）、`predict.py`、`README.md`、`requirements.txt` 和 `.gitignore`。工程文件不在 Vision-Claw 仓库，没有 commit/push。
- 验证：Python 3.12 AST 语法检查、训练和推理脚本 `--help`、当前单图 `--audit-only` 均通过；实际标签映射核对为 `cone 0→4、cube 1→0、cyl 2→2、sph 3→1、tpri 4→3`，7 行均正确转换。没有构造正式数据集或训练出 `best.pt`。
- 后续需由现场确认正式照片是否同一固定机位/光照、六类是否在 train/val 都有实拍实例、每张图的摆放/连拍组 `scene_id`。训练前按 PyTorch 官方 Windows CUDA 12.8+ 指南建独立环境并做 RTX 5060 实测；这不是本轮已完成事项。

## 2026-11-11 续：从最新 main 建中期视觉分支

- 用户明确授权把目前相关内容同步到 GitHub，建议从远端最新 `main` 建中期检查视觉模型分支。已 `git fetch origin main`，基点为 `a3b1ccc24e4f5528588b87f84bb4277774520a17`；原电脑另建工作树 `C:\Users\Lenovo\Documents\ChatGPT\工创赛-midterm-vision`，分支 `codex/midterm-vision-model`。原 `main` 工作树中已有的未提交文件保持原样。
- 远端 `main` 已有较新的 Orange Pi 002/004/005 记录及 STM32 运动控制合并，未用本地较旧同名文件覆盖。以远端索引为底，补入 006–010 记录、视觉方案和研究文档；008 环境实测保留作为新记录。训练代码从原电脑 `F:\gcs_medium_check_YOLO_model` 复制到仓库 `software/midterm-yolo-model/`，仓库版 README 改为从仓库目录执行。原桌面练习照片、AnyLabeling 导出标签、虚拟环境和权重没有复制入仓库。
- 已核对新增文档的本地链接、Python 语法及当前单图的标签审计；首个提交 `664adc4fc087ff8aeca437e118d9904cbdc9313d` 已推送到 `origin/codex/midterm-vision-model`，`git ls-remote` 返回相同 SHA。远端 `main` 在推送前复查仍为基点 `a3b1ccc24e4f5528588b87f84bb4277774520a17`。本次只同步分支，没有合并 `main` 或创建 PR；正式数据集、CUDA 环境和 `best.pt` 尚未产生。
