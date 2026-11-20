# 698 张完整标注数据

`images/` 保存 698 张原尺寸 PNG，其中 668 张有同名 AnyLabeling JSON；`labels/` 保存 698 份固定六类的 YOLO `.txt`，其中 30 份空盘标签为空文件。共有 883 个目标框。`manifest.csv` 记录每张照片的来源、类别、框数和 SHA-256。

`splits.csv` 逐图记录 `scene_id` 与 train/val。`train.txt` 和 `val.txt` 列出相对于本目录的图片路径；`data.yaml` 直接引用这两个清单。**这里只有一份 PNG**，训练与验证不会另存图片副本。训练集 558 张、验证集 140 张，六类在两边都有框；本批次没有独立测试集。

划分脚本是上级目录的 `create_splits_698.py`。它在拍摄组内以框位置/尺寸、混合图画面相似度和连续空盘帧建立近重复场景组，再用种子 42 分配约 80:20 的 train/val。场景组由启发式推断，不是拍摄时人工登记的摆放编号。脚本默认只预览；已有 `splits.csv` 不会被 `--apply` 覆盖。

若以后修改 AnyLabeling JSON，同名 YOLO `.txt` **不会自动更新**；应重新导出或转换标签，核对 `manifest.csv` 和划分后再训练。图片和标注是原电脑 `F:\gcs_medium_check_YOLO_model\dataset_clear_698_photos` 的哈希一致副本。
