# A partial 8086 emulator: reads the binary file and disassemble it to match the original source assembly
# This module assumes the binary files only contains the:
# - mov/add/sub/cmp opcode for the following mods: Immediate-To-Register, Reg-To-Reg, Immediate-to-R-8Bits, Immediate-to-R-16Bits, SA-Cal, SA-Cal-8Bit, SA-Cal-16Bits, Dest Address Cal
# - add/sub/cmp additionally for the following mod: Immediate-To-Accumulator
# - jmps

import argparse

MOV_IMMEDIATE_BIN = "1011"
ARITHMETIC_IMM_BIN = "100000"
ADD_OCT_BIN = "000"
SUB_OCT_BIN = "101"
CMP_OCT_BIN = "111"
ARITH_IMM_ACC_BINS = {f"00{op}" for op in (ADD_OCT_BIN, SUB_OCT_BIN, CMP_OCT_BIN)}
MOD_R = "11"

opcode_to_name = {
    "100010": "mov",
    "000000": "add",
    "001010": "sub",
    "001110": "cmp",
}

immediate_to_reg_name_map = {
    "000": "add",
    "101": "sub",
    "111": "cmp",
}

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

JUMP_OPCODES = {
    "01110000": "jo",   "01110001": "jno",
    "01110010": "jb",   "01110011": "jnb",
    "01110100": "je",   "01110101": "jnz",
    "01110110": "jbe",  "01110111": "ja",
    "01111000": "js",   "01111001": "jns",
    "01111010": "jp",   "01111011": "jnp",
    "01111100": "jl",   "01111101": "jnl",
    "01111110": "jle",  "01111111": "jg",
    "11100000": "loopnz", "11100001": "loopz",
    "11100010": "loop",   "11100011": "jcxz",
}

def decode_with_mem(opc_name: str, asm_bytes: bytes) -> str:
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
        return f"{opc_name} {reg_code.lower()}, {rm_code.lower()}"
    else:
        return f"{opc_name} {rm_code.lower()}, {reg_code.lower()}"

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

def decode_arithmetic_immediate(asm_bytes: bytes) -> str:
    """
    Spec: 100000 s w | mod reg r/m | DISP-LO | DISP-HI | data | data if s:w=01
    - Always pull first and second byte.
    - Third and fourth bytes are only pulled depending on MOD type.
    - One data byte if s=1 (sign-extend) or w=0; two data bytes if s=0 and w=1.
    """
    first_byte = bin(asm_bytes[0])[2:].zfill(8)
    second_byte = bin(asm_bytes[1])[2:].zfill(8)

    word = first_byte[-1]
    mod = second_byte[:2]
    rm = second_byte[-3:]

    # Resolve destination (r/m field)
    disp_bytes = mod_bytes_to_fetch[mod]
    if mod == MOD_R:
        rm_code = reg_and_rm_field_encoding[rm][word]
    elif mod == "00":
        if rm == "110":  # direct address: mod=00, r/m=110 is special-cased
            addr = asm_bytes[2] + (asm_bytes[3] << 8)
            rm_code = f"[{addr}]"
            disp_bytes = 2
        else:
            rm_code = f"[{effective_address_map[rm]}]"
    elif mod == "01":
        low_byte = asm_bytes[2]
        ea = effective_address_map[rm]
        rm_code = f"[{ea} + {low_byte}]" if low_byte != 0 else f"[{ea}]"
    elif mod == "10":
        low_byte = asm_bytes[2]
        high_byte = asm_bytes[3]
        ea = effective_address_map[rm]
        rm_code = f"[{ea} + {low_byte + (high_byte << 8)}]"

    # Immediate data starts after the 2 fixed bytes + any displacement bytes
    data_offset = 2 + disp_bytes
    # Size prefix only needed for memory destinations (register implies its own size)
    size_prefix = ("word " if word == "1" else "byte ") if mod != MOD_R else ""

    s = first_byte[-2]
    reg = second_byte[2:5]
    opc_name = immediate_to_reg_name_map[reg]
    # Two data bytes only when s=0 and w=1; s=1 means sign-extend one byte
    if s == "0" and word == "1":
        imm = asm_bytes[data_offset] + (asm_bytes[data_offset + 1] << 8)
        if imm & 0x8000:
            imm -= 65536
    else:
        imm = asm_bytes[data_offset]
        if imm & 0x80:
            imm -= 256
    return f"{opc_name} {size_prefix}{rm_code.lower()}, {imm}"

