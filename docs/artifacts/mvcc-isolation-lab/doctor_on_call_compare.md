# Doctor on-call write skew — isolation comparison

Two doctors each see coverage in their snapshot and independently sign off, illustrating write skew under snapshot isolation.

| Isolation | Final version | Aborted txs | Invariant status | Final state |
| --- | ---: | ---: | --- | --- |
| read-committed | 2 | 0 | at_least_one_doctor_on_call | `{"alice_on_call": false, "bob_on_call": false}` |
| snapshot | 2 | 0 | at_least_one_doctor_on_call | `{"alice_on_call": false, "bob_on_call": false}` |
| serializable | 1 | 1 | all pass | `{"alice_on_call": false, "bob_on_call": true}` |

## read-committed

- `T1` → **committed**; writes `{"alice_on_call": false}`
- `T2` → **committed**; writes `{"bob_on_call": false}`

Invariant checks:
- ❌ `at_least_one_doctor_on_call` — At least one doctor should remain on call after the schedule commits.

## snapshot

- `T1` → **committed**; writes `{"alice_on_call": false}`
- `T2` → **committed**; writes `{"bob_on_call": false}`

Invariant checks:
- ❌ `at_least_one_doctor_on_call` — At least one doctor should remain on call after the schedule commits.

## serializable

- `T1` → **committed**; writes `{"alice_on_call": false}`
- `T2` → **aborted** — serializable validation conflict on alice_on_call; buffered writes `{"bob_on_call": false}`

Invariant checks:
- ✅ `at_least_one_doctor_on_call` — At least one doctor should remain on call after the schedule commits.
