# Instruction Decoding

A partial 8086 emulator: reads the binary file and disassemble it to match the original source assembly.\
This module assumes the binary files only contains the mov opcode for the following mods: Immediate-To-Register, Reg-To-Reg, Immediate-to-R-8Bits, Immediate-to-R-16Bits, SA-Cal, SA-Cal-8Bit, SA-Cal-16Bits, Dest Address Cal


Step #1: run the examples and verify the assembly is correct by crosschecking it with the same listing numbers shown [here](https://github.com/cmuratori/computer_enhance/tree/main/perfaware/part1)
```bash
python sim8086.py listing_0037
python sim8086.py listing_0038
python sim8086.py listing_0038
```
The output produced:
```bash
listing_0037_py.asm
listing_0038_py.asm
listing_0039_py.asm
```

Step #2: reproduce the binary file using [nasm](https://www.nasm.us/):
```bash
nasm listing_0037_py.asm
nasm listing_0038_py.asm
nasm listing_0039_py.asm
```
The output produced:
```bash
listing_0037_py
listing_0038_py
listing_0039_py
```

Repeat Step #1 but feed the new listings produced by Step #2 to verify that the same assembly instructions are decoded.