# Simulating what the MOV instruction does

import argparse
from instruction_decoding.sim8086 import decode_to_asm

register_store = {
    "ax": 0,
    "bx": 0,
    "cx": 0,
    "dx": 0,
    "sp": 0,
    "bp": 0,
    "si": 0,
    "di": 0,
}

def debug_mov(instructions: list[str]) -> list[str]:
    for idx in range(len(instructions)):
        data = instructions[idx][4:]  # remove 'mov '
        reg_dest, src = data.split(", ")
        src_val = int(src) if src.isdigit() else register_store[src]

        instructions[idx] = f"{instructions[idx]} ; {reg_dest}:{hex(register_store[reg_dest])}->{hex(src_val)}"
        register_store[reg_dest] = src_val

    # Print final registers
    instructions.append("\nFinal registers:")
    instructions.extend([f"\t{k}: {hex(v)} ({v})" for k, v in register_store.items()])
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
        asm_inst = debug_mov(asm_inst)
    write_to_file(f"{filename}_py.asm", asm_inst)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", type=str)
    parser.add_argument("--debug", action="store_true", default=False)
    args = parser.parse_args()
    main(args.filename, args.debug)
