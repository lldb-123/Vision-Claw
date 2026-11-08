# 坐标换算快速说明

公式：`脉冲/毫米 = 电机每转脉冲数 ÷ 丝杆导程(mm)`。

例如 1.8° 电机整步 200 步/转、1/8 细分、丝杆导程 20mm，则 1600/20=80 脉冲/mm。修改 `Core/Inc/motion_config.h` 的 X/Y_STEPS_PER_MM 后重新 F7 编译。

串口：
```
ENABLE X
ENABLE Y
HOME X
HOME Y
GOTO_MM X 100 5
GOTO_MM Y 80 5
Z UP
Z DOWN
STATUS
```

`GOTO_MM` 是绝对坐标，`MOVE_MM` 是相对位移；坐标原点由 HOME 建立。速度单位是 mm/s。当前位置和目标位置会在 STATUS 返回。
