# 011：AnyLabeling 预标注形状类别校正

- 记录日期：2026-11-12，Asia/Singapore。
- 对话编号：011。
- 关联仓库：`https://github.com/lldb-123/Vision-Claw`；本地 `main`。标注数据位于原电脑 `F:\gcs_medium_check_YOLO_model\annotation_remaining_v1\prelabel_v1`，**没有进入仓库**。
- 本次状态：JSON 类别已校正；已补明显漏框，尚非全量人工精标，未导出 YOLO 标签或重新训练。

## 接续摘要

- 用户已经用 AnyLabeling 手工标注二百多张，又用小模型预标注剩余图片；本次要求直接校正 `prelabel_v1` 内错误的形状类别。单件图以 `cone_black__photo_000011.png` 这类文件名中的形状为真值。
- 原目录有 462 张 PNG：409 单件、33 多件、20 空盘组；原先 439 份 AnyLabeling JSON、628 个模型框。修改前 JSON 与 `review_queue.csv` 完全一致，没有发现人工已改过的预标注。
- 已改正 101 个既有框的类别、删除 33 个同物体重复框、拆开 1 个合并两件物体的框；补了 28 个多件图中明显漏掉的物体框，以及 1 个前沿部分可见的单件蓝色三棱柱框。现在有 440 份 JSON、625 个框。
- 两张单件组照片 `cube_white__photo_000026.png`、`tpri_white__photo_000021.png` 画面为空，保持无 JSON；20 张 `empty` 组也已逐张查看缩略图，均为空盘，保持无 JSON。

## 用户本次目标与约束

直接修正原电脑 F 盘预标注目录里的错误类别，不要求用户逐张手改。保留 AnyLabeling JSON 格式和原照片；不启动硬件、不训练模型、不自动提交或推送仓库。

## 处理方法与文件修改

