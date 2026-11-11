# 第二批照片与自动预标注候选框

这是原电脑 `F:\gcs_medium_check_YOLO_model\annotation_remaining_v1\prelabel_v1` 的标注/清单快照。**按用户最新要求，本分支暂不提交照片文件；462 张照片仍在原电脑，待最后一次统一提交。所有 JSON 都是模型预测，尚未经过人工复核，不能直接作为训练真值。** 首轮 236 张的人工 YOLO 标签在 [`../midterm-yolo-v1/`](../midterm-yolo-v1/README.md)。

## 内容

| 路径 | 用途 |
| --- | --- |
| `images/` | 仅 439 个同名 AnyLabeling 矩形 JSON，均为待审核候选框；462 张 PNG 当前只在原电脑 |
| `manifest.csv` | 文件名、原电脑 `dataset_photos/` 相对路径、拍摄组别和单件形状/颜色提示 |
| `review_queue.csv` | 462 张的预测摘要；初始 `review_status=unreviewed`，AnyLabeling 保存不会自动更新此列 |
| `priority_review.csv` | 35 张单件照片的预测类别、框数与拍摄组别提示不符，供优先人工检查；不表示其他照片正确 |
| `model/best.pt` | 首轮训练最佳权重的副本，SHA-256 为 `4456f42b7b25cac953143ed6bb33bf1490d8c14c8f6a50f7586d8116d444a3c3` |
| `summary.json` | 当时预标注数量和参数 |
| `prelabel.py` | 当时生成候选框的脚本快照；会创建新 `prelabel_v1/`，不要对已经人工修改过的目录重新生成 |

462 张分为 409 张单件、33 张多件和 20 张空盘。脚本只对 442 张非空盘推理，`conf=0.25`、`imgsz=640`、RTX 5060 CUDA GPU，保持原图比例。439 张生成候选 JSON；另外三张非空盘没有候选框：`cube_white__photo_000026.png`、`tpri_blue__photo_000011.png`、`tpri_white__photo_000021.png`。20 张空盘跳过推理，没有 JSON。组别仅为拍摄时的提示，不等于逐图真值。

## 在 AnyLabeling 中复核

1. 在原电脑使用 `F:\gcs_medium_check_YOLO_model\annotation_remaining_v1\prelabel_v1\images`，该目录同时有照片和 JSON；`File → Open Dir` 打开它。同名 JSON 会显示矩形框。若使用仓库副本，需等照片最终上传后再打开。
2. 逐张看类别、漏框、误框和框的位置；用 R 补画矩形，修正后 Ctrl+S 保存，D 下一张。空盘也要目视确认。优先检查 `priority_review.csv` 中的图片，以及三棱柱/正方体、圆锥/圆柱的混淆。
3. 如果使用 `review_queue.csv` 管理进度，人工把已核查图片的状态改掉；保存 JSON 不会自动更改 CSV。全部需要的图片审核后，再导出 **YOLO (.txt) → Detection (Bounding Boxes)**。导出的类名顺序要按固定 `cube,sph,cyl,tpri,cone,tet` 核对并重映射。

尚未为这些照片划分 train/val/test。近重复摆放不应跨集合；最终独立测试应使用未参与训练和调参的新摆放照片。`prelabel.py` 需要同目录的 PNG 才能重跑；本分支暂不含这些照片。原电脑另外生成过 `best.onnx` 和 `anylabeling.yaml`，但模拟官方 AnyLabeling 的方形直接缩放预处理时，一张球体照片出现明显误判，因此此快照采用 PyTorch 原比例推理生成 JSON 后再人工复核。没有实际在 AnyLabeling GUI 中逐图验收候选框。
