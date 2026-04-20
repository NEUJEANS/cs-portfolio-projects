# Repeatable read window — isolation comparison

| Isolation | Final version | Aborted txs | Invariant status | Final state |
| --- | ---: | ---: | --- | --- |
| read-committed | 1 | 1 | all pass | `{"inventory": 8}` |
| snapshot | 1 | 0 | all pass | `{"inventory": 8}` |
| serializable | 1 | 1 | all pass | `{"inventory": 8}` |

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
