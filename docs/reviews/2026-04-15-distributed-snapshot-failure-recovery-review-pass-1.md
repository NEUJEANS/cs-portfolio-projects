# Review pass 1 — distributed-snapshot failure/recovery slice

## Focus
Behavioral correctness and outage semantics.

## Findings
- Initial implementation incorrectly required the transfer receiver to be `up` at send time.
- That weakened the outage model because queued messages could not be created for a down receiver.

## Fixes applied
- restricted send-time liveness validation to the sender only
- kept delivery-time validation on the receiver
- added regression coverage proving sends to a failed receiver stay queued until recovery
