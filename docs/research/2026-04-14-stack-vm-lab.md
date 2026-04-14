# Research notes: stack-vm-lab

## Why this project now
The repo already covers many practical CLIs, data structures, and storage/distributed-systems labs. A tiny stack VM adds language-runtime depth and gives a strong "how interpreters work" portfolio story without needing a full compiler.

## Brief external pointers
- educational stack machines emphasize a fetch/decode/execute loop, an operand stack, and a separate call-frame stack
- the most useful first instruction set for a student portfolio is small but expressive: push/load/store, arithmetic, comparisons, jumps, calls, returns, and output
- keeping the program text human-readable makes the architecture easy to inspect and explain in interviews

## Minimal vertical slice chosen
For this run, the goal is a readable assembly-like VM that demonstrates:
- a parser for simple function-based programs
- operand-stack execution with locals
- control flow via `JIF` and `JMP`
- function calls with `arg0`, `arg1`, ... locals and return values
- short execution traces so users can inspect state changes step by step

## Deliberate simplifications
- raw instruction indexes are used instead of labels
- values are mostly integers/booleans/strings rather than a full type system
- sample programs act as the "compiler output"
- JSON summaries are preferred over an interactive debugger for this slice

## Next directions if expanded later
- add labels and an assembler pass
- compile a tiny expression language into VM code
- add typed values, heap objects, and arrays
- benchmark dispatch overhead and compare switch vs table-driven execution
