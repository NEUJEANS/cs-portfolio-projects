# Repeatable read window — isolation comparison

A long-running reader observes a value twice while a concurrent writer increments it in the middle of the schedule.

| Isolation | Final version | Aborted txs | Invariant status | Final state |
| --- | ---: | ---: | --- | --- |
| read-committed | 1 | 1 | all pass | `{"inventory": 8}` |
| snapshot | 1 | 0 | all pass | `{"inventory": 8}` |
| serializable | 1 | 1 | all pass | `{"inventory": 8}` |
| strict-2pl | 0 | 1 | all pass | `{"inventory": 5}` |

## read-committed

- `Reader` → **aborted** — The reader expected a repeatable value across both reads.
- `Writer` → **committed**; writes `{"inventory": 8}`

Invariant checks:
- ✅ `inventory_non_negative` — Inventory should stay non-negative after the update.

## snapshot

- `Reader` → **committed**
- `Writer` → **committed**; writes `{"inventory": 8}`

Invariant checks:
- ✅ `inventory_non_negative` — Inventory should stay non-negative after the update.

## serializable

- `Reader` → **aborted** — serializable validation conflict on inventory
- `Writer` → **committed**; writes `{"inventory": 8}`

Invariant checks:
- ✅ `inventory_non_negative` — Inventory should stay non-negative after the update.

## strict-2pl

- `Reader` → **committed**
- `Writer` → **aborted** — strict-2pl write lock conflict on inventory held by shared lock(s) Reader

Invariant checks:
- ✅ `inventory_non_negative` — Inventory should stay non-negative after the update.
