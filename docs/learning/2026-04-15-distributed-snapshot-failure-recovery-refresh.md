# 2026-04-15 distributed snapshot failure/recovery refresh

## Refresh
Treat process failure as a process-state transition, not as money disappearing.

Rules for this slice:
- balances remain attached to the process even while it is down
- in-flight transfers already sent stay queued on their channels
- a failed sender cannot initiate new transfers
- a failed receiver cannot apply deliveries until it recovers
- snapshot output should expose liveness so the captured cut explains why some messages remain queued

## Quick self-test
1. If B fails after `A->B` is sent but before delivery, should total money change?  
   No. The amount stays in the channel queue.
2. If B is down, should `deliver A:B` succeed?  
   No. Delivery into a failed receiver should be blocked.
3. What should a recovery operation do in this model?  
   Mark the process live again so future sends/deliveries can proceed.
