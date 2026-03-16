# Simulating what the MOV instruction does

import argparse
from collections import defaultdict
from instruction_decoding.sim8086 import decode_to_asm

MOV = "mov"
ADD = "add"
SUB = "sub"
CMP = "cmp"

register_store = defaultdict(int)

def is_immediate(s) -> bool:
    try:
        int(s)
        return True
    except ValueError:
        return False

def debug_asm(instructions: list[str]) -> list[str]:
    for idx in range(len(instructions)):
        opcode = instructions[idx][:3]
        reg_dest, src = instructions[idx][4:].split(", ")

        src_val = (int(src) if is_immediate(src) else register_store[src]) & 0xFFFF

        if is_immediate(src):
            instructions[idx] = instructions[idx].replace(src, str(src_val))

        old_val = register_store[reg_dest]

        if opcode == MOV:
            register_store[reg_dest] = src_val
        elif opcode == ADD:
            register_store[reg_dest] = (old_val + src_val) & 0xFFFF
        elif opcode == SUB:
            register_store[reg_dest] = (old_val - src_val) & 0xFFFF

        if opcode in (MOV, ADD, SUB):
            instructions[idx] += f" ; {reg_dest}:{hex(old_val)}->{hex(register_store[reg_dest])}"

        # Handle flags
        if opcode in (ADD, SUB):
            new_val = register_store[reg_dest]
            if new_val == 0:
                instructions[idx] += " flags:->Z"
            elif new_val >= 0x8000:
                instructions[idx] += " flags:->S"

        if opcode == CMP:
            cmp_val = (old_val - src_val) & 0xFFFF
            new_inst = f"{instructions[idx]} ; flags:"
            instructions[idx] = f"{new_inst}->Z" if cmp_val == 0 else \
                                 f"{new_inst}->S" if cmp_val >= 0x8000 else \
                                 f"{new_inst}S->"

    instructions.append("\nFinal registers:")
    instructions.extend([f"\t{k}: {hex(v)} ({v})" for k, v in register_store.items() if v != 0])

    return instructions


def write_to_file(filename: str, data: list[str]) -> None:
    with open(file=filename, mode="w") as file:
        file.write("bits 16\n\n")
        file.write("\n".join(data))


def main(filename: str, debug: bool = False) -> None:
    asm_bytes = None
    with open(file=filename, mode='rb') as file:
        asm_bytes = file.read()

    if not asm_bytes:
        raise ValueError("Nothing to read from input file.")
        
    asm_inst = decode_to_asm(asm_bytes)
    if debug:
        asm_inst = debug_asm(asm_inst)
    write_to_file(f"{filename}_py.asm", asm_inst)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", type=str)
    parser.add_argument("--debug", action="store_true", default=False)
    args = parser.parse_args()
    main(args.filename, args.debug)
