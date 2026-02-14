# A partial and naive 8086 emulator: reads the binary file and disassemble it to match the original source assembly
# This module assumes the binary files only contains the mov opcode and that MOD = 11 (register mode)

import argparse

MOV_BIN = "100010"
MOD_R = "11"

reg_and_rm_field_encoding = {
    "000": {"0": "AL", "1": "AX"},
    "001": {"0": "CL", "1": "CX"},
    "010": {"0": "DL", "1": "DX"},
    "011": {"0": "BL", "1": "BX"},
    "100": {"0": "AH", "1": "SP"},
    "101": {"0": "CH", "1": "BP"},
    "110": {"0": "DH", "1": "SI"},
    "111": {"0": "BH", "1": "DI"},
}

def decode_to_asm(asm_bytes: bytes) -> str:
    # Pulling First Byte...
    bin_inst = bin(asm_bytes[0])[2:]

    opcode = bin_inst[:6]
    if opcode != MOV_BIN:
        raise ValueError("Script currently supports 'mov' opcode only")
    opcode = "mov"

    direction = bin_inst[-2]
    word = bin_inst[-1]

    # Pulling Second Byte...
    bin_inst2 = bin(asm_bytes[1])[2:]
    mod = bin_inst2[:2]

    # Find REG 
    reg = bin_inst2[2:5]
    reg_2_w_map = reg_and_rm_field_encoding.get(reg)
    reg_code = reg_2_w_map.get(word) 

    # Find R/M
    rm_code = ""
    if mod == MOD_R:
        rm = bin_inst2[-3:]
        rm_2_w_map = reg_and_rm_field_encoding.get(rm)
        rm_code = rm_2_w_map.get(word)
    
    if direction == "1":
        return f"{opcode} {reg_code.lower()}, {rm_code.lower()}"
    else:
        return f"{opcode} {rm_code.lower()}, {reg_code.lower()}"


def write_to_file(filename: str, data: str) -> None:
    with open(file=filename, mode="w") as file:
        file.write("bits 16\n\n")
        file.write("\n".join(data))


def main(filename: str):
    asm_bytes = None
    with open(file=filename, mode='rb') as file:
        asm_bytes = file.read()

    if not asm_bytes:
        raise ValueError("Nothing to read from input file.")
        
    asm_inst = []
    for idx in range(0, len(asm_bytes), 2):
        asm_inst.append(decode_to_asm(asm_bytes[idx:idx+2]))
    write_to_file(f"{filename}_py.asm", asm_inst)

            

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", type=str)
    args = parser.parse_args()
    main(args.filename)