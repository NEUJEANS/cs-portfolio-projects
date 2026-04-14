# Review pass 1: stack-vm-lab

- issue found: the factorial sample jumped to the wrong instruction on loop exit, causing stack underflow
- fix applied: corrected the `JIF` target so the program exits to the final `LOAD acc` block
- validation: reran the project test suite and factorial CLI smoke test
