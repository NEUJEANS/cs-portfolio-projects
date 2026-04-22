# Banker's algorithm request gallery

- Request count: 2
- Granted: 1
- Denied: 1

## Highlights

- This gallery contrasts 1 granted request with 1 denied request.
- sample_banker_request.json: P1 requesting A=1, B=0, C=2 stays safe with sequence P1, P3, P4, P0, P2.
- sample_banker_request_unsafe.json: P0 requesting A=0, B=0, C=2 is denied because request would move the system into an unsafe state; the trial leaves no runnable process and blocking is P0: A=4, B=1, C=1; P1: C=2; P2: A=3; P3: C=1; P4: A=1, C=1.

## Request comparison

| Source | Process | Request | Decision | First runnable set | Safe sequence | Evaluated available | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `sample_banker_request.json` | `P1` | `A=1, B=0, C=2` | granted | `P1` | `P1, P3, P4, P0, P2` | `A=2, B=3, C=0` | `none` |
| `sample_banker_request_unsafe.json` | `P0` | `A=0, B=0, C=2` | denied | `none` | `none` | `A=3, B=3, C=0` | `P0: A=4, B=1, C=1; P1: C=2; P2: A=3; P3: C=1; P4: A=1, C=1` |
