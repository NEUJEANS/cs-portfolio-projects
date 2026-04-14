# Wrap-up: stack-vm-lab

- Timestamp: 2026-04-14T18:37:00Z
- Project: stack-vm-lab
- Commit: 82ed8fa

## What changed
- added a new language-runtime portfolio project: a tiny stack-based virtual machine with a parser, operand stack, locals, branching, function calls, and JSON CLI output
- included bundled/sample programs plus a real example file so the docs stay runnable
- added research notes, a VM/interpreter refresh sheet, a dedicated checklist, and three review-pass logs
- updated the repo README so the new project appears in the overall progress list

## Tests run
- `python3 -m unittest discover -s projects/stack-vm-lab -p 'test_*.py' -v`
- `python3 projects/stack-vm-lab/stack_vm_lab.py sample factorial --trace-limit 5`
- `python3 projects/stack-vm-lab/stack_vm_lab.py sample max2 --trace-limit 5`

## Reviews run
- review pass 1: fixed the factorial sample's wrong exit jump that caused stack underflow
- review pass 2: added the missing `examples/max2.svm` file referenced by the README
- review pass 3: switched parsing to `shlex.split()` and added a regression test for quoted strings with spaces

## Secret scan
- `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`
- result: clean

## Next step
- add either symbolic labels/assembler support to this VM line or a complementary runtime-heavy project such as a tiny HTTP proxy cache or bytecode compiler front end
