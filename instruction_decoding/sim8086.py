# A partial 8086 emulator: reads the binary file and disassemble it to match the original source assembly
# This module assumes the binary files only contains the mov opcode for the following mods: Immediate-To-Register, Reg-To-Reg, Immediate-to-R-8Bits, Immediate-to-R-16Bits, SA-Cal, SA-Cal-8Bit, SA-Cal-16Bits, Dest Address Cal

import argparse

MOV_BIN = "100010"
MOV_IMMEDIATE_BIN = "1011"
MOD_R = "11"

mod_bytes_to_fetch = {
    "00": 0,
    "01": 1,
    "10": 2,
    "11": 0,
}

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

effective_address_map = {
    "000": "BX + SI",
    "001": "BX + DI",
    "010": "BP + SI",
    "011": "BP + DI",
    "100": "SI",
    "101": "DI",
    "110": "BP",
    "111": "BX",
}

def decode_mov(asm_bytes: bytes) -> str:
    """
    Spec: 100010 d w | mod reg r/m | DISP-LO | DISP-HI
    - Always pull first and second byte.
    - Third and fourth bytes are only pulled depending on MOD type.
    """
    first_byte = bin(asm_bytes[0])[2:].zfill(8)
    direction = first_byte[-2]
    word = first_byte[-1]

    second_byte = bin(asm_bytes[1])[2:].zfill(8)

    # Find REG 
    reg = second_byte[2:5]
    reg_2_w_map = reg_and_rm_field_encoding.get(reg)
    reg_code = reg_2_w_map.get(word) 

    # Find R/M
    mod = second_byte[:2]
    rm = second_byte[-3:]
    if mod == MOD_R:
        rm_2_w_map = reg_and_rm_field_encoding.get(rm)
        rm_code = rm_2_w_map.get(word)
    elif mod == "00":
        rm_code = effective_address_map.get(rm)
        rm_code = f"[{rm_code}]"
    elif mod == "01":
        rm_code = effective_address_map.get(rm)
        low_byte = asm_bytes[2]
        rm_code = f"[{rm_code} + {low_byte}]" if low_byte != 0 else f"[{rm_code}]"
    elif mod == "10":
        rm_code = effective_address_map.get(rm)
        low_byte = asm_bytes[2]
        high_byte = asm_bytes[3]
        rm_code = f"[{rm_code} + {low_byte + (high_byte << 8)}]"

    if direction == "1":
        return f"mov {reg_code.lower()}, {rm_code.lower()}"
    else:
        return f"mov {rm_code.lower()}, {reg_code.lower()}"

def decode_mov_immediate(asm_bytes: bytes) -> str:
    """
    Spec: 1011 w reg
    - Pull one data byte if w = 0
    - Pull two data bytes if w = 1
    """
    first_byte = bin(asm_bytes[0])[2:].zfill(8)
    word = first_byte[4]

    reg = first_byte[5:]
    reg_2_w_map = reg_and_rm_field_encoding.get(reg)
    reg_code = reg_2_w_map.get(word) 

    if word == "1":
        value = asm_bytes[1] + (asm_bytes[2] << 8)
        if value & 0x8000:
            value -= 65536
    else:
        value = asm_bytes[1]
        if value & 0x80:
            value -= 256

    return f"mov {reg_code.lower()}, {value}"

def decode_to_asm(asm_bytes: bytes) -> list[str]:
    """
    Identify opcode and pull # of bytes needed to decode entire instruction
    """
    i = 0
    instructions = []
    while i < len(asm_bytes):
        instruction = bin(asm_bytes[i])[2:].zfill(8)

        if instruction[:6] == MOV_BIN:
            second_byte = bin(asm_bytes[i+1])[2:].zfill(8)
            # Pull mod to check if one or two displacement bytes are needed 
            mod = second_byte[:2]
            bytes_to_fetch = 2 + mod_bytes_to_fetch.get(mod)
            instructions.append(decode_mov(asm_bytes[i:i+bytes_to_fetch]))

        elif instruction[:4] == MOV_IMMEDIATE_BIN:
            # Pull w to see if one or two bytes of data are needed
            w = instruction[4]
            bytes_to_fetch = 2 + int(w)
            instructions.append(decode_mov_immediate(asm_bytes[i:i+bytes_to_fetch]))
        
        else: 
            raise ValueError(f"Instruction decoding is not supported for {instruction}")

        i += bytes_to_fetch

    return instructions

def write_to_file(filename: str, data: str) -> None:
    with open(file=filename, mode="w") as file:
        file.write("bits 16\n\n")
        file.write("\n".join(data))


def main(filename: str) -> None:
    asm_bytes = None
    with open(file=filename, mode='rb') as file:
        asm_bytes = file.read()

    if not asm_bytes:
        raise ValueError("Nothing to read from input file.")
        
    asm_inst = decode_to_asm(asm_bytes)
    write_to_file(f"{filename}_py.asm", asm_inst)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", type=str)
    args = parser.parse_args()
    main(args.filename)