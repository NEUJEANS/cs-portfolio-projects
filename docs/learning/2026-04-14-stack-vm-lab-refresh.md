# Refresh + self-test: stack-vm-lab

## Quick refresh
- stack-based VMs keep intermediate values on an operand stack instead of named registers
- a call frame usually stores the current function's locals plus the return address
- conditional jumps are enough to build `if` statements and loops
- an interpreter repeatedly fetches the next instruction, decodes it, updates VM state, and advances the instruction pointer

## Self-test
1. Why keep call frames separate from the operand stack?
   - So function scope and return addresses remain structured even while expression values are pushed and popped rapidly.
2. Why is a small instruction set better than a huge one for this kind of portfolio project?
   - It makes the execution model easier to reason about while still proving the core interpreter concepts.
3. What does `JIF` do in this project?
   - It pops a condition and jumps when that condition is false, which is enough to implement branching and loops.
4. Why are execution traces useful here?
   - They let you show exactly how stack values and locals change across instructions during debugging or interviews.
