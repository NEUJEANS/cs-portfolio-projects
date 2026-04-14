# Review pass 3: stack-vm-lab

- issue found: `parse_program()` split tokens naively, so quoted strings containing spaces were broken into multiple arguments
- fix applied: switched parsing to `shlex.split()` and added a regression test for `PUSH "hello vm"`
- validation: reran the full test suite after the parser change
