#!/usr/bin/env python3
"""Orange Pi host controller for the VisionClaw STM32 text protocol."""
from __future__ import annotations
import json, os, queue, threading, time
from dataclasses import dataclass, field
from typing import Any

try:
    import serial
except ImportError:
    serial = None

@dataclass
class ControllerState:
    connected: bool = False
    simulation: bool = True
    last_reply: str = ""
    last_error: str = ""
    updated_at: float = field(default_factory=time.time)
    axes: dict[str, dict[str, Any]] = field(default_factory=lambda: {
        "X": {"pos_steps": 0, "pos_mm": 0.0, "target": 0, "state": 0, "enabled": 1, "homed": 0, "min": 0, "max": 0},
        "Y": {"pos_steps": 0, "pos_mm": 0.0, "target": 0, "state": 0, "enabled": 1, "homed": 0, "min": 0, "max": 0},
    })
    z: dict[str, Any] = field(default_factory=lambda: {"pulse_us": 1500, "target_us": 1500, "enabled": 1, "busy": 0, "estop": 0, "feedback": "NONE"})
    tray: dict[str, Any] = field(default_factory=lambda: {"state": 0, "direction": 0, "speed": 0, "pulse_us": 1500, "remaining_ms": 0, "feedback": "OPEN_LOOP"})

class Controller:
    def __init__(self, device: str = "/dev/ttyS3", baud: int = 115200, simulation: bool = False, poll_s: float = 1.0):
        self.device, self.baud, self.poll_s = device, baud, poll_s
        self.simulation = simulation or serial is None
        self.state = ControllerState(simulation=self.simulation)
        self._lock = threading.RLock(); self._port = None; self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._commands: queue.Queue[str] = queue.Queue()
        self._thread.start()

    def snapshot(self):
        with self._lock:
            return json.loads(json.dumps(self.state.__dict__))

    def send(self, command: str) -> str:
        command = " ".join(command.strip().split())
        if not command or len(command) > 120: raise ValueError("invalid command")
        self._commands.put(command); return "QUEUED"

    def close(self): self._stop.set(); self._thread.join(timeout=2); self._close_port()

    def _open_port(self):
        if self.simulation: return
        try:
            if serial and self._port is None: self._port = serial.Serial(self.device, self.baud, timeout=0.8)
            with self._lock: self.state.connected = True; self.state.last_error = ""
        except Exception as exc:
            with self._lock: self.state.connected = False; self.state.last_error = str(exc)
            time.sleep(2)

    def _close_port(self):
        if self._port:
            try: self._port.close()
            except Exception: pass
            self._port = None

    def _run(self):
        next_status = 0.0
        while not self._stop.is_set():
            if not self.simulation: self._open_port()
            now = time.monotonic()
            if now >= next_status:
                self._execute("STATUS"); next_status = now + self.poll_s
            try: command = self._commands.get(timeout=0.05)
            except queue.Empty: continue
            self._execute(command)

    def _execute(self, command: str):
        try:
            reply = self._simulate(command) if self.simulation else self._serial(command)
            self._parse(reply)
        except Exception as exc:
            with self._lock: self.state.last_error = str(exc); self.state.updated_at = time.time()

    def _serial(self, command: str) -> str:
        if not self._port: return "ERR SERIAL_DISCONNECTED"
        self._port.write((command + "\r\n").encode()); lines=[]
        deadline=time.monotonic()+1.2
        while time.monotonic()<deadline:
            line=self._port.readline().decode(errors="replace").strip()
            if line: lines.append(line)
            if line.startswith(("ACK", "ERR")): break
        return "\n".join(lines) or "ERR TIMEOUT"

    def _simulate(self, command: str) -> str:
        p=command.split(); c=p[0].upper() if p else ""
        with self._lock:
            if c == "STATUS":
                a=[]
                for axis in ("X","Y"):
                    x=self.state.axes[axis]; a.append(f"STATUS {axis} pos_steps={x['pos_steps']} pos_mm={x['pos_mm']:.2f} target={x['target']} state={x['state']} enabled={x['enabled']} homed={x['homed']} min=0 max=0")
                z=self.state.z; t=self.state.tray
                return "\n".join(a+[f"STATUS Z pulse_us={z['pulse_us']} target_us={z['target_us']} enabled={z['enabled']} busy=0 estop={z['estop']} feedback=NONE", f"STATUS TRAY state={t['state']} dir={t['direction']} speed={t['speed']} pulse_us={t['pulse_us']} remaining_ms=0 feedback=OPEN_LOOP"])
            if c in ("ESTOP",): self.state.z["estop"]=1; return "ACK"
            if c == "CLEAR": self.state.z["estop"]=0; return "ACK"
            if c in ("ENABLE", "DISABLE"): return "ACK"
            if c in ("MOVE_MM", "GOTO_MM") and len(p)>=4:
                axis=p[1].upper(); value=float(p[2]); x=self.state.axes.get(axis)
                if x: x["pos_mm"] = value if c=="GOTO_MM" else x["pos_mm"]+value; x["pos_steps"]=round(x["pos_mm"]*80); x["target"]=x["pos_steps"]
                return "ACK"
            return "ACK"

    def _parse(self, reply: str):
        with self._lock:
            self.state.last_reply = reply; self.state.updated_at = time.time()
            for line in reply.splitlines():
                p=line.split()
                if len(p)<3 or p[0] != "STATUS": continue
                kind=p[1]
                values={k:self._value(v) for k,v in (item.split("=",1) for item in p[2:] if "=" in item)}
                if kind in self.state.axes: self.state.axes[kind].update(values)
                elif kind == "Z": self.state.z.update(values)
                elif kind == "TRAY": self.state.tray.update(values)
            if reply.startswith("ERR"): self.state.last_error=reply
            elif reply.startswith("ACK"): self.state.last_error=""

    @staticmethod
    def _value(value: str):
        try: return float(value) if "." in value else int(value)
        except ValueError: return value
