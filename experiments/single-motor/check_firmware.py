"""Check GPIO sequencing in a Cortex-M4 CPU emulator, not physical hardware."""
from pathlib import Path
import json, struct
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_MODE_MCLASS, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE, UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_SP, UC_ARM_REG_PC

ROOT = Path(__file__).resolve().parent
info = json.loads((ROOT / 'firmware_info.json').read_text())
firmware = (ROOT / 'motor_test.bin').read_bytes()
mu = Uc(UC_ARCH_ARM, UC_MODE_THUMB | UC_MODE_MCLASS)
mu.mem_map(0x08000000, 0x80000)
mu.mem_write(0x08000000, firmware)
mu.mem_map(0x20000000, 0x20000)
mu.mem_map(0x40000000, 0x30000)
mu.mem_map(0xe000e000, 0x1000)
mu.mem_write(0x40020000, struct.pack('<I', 0xa8000000))
mu.reg_write(UC_ARM_REG_SP, info['stack'])
state = {'odr': 0, 'rising_steps': 0, 'enabled_steps': 0,
         'ever_enabled': False, 'disabled_after_run': False, 'systick_ms': 0,
         'enable_start_ms': None, 'enable_end_ms': None, 'ticks_at_step': [],
         'ticks_at_fall': []}

def on_read(uc, access, addr, size, value, data):
    if addr == 0x40023800:
        old = struct.unpack('<I', uc.mem_read(addr, 4))[0]
        uc.mem_write(addr, struct.pack('<I', old | 3))
    elif addr == 0xe000e010:
        # Model an elapsed SysTick period; no host-time/timing claim.
        uc.mem_write(addr, struct.pack('<I', 0x10005))
        state['systick_ms'] += 1

def on_write(uc, access, addr, size, value, data):
    if addr != 0x40020018:
        return
    old = state['odr']
    new = (old | (value & 0xffff)) & ~((value >> 16) & 0xffff)
    state['odr'] = new
    if old & 16 and not new & 16:
        state['ever_enabled'] = True
        state['enable_start_ms'] = state['systick_ms']
    if state['ever_enabled'] and not old & 16 and new & 16:
        state['disabled_after_run'] = True
        state['enable_end_ms'] = state['systick_ms']
    if not old & 1 and new & 1:
        state['rising_steps'] += 1
        state['enabled_steps'] += not bool(new & 16)
        state['ticks_at_step'].append(state['systick_ms'])
    if old & 1 and not new & 1:
        state['ticks_at_fall'].append(state['systick_ms'])
        if len(state['ticks_at_fall']) == 650:
            uc.emu_stop()

visits = {}
def on_code(uc, addr, size, data):
    opcode = bytes(uc.mem_read(addr, 2))
    if opcode == b'\xfe\xe7':
        visits[addr] = visits.get(addr, 0) + 1
        if visits[addr] >= 10:
            uc.emu_stop()

mu.hook_add(UC_HOOK_MEM_READ, on_read)
mu.hook_add(UC_HOOK_MEM_WRITE, on_write)
mu.hook_add(UC_HOOK_CODE, on_code)
mu.emu_start(info['entry'], 0x08000000 + len(firmware), count=1000000)
moder = struct.unpack('<I', mu.mem_read(0x40020000, 4))[0]
assert state['rising_steps'] == state['enabled_steps'] == 650, state
assert state['ever_enabled'] and not state['disabled_after_run'], state
assert not state['odr'] & 0x13, state
assert moder & ~0x30f == 0xa8000000, hex(moder)
assert moder & 0x30f == 0x105, hex(moder)
assert state['ticks_at_step'][0] - state['enable_start_ms'] == 5, state
assert all(fall-rise == 1 for rise,fall in zip(state['ticks_at_step'], state['ticks_at_fall'])), state
intervals = [b-a for a,b in zip(state['ticks_at_step'], state['ticks_at_step'][1:])]
assert intervals[0] == 20 and min(intervals) == 5, state
assert all(a >= b >= 5 for a,b in zip(intervals, intervals[1:])), state
assert intervals[-499:] == [5] * 499, state
state['check'] = 'PASS: continuous rotation, 50-to-200 Hz ramp, 1ms pulse width, fixed direction, SWD preserved'
state['scope'] = 'CPU/GPIO sequencing with mocked peripherals; real timing and motor not verified'
(ROOT / 'verification.json').write_text(json.dumps(state, indent=2), encoding='utf-8')
print(state['check'])
