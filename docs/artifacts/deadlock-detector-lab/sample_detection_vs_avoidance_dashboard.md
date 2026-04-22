# Deadlock detection vs avoidance dashboard

- Wait-for graph source: `projects/deadlock-detector-lab/sample_wait_graph.json`
- Allocation snapshot source: `projects/deadlock-detector-lab/sample_allocation_state.json`
- Banker's safety source: `projects/deadlock-detector-lab/sample_banker_state.json`
- Banker's request source: `projects/deadlock-detector-lab/sample_banker_request.json`
- Banker's contrast request source: `projects/deadlock-detector-lab/sample_banker_request_unsafe.json`

## Key takeaways

- Wait-for detection finds a concrete cycle among P1, P2, P3.
- Resource-allocation detection still leaves P1, P2 blocked after only P3 can finish.
- Banker's avoidance keeps the system safe with sequence P1, P3, P4, P0, P2.
- The sample request from P1 (A=1, B=0, C=2) is granted and still leaves safe sequence P1, P3, P4, P0, P2.
- sample_banker_request.json keeps the path grantable after spending shared slack C=2; plus granted-only slack A=1; and still leaves first runnable set P1; whereas sample_banker_request_unsafe.json leaves first runnable set none; so runnable option P1 disappears; and blocking becomes P0: A=4, B=1, C=1; P1: C=2; P2: A=3; P3: C=1; P4: A=1, C=1.

## Detection models

### Wait-for graph
- Question answered: is there already a cycle among the waiting processes?
- Deadlocked: yes
- Cycle: `P1 -> P2 -> P3 -> P1`
- Blocked processes: `P1, P2, P3`

### Resource-allocation snapshot
- Question answered: can the current work vector still finish anyone and free resources?
- Deadlocked: yes
- Finish order: `P3`
- Deadlocked processes: `P1, P2`
- Blocking summary: `P1: scanner=1; P2: printer=1`

## Avoidance model

### Banker's safety check
- Question answered: is the current state safe before any new request is granted?
- Safe: yes
- Safe sequence: `P1, P3, P4, P0, P2`
- Final work: `A=10, B=5, C=7`
- Blocking summary: `none`

| Step | Chosen process | Runnable set | Work before | Remaining need | Allocation released | Work after |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `P1` | `P1, P3` | `A=3, B=3, C=2` | `A=1, B=2, C=2` | `A=2, B=0, C=0` | `A=5, B=3, C=2` |
| 2 | `P3` | `P3, P4` | `A=5, B=3, C=2` | `A=0, B=1, C=1` | `A=2, B=1, C=1` | `A=7, B=4, C=3` |
| 3 | `P4` | `P0, P2, P4` | `A=7, B=4, C=3` | `A=4, B=3, C=1` | `A=0, B=0, C=2` | `A=7, B=4, C=5` |
| 4 | `P0` | `P0, P2` | `A=7, B=4, C=5` | `A=7, B=4, C=3` | `A=0, B=1, C=0` | `A=7, B=5, C=5` |
| 5 | `P2` | `P2` | `A=7, B=5, C=5` | `A=6, B=0, C=0` | `A=3, B=0, C=2` | `A=10, B=5, C=7` |

### Banker's request trial
- Question answered: should this new request be granted while keeping the system safe?
- Process: `P1`
- Request: `A=1, B=0, C=2`
- Granted: yes
- Reason: request can be granted safely
- Safe after trial: yes
- Safe sequence: `P1, P3, P4, P0, P2`
- Evaluated available vector: `A=2, B=3, C=0`
- Blocking summary: `none`

| Step | Chosen process | Runnable set | Work before | Remaining need | Allocation released | Work after |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `P1` | `P1` | `A=2, B=3, C=0` | `A=0, B=2, C=0` | `A=3, B=0, C=2` | `A=5, B=3, C=2` |
| 2 | `P3` | `P3, P4` | `A=5, B=3, C=2` | `A=0, B=1, C=1` | `A=2, B=1, C=1` | `A=7, B=4, C=3` |
| 3 | `P4` | `P0, P2, P4` | `A=7, B=4, C=3` | `A=4, B=3, C=1` | `A=0, B=0, C=2` | `A=7, B=4, C=5` |
| 4 | `P0` | `P0, P2` | `A=7, B=4, C=5` | `A=7, B=4, C=3` | `A=0, B=1, C=0` | `A=7, B=5, C=5` |
| 5 | `P2` | `P2` | `A=7, B=5, C=5` | `A=6, B=0, C=0` | `A=3, B=0, C=2` | `A=10, B=5, C=7` |

### Granted vs denied request delta
- Question answered: what immediate slack and runnable options disappear between the safe and unsafe request paths?
- Reference granted request: `sample_banker_request.json`
- Contrast denied request: `sample_banker_request_unsafe.json`
- Shared slack spent: `C=2`
- Granted-only slack spent: `A=1`
- Denied-only slack spent: `none`
- Granted first runnable set: `P1`
- Denied first runnable set: `none`
- Lost runnable options: `P1`
- Denied blocking: `P0: A=4, B=1, C=1; P1: C=2; P2: A=3; P3: C=1; P4: A=1, C=1`
- Summary: sample_banker_request.json keeps the path grantable after spending shared slack C=2; plus granted-only slack A=1; and still leaves first runnable set P1; whereas sample_banker_request_unsafe.json leaves first runnable set none; so runnable option P1 disappears; and blocking becomes P0: A=4, B=1, C=1; P1: C=2; P2: A=3; P3: C=1; P4: A=1, C=1.
