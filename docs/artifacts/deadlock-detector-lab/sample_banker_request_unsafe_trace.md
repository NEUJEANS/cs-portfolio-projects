# Banker's algorithm request trace

- Source: `projects/deadlock-detector-lab/sample_banker_request_unsafe.json`
- Process: `P0`
- Request: `A=0, B=0, C=2`
- Granted: no
- Reason: request would move the system into an unsafe state
- Safe after trial: no
- Safe sequence: none
- Evaluated available vector: `A=3, B=3, C=0`
- Blocking summary: `P0` needs A=4, B=1, C=1; `P1` needs C=2; `P2` needs A=3; `P3` needs C=1; `P4` needs A=1, C=1

## Trial safety trace

| Step | Chosen process | Runnable set | Work before | Remaining need | Allocation released | Work after |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | none | none | n/a | n/a | n/a | n/a |
