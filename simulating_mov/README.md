# Simulating MOV

Extends the instruction decoder to simulate what MOV instructions do: tracks register state and annotates each instruction with before/after values.

Step #1: run the examples and verify the assembly is correct by crosschecking it with the same listing numbers shown [here](https://github.com/cmuratori/computer_enhance/tree/main/perfaware/part1)
```bash
PYTHONPATH=./ python simulating_mov/sim8086.py simulating_mov/listing_0043
PYTHONPATH=./ python simulating_mov/sim8086.py simulating_mov/listing_0044
```
The output produced:
```bash
simulating_mov/listing_0043_py.asm
simulating_mov/listing_0044_py.asm
```

Pass `--debug` to annotate each instruction with register state changes and print final register values:
```bash
PYTHONPATH=./ python simulating_mov/sim8086.py simulating_mov/listing_0043 --debug
```

Step #2: reproduce the binary file using [nasm](https://www.nasm.us/):
```bash
nasm simulating_mov/listing_0043_py.asm
nasm simulating_mov/listing_0044_py.asm
```

Repeat Step #1 but feed the new listings produced by Step #2 to verify that the same assembly instructions are decoded.
