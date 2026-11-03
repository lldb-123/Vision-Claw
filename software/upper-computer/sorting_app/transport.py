"""真实串口与模拟设备提供相同的 read/write/close 接口。"""
class SerialTransport:
    def __init__(self, port: str, baudrate: int = 115200):
        import serial
        self.serial = serial.Serial(port, baudrate=baudrate, timeout=0.03, write_timeout=0.5,
                                    bytesize=8, parity="N", stopbits=1)

    def write(self, data: bytes):
        self.serial.write(data)

    def read(self) -> bytes:
        return self.serial.read(self.serial.in_waiting or 1)

    def close(self):
        self.serial.close()
