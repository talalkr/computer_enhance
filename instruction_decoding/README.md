# Instruction Decoding

A partial and naive 8086 emulator: reads the binary file and disassemble it to match the original source assembly.\
This module assumes the binary files only contains the mov opcode and that MOD = 11 (register mode).


Run both examples and verify the assembly is correct by crosschecking it with the same listing numbers shown [here](https://github.com/cmuratori/computer_enhance/tree/main/perfaware/part1)
```bash
python sim8086.py listing_0037_py
python sim8086.py listing_0038_py
```

Reproduce the binary file using [nasm](https://www.nasm.us/):
```bash
nasm listing_0037_py.asm
nasm listing_0038_py.asm
```
Feed those files into the python script to verify that the same assembly instructions are generated.