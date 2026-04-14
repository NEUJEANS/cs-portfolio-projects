# HyperLogLog refresh and self-test

## Refresh notes
- A HyperLogLog sketch uses the first `p` hash bits as the register index.
- The remaining bits are used to measure the position of the first `1` bit (leading-zero count + 1).
- More registers reduce variance; the rough relative error is `1.04 / sqrt(m)`.
- Merge is simple only when sketches use the same precision.

## Self-test
1. Why can HyperLogLog merge distributed partial counts cheaply?
   - Because each register stores a local maximum rank, and merge is just register-wise `max`.
2. What should happen when many registers are still zero?
   - Prefer linear counting for better small-range estimates.
3. What is the main tradeoff in choosing precision?
   - Higher precision uses more memory but reduces error.
