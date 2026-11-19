# 香橙派上位控制程序

## 运行

模拟模式无需串口依赖：

```bash
cd orangepi_host
python3 server.py --simulation --port 8080
```

浏览器打开 `http://香橙派IP:8080`。

接入 STM32 后安装串口库并启动：

```bash
python3 -m pip install pyserial
python3 server.py --device /dev/ttyS3 --port 8080
```

串口设备可通过环境变量 `VISIONCLAW_SERIAL` 设置。香橙派型号不同，设备名可能是 `/dev/ttyS3`、`/dev/ttyUSB0` 或 `/dev/ttyACM0`。

程序复用固件现有文本协议，网页操作会转换成 `MOVE_MM`、`HOME`、`SERVO`、`TRAY`、`ESTOP` 等命令。连接失败时界面仍可在模拟模式运行。
