# Vector clock Mermaid review pass 1

Focus: implementation + test alignment.

Checks:
- ran `python3 -m unittest discover -s projects/vector-clock-lab -p 'test_*.py' -v`
- inspected failing assertions against the rendered Mermaid output

Issue found:
- sync lines in the Mermaid renderer omitted the source replica label inside the payload summary, while the README/test story expected explicit source context (`profile=c draft-c @ {c:1}`)

Fix applied:
- updated the sync-line renderer to include replica labels in anti-entropy sync messages
- re-ran the vector-clock test suite after the change

Status: fixed
