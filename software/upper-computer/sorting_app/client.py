"""单工作线程拥有串口；GUI 通过事件请求停止，不并发读取串口。"""
import secrets
import time
from collections import defaultdict, deque
from .protocol import Packet, FrameDecoder

class DeviceError(RuntimeError):
    pass

class TaskCancelled(DeviceError):
    pass

class ControllerClient:
    def __init__(self, transport, config=None, trace=None):
        self.transport = transport
        self.config = config or {}
        self.trace = trace or (lambda direction, frame: None)
        self.session = secrets.token_hex(4).upper()
        self.seq = 0
        self.boot_id = None
        self.homed = False
        self.decoder = FrameDecoder()
        self.inbox = defaultdict(deque)

    def new_request(self, command, *args):
        self.seq += 1
        return Packet(self.session, self.seq, command, tuple(map(str, args)))

    def send(self, request):
        frame = request.encode()
        self.trace("TX", frame.decode("ascii").strip())
        self.transport.write(frame)

    def receive(self):
        for packet in self.decoder.feed(self.transport.read()):
            self.trace("RX", packet.encode().decode("ascii").strip())
            if packet.session == self.session:
                self.inbox[packet.seq].append(packet)

    @staticmethod
    def checked(packet):
        if packet.command == "ERR":
            if packet.args[-1:] == ("ABORTED",):
                raise TaskCancelled("任务已停止；再次运行前请回原点")
            raise DeviceError(" / ".join(packet.args))
        return packet

    def exchange(self, command, *args, timeout=None):
        request = self.new_request(command, *args)
        wait = timeout or self.config.get("ack_timeout", 0.3)
        for _ in range(self.config.get("retries", 2) + 1):
            self.send(request)
            until = time.monotonic() + wait
            while time.monotonic() < until:
                self.receive()
                if self.inbox[request.seq]:
                    packet = self.inbox.pop(request.seq).popleft()
                    return self.checked(packet)
        self.inbox.pop(request.seq, None)
        raise DeviceError(f"{command} 无回复，请检查连接")

    def connect(self):
        packet = self.exchange("HELLO")
        if packet.command != "DONE" or len(packet.args) != 4 or packet.args[0] != "HELLO":
            raise DeviceError("HELLO 回复格式不匹配，请核对协议文档")
        self.boot_id = packet.args[1]
        self.homed = packet.args[3] == "1"
        return packet

    def status(self):
        packet = self.exchange("STATUS")
        if packet.command != "STATUS" or len(packet.args) != 4:
            raise DeviceError("STATUS 回复格式错误")
        if self.boot_id != packet.args[3]:
            self.homed = False
            raise DeviceError("STM32 已重启：需要重新连接并核实任务状态")
        self.homed = packet.args[2] == "1"
        return packet

    def stop(self):
        try:
            return self.exchange("STOP")
        finally:
            self.homed = False

    def execute(self, command, *args, cancel=None, on_status=None):
        request = self.new_request(command, *args)
        timeout = self.config.get("motion_timeout", 12.0)
        ack_timeout = self.config.get("ack_timeout", 0.3)
        started = time.monotonic()
        retry_at = started + ack_timeout
        poll_at = started + 0.5
        attempts = 1
        accepted = False
        self.send(request)
        try:
            while time.monotonic() - started < timeout:
                if cancel and cancel.is_set():
                    self.stop()
                    raise TaskCancelled("已停止；下次运行前请回原点")
                self.receive()
                while self.inbox[request.seq]:
                    packet = self.checked(self.inbox[request.seq].popleft())
                    if packet.command == "ACK" and packet.args == (command,):
                        accepted = True
                    elif packet.command == "DONE" and packet.args[:1] == (command,):
                        if command == "HOME":
                            self.homed = True
                        return packet
                now = time.monotonic()
                if not accepted and now >= retry_at:
                    if attempts > self.config.get("retries", 2):
                        raise DeviceError("任务是否接受尚未确认；停止推进，请核实设备状态")
                    self.send(request)  # 原编号重发，绝不生成第二个分拣任务。
                    attempts += 1
                    retry_at = now + ack_timeout
                if accepted and now >= poll_at:
                    status = self.status()
                    if on_status:
                        on_status(status)
                    result = self.exchange("RESULT", request.seq)
                    if result.command != "RESULT" or not result.args or result.args[0] != str(request.seq):
                        raise DeviceError("RESULT 回复格式错误")
                    if len(result.args) >= 3 and result.args[1] in ("DONE", "ERR"):
                        recovered = Packet(self.session, request.seq, result.args[1], result.args[2:])
                        self.inbox[request.seq].append(recovered)
                    elif result.args[1:2] == ("UNKNOWN",):
                        raise DeviceError("设备未保留任务结果，需核实物体去向")
                    poll_at = now + 0.5
            raise DeviceError(f"{command} 动作超时；请核实设备与物体状态")
        except TaskCancelled:
            raise
        except Exception:
            # 已经发出的运动结果可能未知，尽力停止且不自动重做。
            try:
                self.stop()
            except Exception:
                pass
            raise
        finally:
            self.inbox.pop(request.seq, None)

    def close(self):
        self.transport.close()