- 单件图先核对 `review_queue.csv` 的 `shape_hint`、文件名前缀与六类固定顺序 `cube/sph/cyl/tpri/cone/tet`，将框类别设为文件名形状。20 张单件双框的 IoU 均高于 0.9，是同一物体的重复检测，各保留一框。
- 33 张多件图逐框看裁剪图、必要时查看整图，校正已检出的物体类别；明显漏框按可见区域补充。白色物体与托盘、边缘遮挡仍需后续细查。
- 原电脑 `F:\gcs_medium_check_YOLO_model\annotation_remaining_v1\prelabel_v1\images\`：直接修改 63 份既有 JSON，另新增 1 份 JSON；PNG 未改。
- 原电脑同目录 `backup_before_correction_2026-11-12/`：保留修改前 439 份 JSON、原 `review_queue.csv`、`priority_review.csv`、`summary.json`、`README.md`。备份建立后逐字节核对与修改前源文件一致。
- 原电脑同目录 `correction_details_2026-11-12.csv`：164 条逐框变更记录；`correction_report_2026-11-12.json`：数量汇总；`review_queue.csv`：新增当前框数、当前类别及处理状态，原模型预测列保留；`README.md`：说明用法和剩余限制。
- 仓库新增本记录，并更新 `ai-dialogue/README.md`。仓库原有未提交改动保留；本轮没有 commit/push。

## 验证与证据

- 阅读本地项目记录与训练工程的 `classes.txt`、预标注脚本、原目录说明，并核对公开 GitHub 仓库。
- 程序核验 462 张 PNG、440 份 JSON 和 625 个框；每份 JSON 可解析，图片名/尺寸/坐标有效；有 JSON 的 407 张单件图都恰好一框且类别等于文件名形状。
- 抽看修正后的带框预览，包括 `cone_black__photo_000011.png`、`tpri_blue__photo_000011.png`、若干 `large_mix` 和 `small_mix`。`cone_black__photo_000011.png` 现为 `cone`。
- 20 张 `empty` 组制作缩略图拼图逐张查看，未见目标物；未生成 JSON。
- `summary.json` 仍是**原模型输出统计**，不代表当前标签；当前数值以 `correction_report_2026-11-12.json` 为准。没有进行模型训练或精度评估。

## 未解决的问题与下一步

- 类别校正完成，但尚不能宣称全量人工精标。尤其多件图仍可能有漏框或框位置误差，单件图也未逐张检查边界。用于正式训练前应做最后一次可视化抽检和 train/val/test 分组核对。
- 20 张空盘组按核验后的无标签状态保留。原照片与模型权重没有复制进仓库。

## 2026-11-12 续：单件类别与文件名核验

- 应用户追问，重新逐份解析单件图当前 JSON，并比较图片文件名前缀、`shape_hint` 和每个框的 `label`：409 张单件图中，407 张有且仅有一框，407 个类别全部与文件名前缀一致，错误数为 0。
- 另两张 `cube_white__photo_000026.png`、`tpri_white__photo_000021.png` 经画面查看为空盘，故无 JSON。此核验是“标签与文件名严格一致”，不是对 409 张照片逐张独立判定实物形状的视觉真值复审；若拍摄时某张被放错组，文件名规则不会发现。

## 2026-11-12 续：全部 698 张合并成统一数据源

- 用户报告已完成后续预标注的人工修订，请将首批和后续全部照片与标签整理到独立新目录。未要求训练或重新划分数据。
- 本次以**当前磁盘上的标注 JSON** 为准：首批 236 张照片、226 份 JSON；后续 462 张照片、442 份 JSON。后续的 `cube_white__photo_000026.png` 与 `tpri_white__photo_000021.png` 现在已有用户新增的 JSON；叠框查看可见白色物体，前述“空盘”判断已被新证据取代。当前只有 30 张 `empty` 组没有 JSON。
- 原电脑新建 `F:\gcs_medium_check_YOLO_model\dataset_unified_v1\`。`images/` 放 698 张 PNG 与 668 份同名 AnyLabeling JSON；`labels/` 放 698 份同名 YOLO 检测 `.txt`，其中 30 份空盘标签为空文件；`classes.txt` 固定 ID 顺序 `cube/sph/cyl/tpri/cone/tet`。另有 `manifest.csv`、`dataset_summary.json` 和用法 `README.md`。原标注目录未修改。
- 合并清单逐项核对原始 `dataset_photos/`，无重名、缺图、非法类别、越界框或单件类别与文件名不一致。最终 698 张图、883 个框，逐类数量：`cube` 177、`sph` 78、`cyl` 201、`tpri` 160、`cone` 149、`tet` 118。698 张复制图与原图逐字节相同；生成的 YOLO 框与 JSON 逐框数值核对通过；`prepare_dataset.py --audit-only` 通过。
- 新目录是完整**未划分**数据源，没有 `train/val/test` 或 `data.yaml`；后续训练前按摆放场景分组划分，避免近重复泄漏。用户以后若继续修改 JSON，YOLO `.txt` 不会自动同步。
- 原电脑工程 `README.md`、`项目文件说明.md` 已更新入口；仓库本记录和对话索引已更新。未训练、提交或推送。

## 2026-11-12 续：正式训练就绪性检查

- 用户已自行将统一数据源移至原电脑 `F:\gcs_medium_check_YOLO_model\dataset_clear_698_photos\`，将旧训练、标注和输出目录移至 `preYOLO/`，另有 `dataset_photos_without_labels/`。本次只检查是否能训练，未启动训练。
- 当前 `dataset_clear_698_photos/` 仍有 698 张 PNG、668 份 AnyLabeling JSON、698 份 YOLO `.txt`（30 份空盘）、883 个框；`classes.txt` 六类顺序正确。`prepare_dataset.py --audit-only` 通过，清单逐图检查无缺图、缺标签或框数不一致。
- 现有 `.venv` 中 `torch 2.14.1+cu130`、`ultralytics 8.4.210` 可导入；RTX 5060 Laptop GPU 的 CUDA 小矩阵运算通过；根目录 `yolov8n.pt` 存在，`train.py` 可用，固定从该基础预训练权重训练六形状 YOLOv8n。
- **当前不能直接运行正式训练**：干净数据源尚无 train/val 划分、`splits_698.csv` 或 `data.yaml`。现有 `prepare_dataset.py` 能按划分表生成训练目录；`train.py` 要求 train/val 均有六类。首轮旧 `preYOLO/dataset_v1/data.yaml` 写死旧的 `F:/gcs_medium_check_YOLO_model/dataset_v1` 绝对路径，不可直接复用，`splits_first_v1.csv` 也只覆盖首轮 236 张。
- 更新原电脑根目录 `README.md`、`项目文件说明.md` 和 `dataset_clear_698_photos/README.md`，纠正用户移动后的路径和准备命令；仓库内仅更新本对话记录及索引。下一步需按摆放场景为 698 张图制定划分表、生成新训练目录与 `data.yaml`，再短跑烟测和正式训练。这里的下一步不代表本次已经执行。

## 2026-11-12 续：698 张按场景分组划分，未训练

- 用户要求写 Python 脚本完成划分，但明确**先不要开始训练**。此前“尚无划分与 `data.yaml`”的状态已由本节取代；没有执行短跑或正式训练。
- 原电脑 `F:\gcs_medium_check_YOLO_model\create_splits_698.py` 已创建。默认只预览；`--apply` 才写新文件且不覆盖旧文件。它审计 698 张清单、图片、六类标签；在拍摄组内按框位置/尺寸和多件图托盘画面相似度将近重复帧连成场景组，空盘按连续三张分组；随后用固定随机种子 `42` 对各拍摄组的场景组做约 80:20 训练/验证分配。不是逐张随机。实际有 583 个场景组，训练 461 组/558 图，验证 122 组/140 图；所有 39 个拍摄组两边均有图，六种类别两边均有框。同一 `scene_id` 没有跨划分。此批次不设 test，后续宜用新摆放的独立照片盲测。场景分组是启发式推断，不等于人工记录的真实摆放编号。
- 已执行 `create_splits_698.py --apply`，生成原电脑 `splits_698.csv` 与 `splits_698_summary.json`。验证将脚本以种子 42 重算，698 条 `(scene_id, split)` 与 CSV 完全一致。
- 原电脑 `prepare_dataset.py` 新增可选 `--link-images`；已执行 `--source .\dataset_clear_698_photos --splits-csv .\splits_698.csv --out .\dataset_train_698_v1 --link-images`。生成 `dataset_train_698_v1/images/{train,val}`、`labels/{train,val}`、`data.yaml`、划分与汇总。698 张训练目录图片均与干净数据源为同卷 NTFS 硬链接，避免另一份照片空间；698 份标签逐字节匹配源 `.txt`，含 30 份空盘标签。图片若在任一硬链接路径原地修改，另一处也改变。
- 调用 `train.check_dataset(data.yaml)` 只读验证通过：train 558 张，框数 `cube 141/sph 61/cyl 159/tpri 133/cone 122/tet 99`；val 140 张，框数 `cube 36/sph 17/cyl 42/tpri 27/cone 27/tet 19`。没有执行 `train.py`、`--smoke` 或其他模型训练。更新了原电脑 `README.md`、`项目文件说明.md`、干净数据源 `README.md`，以及仓库本记录与索引；没有 commit/push。

## 2026-11-12 续：正式训练启动命令准备，未开训

- 用户问是否现在能正式训练，要求给命令行启动程序，由用户自行启动；若现有 PyTorch/CUDA 可用，不先下载大量文件。
- 本机只读复核：现有 `.venv` 为 `torch 2.14.1+cu130`、`ultralytics 8.4.210`；RTX 5060 Laptop GPU CUDA 运算通过；原电脑根目录本地 `yolov8n.pt`（约 6.5 MB）成功加载为检测模型；`dataset_train_698_v1/data.yaml` 通过 `train.check_dataset()`，558 train / 140 val、六类均有框。没有安装或下载依赖、权重。
- 原电脑 `F:\gcs_medium_check_YOLO_model\train.py` 改为从脚本所在目录加载本地 `yolov8n.pt`，文件缺失时直接报错，避免相对路径落空后尝试下载。新增同目录 `start-train-698.cmd`：切换自身目录，设置 `YOLO_OFFLINE=1`，确认现有 `.venv`、权重及数据 YAML 存在，然后以 `--epochs 100 --imgsz 640 --batch 8 --workers 0` 调用 `train.py`。PowerShell 启动命令：`Set-Location 'F:\gcs_medium_check_YOLO_model'; .\start-train-698.cmd`。更新原电脑 `README.md`、`项目文件说明.md`。
- `train.py` 语法检查通过；另以 `YOLO_OFFLINE=1` 只读运行预检，确认 Ultralytics `ONLINE=False`、本地权重可加载、GPU 和 558/140 数据可用。**没有执行启动脚本、烟测或任何正式训练**；运行时的显存占用和最终模型精度仍待用户启动后观察。仓库仅更新本对话记录与索引，未 commit/push。

## 2026-11-12 续：用户启动后的训练状态检查

- 用户自行运行了原电脑 `F:\gcs_medium_check_YOLO_model\start-train-698.cmd`。本次只读检查进程、`runs/train_20261112_115424/` 的日志和检查点，没有启动、中断或修改训练。
- 2026-11-12 约 12:10（Asia/Singapore）时，`train.py` 进程仍在，`results.csv` 已持续写到第 45/100 轮，`last.pt` 和 `best.pt` 均存在；运行参数是 `yolov8n.pt`、698 图数据 YAML、CUDA 设备 0、640 像素、batch 8、workers 0。45 轮的验证精确率约 0.980、召回率约 0.941、mAP50 约 0.990、mAP50-95 约 0.948；此前第 44 轮的 mAP50-95 约 0.959，为当时最佳检查点。首轮 mAP50-95 约 0.364，指标整体明显提升。
- `nvidia-smi` 显示 GPU 显存约 1494/8151 MiB，采样利用率 0–19% 间波动；无显存溢出迹象。进程和日志持续推进，当前判断训练正常。验证照片仍来自同一拍摄批次，指标不能替代独立新场景测试。模型尚未训练结束，最终效果及最终权重尚未确认。

## 2026-11-12 续：正式训练结束与模型效果

- 用户报告训练已结束。本机确认 `train.py` 进程已退出，原电脑 `F:\gcs_medium_check_YOLO_model\runs\train_20261112_115424\` 有 `run_metadata.json`、`results.csv`、曲线和验证预览，`weights/best.pt` 与 `last.pt` 均已保存。命令设最多 100 轮、`patience=20`；CSV 最后为第 99 轮，最佳验证 mAP50-95 出现在第 79 轮，符合 20 轮无改善后提前停止。没有异常退出的证据。
- 使用现有 `.venv` 和 `YOLO_OFFLINE=1`，以 `best.pt` 在原 140 张验证图（168 个标注目标）上再次运行 `YOLO.val()`；只做验证，未重新训练或下载。结果：precision 0.97545、recall 0.97380、mAP50 0.99464、mAP50-95 0.97014，与训练时最佳 0.97022 接近；验证输出在原电脑 `runs/eval_best_20261112/`。
- 逐类 mAP50-95：`cube` 0.9875、`sph` 0.9713、`cyl` 0.9790、`tpri` 0.9628、`cone` 0.9688、`tet` 0.9514。`tet` 精确率 0.8823，为相对较弱的一类。查看训练输出 `val_batch0_pred.jpg`，`cone_black__photo_000009.png` 的圆锥出现误判为四面体，故不可称六类完全无错。6 张验证集空盘在置信度阈值 0.25 下均无误报。
- 训练/验证损失曲线整体下降，验证指标后期趋稳；但两集合均来自同一拍摄批次，且场景组由启发式近重复识别得出。这里的高分只证明该批次验证表现，**尚无新摆放、不同光照或混放的独立测试成绩**，不能宣称实物泛化精度。建议后续以最佳 `best.pt` 对新照片做独立测试，再决定是否补拍或调整模型。
- 原电脑根目录 `README.md`、`项目文件说明.md` 和 `dataset_clear_698_photos/README.md` 已更新最终状态；仓库仅更新本记录与索引，未 commit/push。

## 2026-11-12 续：中期视觉分支整理

- 用户明确要求在 `codex/midterm-vision-model` 分支清理过程中留下的半成品，将**目前正式训练数据、结果权重和训练代码**集中放进一个目录；授权删除过时的零散模型/数据。此前“不在当前分支提交照片”的要求被本次要求取代。原电脑 `F:\gcs_medium_check_YOLO_model` 不受清理影响。
- 分支工作树为原电脑 `C:\Users\Lenovo\Documents\ChatGPT\工创赛-midterm-vision`。操作前已有 23 个 STM32 固件文件的未提交改动，属于另一项工作；本轮未修改、暂存或清除它们。
- 新建仓库 `midterm-vision/`：`dataset/images/` 放唯一一份 698 张 PNG 与 668 份 AnyLabeling JSON；`dataset/labels/` 放 698 份 YOLO 标签（30 份空盘），另有六类清单、698 张 manifest、`splits.csv`、`splits_summary.json`、558/140 图片路径清单与可迁移的 `data.yaml`。训练/验证通过文本清单引用同一份图片，没有第二份图片目录。
- 同目录放当前 `train.py`、`predict.py`、`capture.py`、数据审计与划分脚本、启动脚本、依赖表；`weights/` 只保留当时基础 `yolov8n.pt` 与本轮最佳 `best.pt`；`results/` 保留精简指标 JSON、训练曲线、混淆矩阵和一张验证预览。实时演示代码移至 `midterm-vision/live-demo/` 并改为默认加载当前 `best.pt`。未复制 `.venv`、运行日志、`last.pt` 或第一轮权重。
- 当前树移除旧 `datasets/midterm-yolo-v1/`、`datasets/midterm-yolo-prelabel-v1/`、`software/midterm-yolo-model/`，并将旧实时演示目录迁至新位置。旧预标注 462 张和首轮 236 张本机忽略 PNG 均逐张与新目录同名图片 SHA-256 一致后删除；旧阶段文件仍可由 Git 提交 `70fa3fb` 追溯。
- `.gitattributes` 将新目录 698 张 PNG 与 2 份 `.pt` 交给 Git LFS；AnyLabeling JSON 保留原字节，避免换行归一化破坏 manifest 的标注 SHA-256。`.gitignore` 排除新目录的虚拟环境、运行输出、拍摄临时图和缓存。根 README、资料索引和旧进展文档已更新当前入口与历史状态。
- 验证：复制后 698 张图片 SHA-256 与 manifest 一致，698 份 YOLO 标签逐字节等于 F 盘原件，2 份权重哈希一致；脚本重算 583 个场景组和 558/140 划分与 CSV 完全一致；`train.check_dataset()` 检查六类覆盖通过。使用仓库副本 `best.pt`、仓库相对 `data.yaml` 与原电脑已有 CUDA 环境，只运行验证，得到原 140 张验证图/168 框的 Precision 0.97545、Recall 0.97380、mAP50 0.99464、mAP50-95 0.97014，与 F 盘复核一致。没有新训练或实物实时演示测试。
- 本节完成状态：视觉整理提交为 `ed40ba8d724aac0a789594949dce0fe84e0dfff2`，已推送到远端 `origin/codex/midterm-vision-model`，`git ls-remote` 与本地 SHA 一致。Git LFS 上传 700/700 个对象、约 514 MB，`git lfs fsck` 通过；新照片和权重在 Git 提交中是 LFS 指针。当前树已无旧阶段目录。整理前的旧图片仍存在于 Git 历史，未对共享历史做强制重写。
- 本地工作树还有操作前已有的 22 个 STM32 固件文件未提交改动（`git status` 所示）；本轮没有修改或暂存它们，因此“视觉部分已整理并同步”不等于整个工作树零改动。原电脑 F 盘训练工程没有移动或删除。

## 2026-11-12 续：实时颜色与形状识别演示

- 用户要求使用新的 `best.pt` 写实时物体检测与六色识别脚本，用于中期检查；保持现有数据集、训练代码和权重不变。本次只修改 `midterm-vision/live-demo/` 的演示脚本与说明，并更新本记录、索引和 `midterm-vision/README.md`。未启动相机或训练。
- `live-demo/color_vision.py` 新增 HSV 判色：在每个 YOLO 框中心取椭圆区域，避免框边托盘背景；按亮度和饱和度先区分黑、白，再按色相区分红、黄、深蓝、浅蓝。`live_demo.py` 将颜色与六形状一起显示在实时画面，右侧分别计数；`--check` 在终端逐项输出颜色、形状及形状置信度。相机后端和现有启动命令保持可用。
- 用现有 CUDA 环境和仓库图片离线核对：625 张单物体照片按人工标注框取色，625/625 与文件名颜色一致；同批次验证集的 125 张单物体照片用新模型实际预测框取色，125 张检出且 125/125 颜色一致。另渲染 `small_mix__photo_000003.png` 和 `large_mix__photo_000003.png` 多物体画面并查看预览。预览位于被 Git 忽略的 `midterm-vision/runs/`，不进入数据集。旧已知错误 `cone_black__photo_000009.png` 依然会被模型误判为四面体，颜色判断为黑色。
- 这些核对都来自原拍摄批次，尚不能证明新摆放、新光照的颜色或形状准确率；**尚未实际打开实时相机窗口验收 FPS 与识别效果**。没有修改或暂存原有 STM32 固件改动。本轮尚未 commit/push。

## 2026-11-14 续：实时展示脚本提交到 GitHub

- 用户明确要求将上节实时展示脚本及说明提交到 GitHub，并列出仓库分支和结构；本次按要求不运行测试。
- 提交范围仅为 `midterm-vision/live-demo/color_vision.py`、`live_demo.py`、实时演示及中期资料 README、`ai-dialogue/README.md` 和本记录。原有 STM32 固件未提交改动不纳入提交；数据集、权重和训练代码不修改。
- 提交目标为 `origin/codex/midterm-vision-model`。前一节“尚未 commit/push”描述的是上次工作结束时的状态，本节完成后以远端分支为准。
