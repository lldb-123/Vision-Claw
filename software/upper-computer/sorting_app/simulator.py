"""可读的 STM32 协议参考实现，不控制真实设备。"""
from collections import deque
import secrets
import time
from .protocol import Packet, FrameDecoder

class MockSTM32:
    def __init__(self, duration=0.35, drop_first_ack=False, drop_first_done=False, fail_sort=False):
        self.duration = duration
        self.drop_first_ack = drop_first_ack
        self.drop_first_done = drop_first_done
        self.fail_sort = fail_sort
        self.boot_id = secrets.token_hex(4).upper()
        self.session = None
        self.homed = False
        self.state = "UNHOMED"
        self.active = None
        self.records = {}
        self.outbox = deque()
        self.sort_executions = 0
        self.highest_seq = 0

    def reply(self, request, command, *args):
        return Packet(request.session, request.seq, command, tuple(map(str, args)))

    def emit(self, packet):
        if packet.command == "ACK" and packet.args == ("SORT",) and self.drop_first_ack:
            self.drop_first_ack = False
            return
        if packet.command == "DONE" and packet.args[:1] == ("SORT",) and self.drop_first_done:
            self.drop_first_done = False
            return
        self.outbox.append(packet.encode())

    def handle(self, request):
        self.tick()
        if request.command == "HELLO" and self.session != request.session:
            if self.active:
                self.emit(self.reply(request, "ERR", "HELLO", "REJECTED", "BUSY"))
                return
            self.session = request.session
            self.records.clear()
            self.highest_seq = 0
        if request.session != self.session:
            self.emit(self.reply(request, "ERR", request.command, "REJECTED", "SESSION_MISMATCH"))
            return
        if request.seq in self.records:
            original, result = self.records[request.seq]
            self.emit(result if original == request else self.reply(request, "ERR", request.command, "REJECTED", "ID_CONFLICT"))
            return
        if request.seq <= self.highest_seq:
            self.emit(self.reply(request, "ERR", request.command, "REJECTED", "STALE_ID"))
            return
        self.highest_seq = request.seq
        command, args = request.command, request.args
        result = None
        try:
            counts = {"HELLO": 0, "HOME": 0, "SORT": 3, "STATUS": 0, "RESULT": 1, "STOP": 0, "CLEAR_FAULT": 0}
            if command not in counts or len(args) != counts[command]:
                raise ValueError("BAD_COMMAND")
            if command == "HELLO":
                result = self.reply(request, "DONE", "HELLO", self.boot_id, self.state, int(self.homed))
            elif command == "STATUS":
                result = self.reply(request, "STATUS", self.state, self.active[0].seq if self.active else 0,
                                    int(self.homed), self.boot_id)
            elif command == "RESULT":
                record = self.records.get(int(args[0]))
                if record and record[0].command in ("HOME", "SORT", "STOP", "CLEAR_FAULT"):
                    prior = record[1]
                    result = self.reply(request, "RESULT", args[0], prior.command, *prior.args)
                else:
                    result = self.reply(request, "RESULT", args[0], "UNKNOWN")
            elif command == "STOP":
                if self.active:
                    active_request = self.active[0]
                    aborted = self.reply(active_request, "ERR", active_request.command, "FAILED", "ABORTED")
                    self.records[active_request.seq] = (active_request, aborted)
                    self.emit(aborted)
                    self.active = None
                    self.homed = False
                self.state = "UNHOMED" if not self.homed else "IDLE"
                result = self.reply(request, "DONE", "STOP")
            elif command == "CLEAR_FAULT":
                if self.active:
                    raise ValueError("BUSY")
                self.state = "UNHOMED"
                self.homed = False
                result = self.reply(request, "DONE", "CLEAR_FAULT")
            else:
                if self.active:
                    raise ValueError("BUSY")
                if self.state == "FAULT":
                    raise ValueError("FAULT_ACTIVE")
                if command == "SORT":
                    if not self.homed:
                        raise ValueError("NOT_HOMED")
                    x, y, box = map(int, args)
                    if not (0 <= x <= 26000 and 0 <= y <= 26000 and 1 <= box <= 6):
                        raise ValueError("OUT_OF_RANGE")
                    self.sort_executions += 1
                self.state = "RUNNING"
                self.active = (request, time.monotonic() + self.duration)
                result = self.reply(request, "ACK", command)
        except ValueError as exc:
            code = str(exc) if str(exc).isupper() else "BAD_ARGUMENT"
            result = self.reply(request, "ERR", command, "REJECTED", code)
        self.records[request.seq] = (request, result)
        self.emit(result)

    def tick(self):
        if self.active and time.monotonic() >= self.active[1]:
            request = self.active[0]
            self.active = None
            if request.command == "SORT" and self.fail_sort:
                self.state = "FAULT"
                result = self.reply(request, "ERR", "SORT", "FAILED", "DROP_TIMEOUT")
            else:
                self.state = "IDLE"
                self.homed = True
                result = self.reply(request, "DONE", request.command, *(["ENTRY_VERIFIED"] if request.command == "SORT" else []))
            self.records[request.seq] = (request, result)
            self.emit(result)

class MockTransport:
    def __init__(self, device=None):
        self.device = device or MockSTM32()
        self.decoder = FrameDecoder()

    def write(self, data):
        for packet in self.decoder.feed(data):
            self.device.handle(packet)

    def read(self):
        self.device.tick()
        if self.device.outbox:
            return self.device.outbox.popleft()
        time.sleep(0.005)
        return b""

    def close(self):
        pass
