"""与 STM32 共用的字节协议。解析与硬件无关。"""
from dataclasses import dataclass
import re

MAX_FRAME = 256
TOKEN = re.compile(r"[A-Za-z0-9_.:+-]+\Z")

class ProtocolError(ValueError):
    pass

def crc16(data: bytes) -> int:
    value = 0xFFFF
    for byte in data:
        value ^= byte << 8
        for _ in range(8):
            value = ((value << 1) ^ 0x1021) & 0xFFFF if value & 0x8000 else (value << 1) & 0xFFFF
    return value

@dataclass(frozen=True)
class Packet:
    session: str
    seq: int
    command: str
    args: tuple[str, ...] = ()

    def encode(self) -> bytes:
        fields = ["1", self.session, str(self.seq), self.command, *map(str, self.args)]
        if not re.fullmatch(r"[0-9A-F]{8}", self.session) or not 1 <= self.seq <= 2147483647:
            raise ProtocolError("非法会话或请求编号")
        if not all(TOKEN.fullmatch(field) for field in fields):
            raise ProtocolError("参数只能包含数字和约定的 ASCII 标识符")
        body = ",".join(fields).encode("ascii")
        frame = b"@" + body + f"*{crc16(body):04X}\r\n".encode("ascii")
        if len(frame) > MAX_FRAME:
            raise ProtocolError("帧超过 256 字节")
        return frame

    @classmethod
    def decode(cls, frame: bytes):
        if len(frame) > MAX_FRAME or not frame.startswith(b"@") or not frame.endswith(b"\r\n"):
            raise ProtocolError("帧边界错误")
        try:
            body, checksum = frame[1:-2].rsplit(b"*", 1)
            if not re.fullmatch(rb"[0-9A-F]{4}", checksum) or crc16(body) != int(checksum, 16):
                raise ProtocolError("CRC 错误")
            fields = body.decode("ascii").split(",")
            if len(fields) < 4 or fields[0] != "1":
                raise ProtocolError("不支持的协议版本")
            packet = cls(fields[1], int(fields[2]), fields[3], tuple(fields[4:]))
            if packet.encode() != frame:
                raise ProtocolError("非规范帧")
            return packet
        except (ValueError, UnicodeError) as exc:
            raise ProtocolError(str(exc)) from exc

class FrameDecoder:
    """允许拆包/粘包；坏帧丢弃，下一个 @ 重新同步。"""
    def __init__(self):
        self.buffer = bytearray()
        self.errors = 0

    def feed(self, data: bytes) -> list[Packet]:
        packets = []
        for byte in data:
            if byte == ord("@"):
                self.buffer.clear()
            if byte == ord("@") or self.buffer:
                self.buffer.append(byte)
            if len(self.buffer) > MAX_FRAME:
                self.buffer.clear()
                self.errors += 1
            elif byte == 10 and self.buffer:
                try:
                    packets.append(Packet.decode(bytes(self.buffer)))
                except ProtocolError:
                    self.errors += 1
                self.buffer.clear()
        return packets
