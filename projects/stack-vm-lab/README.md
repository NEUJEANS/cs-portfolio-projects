# Stack VM Lab

A compact stack-based virtual machine that executes a tiny assembly-like language with arithmetic, locals, branching, and function calls.

## Why this project is portfolio-worthy
- demonstrates how interpreters work below the level of an ordinary app framework
- turns core CS topics like stacks, call frames, control flow, and bytecode-style execution into a runnable artifact
- gives strong interview material around fetch/decode/execute loops, VM state, and instruction-set design
- stays small enough to understand quickly while still showing non-trivial systems thinking

## Features
- small assembly parser organized into named functions
- operand stack plus per-function local variables
- arithmetic and comparison instructions
- conditional and unconditional jumps
- function calls with argument passing through call frames
- JSON CLI output for execution summaries and short traces
- bundled sample programs for factorial loops and function-call control flow

## Project structure
- `stack_vm_lab.py` - parser, VM runtime, samples, and CLI
- `test_stack_vm_lab.py` - unit + CLI tests

## Usage
Run from this directory.

### Execute the factorial sample
```bash
python3 stack_vm_lab.py sample factorial
```

### Execute the max function-call sample
```bash
python3 stack_vm_lab.py sample max2
```

### Disassemble a program file
```bash
python3 stack_vm_lab.py disassemble examples/max2.svm
```

### Run your own program
```bash
python3 stack_vm_lab.py run program.svm --trace-limit 10
```

## Testing
```bash
python3 -m unittest discover -s projects/stack-vm-lab -p 'test_*.py' -v
```

## Interview talking points
- why stack machines use push/pop operations instead of explicit registers
- how call frames preserve return addresses and function-local scope
- where an interpreter loop spends time and what optimizations usually come next
- how adding labels, a compiler front end, or typed values would evolve this into a stronger language-runtime project

## Future improvements
- add symbolic labels instead of raw instruction indexes
- compile a tiny expression language into the VM instruction set
- add typed values and better runtime error messages
- expose instruction-count benchmarking across sample programs