def decode_arith_accumulator(asm_bytes: bytes) -> str:
    """
    Spec: 00 opc 10 w | data-lo | data-hi (if w=1)
    - Always pull first and second byte.
    - Third byte is only pulled if w=1.
    - Destination is always the accumulator: AL if w=0, AX if w=1.
    """
    first_byte = bin(asm_bytes[0])[2:].zfill(8)
    word = first_byte[-1]

    opc_name = immediate_to_reg_name_map[first_byte[2:5]]
    dest = "ax" if word == "1" else "al"

    if word == "1":
        imm = asm_bytes[1] + (asm_bytes[2] << 8)
        if imm & 0x8000:
            imm -= 65536
    else:
        imm = asm_bytes[1]
        if imm & 0x80:
            imm -= 256

    return f"{opc_name} {dest}, {imm}"

def decode_jump(asm_bytes: bytes) -> str:
    """
    Spec: 8-bit opcode | IP-INC8
    - Always pull two bytes: the opcode and a signed 8-bit offset.
    - Offset is relative to the next instruction (i.e. current instruction size + offset).
    """
    first_byte = bin(asm_bytes[0])[2:].zfill(8)
    opc_name = JUMP_OPCODES[first_byte]
    offset = asm_bytes[1]
    if offset & 0x80:
        offset -= 256
    return f"{opc_name} ${2 + offset:+d}" 

def decode_to_asm(asm_bytes: bytes) -> list[str]:
    """
    Identify opcode and pull # of bytes needed to decode entire instruction
    """
    i = 0
    instructions = []
    while i < len(asm_bytes):
        instruction = bin(asm_bytes[i])[2:].zfill(8)

        # MOV/ADD/SUB/CMP from reg/memory to register
        if opc_name := opcode_to_name.get(instruction[:6], None):
            second_byte = bin(asm_bytes[i+1])[2:].zfill(8)
            mod = second_byte[:2]
            bytes_to_fetch = 2 + mod_bytes_to_fetch.get(mod)
            instructions.append(decode_with_mem(opc_name, asm_bytes[i:i+bytes_to_fetch]))

        # MOV immediate to register
        elif instruction[:4] == MOV_IMMEDIATE_BIN:
            # Pull w to see if one or two bytes of data are needed
            w = instruction[4]
            bytes_to_fetch = 2 + int(w)
            instructions.append(decode_mov_immediate(asm_bytes[i:i+bytes_to_fetch]))

        # ADD/SUB/CMP immediate to register/memory
        elif instruction[:6] == ARITHMETIC_IMM_BIN:
            second_byte = bin(asm_bytes[i+1])[2:].zfill(8)
            mod = second_byte[:2]
            rm = second_byte[-3:]
            w = instruction[-1]
            s = instruction[-2]
            data_bytes = 2 if (s == "0" and w == "1") else 1
            disp_bytes = 2 if (mod == "00" and rm == "110") else mod_bytes_to_fetch[mod]
            bytes_to_fetch = 2 + disp_bytes + data_bytes
            instructions.append(decode_arithmetic_immediate(asm_bytes[i:i+bytes_to_fetch]))

        # ADD/SUB/CMP immediate to accumulator
        elif instruction[:5] in ARITH_IMM_ACC_BINS:
            # Pull w to see if one or two bytes of data are needed
            w = instruction[-1]
            bytes_to_fetch = 2 + int(w)
            instructions.append(decode_arith_accumulator(asm_bytes[i:i+bytes_to_fetch]))

        # Jumps
        elif instruction in JUMP_OPCODES: 
            bytes_to_fetch = 2
            instructions.append(decode_jump(asm_bytes[i:i+bytes_to_fetch]))

        else:
            raise ValueError(f"Instruction decoding is not supported for {instruction} at index {i}")

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