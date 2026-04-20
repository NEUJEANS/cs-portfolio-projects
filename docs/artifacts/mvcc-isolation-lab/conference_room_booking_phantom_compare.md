# Conference room booking phantom — isolation comparison

Two coordinators each scan for an open room slot before inserting a separate reservation row. Key-based conflicts miss the shared predicate, so only serializable predicate validation should stop the double-booking anomaly.

| Isolation | Final version | Aborted txs | Invariant status | Final state |
| --- | ---: | ---: | --- | --- |
| read-committed | 2 | 0 | at_most_one_room101_booking | `{"booking_room101_2026-04-20T09:00_alice": "reserved", "booking_room101_2026-04-20T09:00_bob": "reserved", "room101_capacity": 1}` |
| snapshot | 2 | 0 | at_most_one_room101_booking | `{"booking_room101_2026-04-20T09:00_alice": "reserved", "booking_room101_2026-04-20T09:00_bob": "reserved", "room101_capacity": 1}` |
| serializable | 1 | 1 | all pass | `{"booking_room101_2026-04-20T09:00_alice": "reserved", "room101_capacity": 1}` |
| strict-2pl | 1 | 1 | all pass | `{"booking_room101_2026-04-20T09:00_bob": "reserved", "room101_capacity": 1}` |

## read-committed

- `AliceBooking` → **committed**; predicate reads `["prefix=booking_room101_2026-04-20T09:00_, value=\"reserved\""]`; writes `{"booking_room101_2026-04-20T09:00_alice": "reserved"}`
- `BobBooking` → **committed**; predicate reads `["prefix=booking_room101_2026-04-20T09:00_, value=\"reserved\""]`; writes `{"booking_room101_2026-04-20T09:00_bob": "reserved"}`

Invariant checks:
- ❌ `at_most_one_room101_booking` — room capacity should cap concurrent reservations at one

## snapshot

- `AliceBooking` → **committed**; predicate reads `["prefix=booking_room101_2026-04-20T09:00_, value=\"reserved\""]`; writes `{"booking_room101_2026-04-20T09:00_alice": "reserved"}`
- `BobBooking` → **committed**; predicate reads `["prefix=booking_room101_2026-04-20T09:00_, value=\"reserved\""]`; writes `{"booking_room101_2026-04-20T09:00_bob": "reserved"}`

Invariant checks:
- ❌ `at_most_one_room101_booking` — room capacity should cap concurrent reservations at one

## serializable

- `AliceBooking` → **committed**; predicate reads `["prefix=booking_room101_2026-04-20T09:00_, value=\"reserved\""]`; writes `{"booking_room101_2026-04-20T09:00_alice": "reserved"}`
- `BobBooking` → **aborted** — predicate conflict on prefix=booking_room101_2026-04-20T09:00_, value="reserved" (0 matches -> booking_room101_2026-04-20T09:00_alice); predicate reads `["prefix=booking_room101_2026-04-20T09:00_, value=\"reserved\""]`; buffered writes `{"booking_room101_2026-04-20T09:00_bob": "reserved"}`

Invariant checks:
- ✅ `at_most_one_room101_booking` — room capacity should cap concurrent reservations at one

## strict-2pl

- `AliceBooking` → **aborted** — strict-2pl predicate lock conflict on prefix=booking_room101_2026-04-20T09:00_, value="reserved" held by BobBooking; predicate reads `["prefix=booking_room101_2026-04-20T09:00_, value=\"reserved\""]`
- `BobBooking` → **committed**; predicate reads `["prefix=booking_room101_2026-04-20T09:00_, value=\"reserved\""]`; writes `{"booking_room101_2026-04-20T09:00_bob": "reserved"}`

Invariant checks:
- ✅ `at_most_one_room101_booking` — room capacity should cap concurrent reservations at one
