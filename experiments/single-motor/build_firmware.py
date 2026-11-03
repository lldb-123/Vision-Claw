"""Assemble a tiny Cortex-M4 firmware without installing a full IDE."""
from pathlib import Path
import struct
import json
from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB, KS_MODE_LITTLE_ENDIAN
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS
from intelhex import IntelHex

ROOT = Path(__file__).resolve().parent
FLASH = 0x08000000
CODE = FLASH + 0x200
STACK = 0x20020000

def build():
    asm = (ROOT / 'motor_test.s').read_text(encoding='utf-8')
    # Keystone does not accept C block comments or GNU mode directives.
    import re
    asm = re.sub(r'/\*.*?\*/', '', asm, flags=re.S)
    asm = '\n'.join(line for line in asm.splitlines() if not line.strip().startswith('.'))
    machine, count = Ks(KS_ARCH_ARM, KS_MODE_THUMB | KS_MODE_LITTLE_ENDIAN).asm(asm, addr=CODE)
    code = bytes(machine)
    instructions = list(Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS).disasm(code, CODE))
    # The final five instructions form fault_handler; resolve their actual addresses.
    fault = instructions[-5].address
    assert instructions[-1].mnemonic == 'b'
    vectors = [STACK, CODE | 1] + [fault | 1] * 126
    blob = struct.pack('<128I', *vectors) + code
    (ROOT / 'motor_test.bin').write_bytes(blob)
    hexfile = IntelHex()
    hexfile.frombytes(blob, offset=FLASH)
    hexfile.start_addr = {'EIP': CODE | 1}
    hexfile.write_hex_file(str(ROOT / 'motor_test.hex'))
    listing = '\n'.join(f'{i.address:08X}  {i.bytes.hex():12s}  {i.mnemonic:8s} {i.op_str}' for i in instructions)
    (ROOT / 'motor_test.lst').write_text(listing + '\n', encoding='utf-8')
    metadata = {'flash': FLASH, 'entry': CODE | 1, 'stack': STACK, 'bytes': len(blob),
                'instructions': len(instructions), 'fault_handler': fault | 1,
                'step': 'PA0', 'direction': 'PA1', 'enable_active_low': 'PA4',
                'mode': 'continuous', 'pulse_high_ms': 1, 'pulse_low_ms': 4,
                'step_frequency_hz': 200,
                'startup_ramp': '50 Hz to 200 Hz in approximately 2 seconds',
                'stop': 'Disconnect motor power; RESET starts rotation again'}
    (ROOT / 'firmware_info.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print(json.dumps(metadata))

if __name__ == '__main__':
    build()
