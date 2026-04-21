# Robin Hood hashing refresh + self-test

## Topics refreshed
- open addressing vs tombstone-heavy deletion strategies
- Robin Hood insertion invariant: if the incoming entry has probed farther than the resident entry, swap them
- backward-shift deletion: keep shifting entries left until hitting an empty slot or a home-slot entry
- deterministic hashing for stable tests and committed artifacts
- lightweight CLI patterns with `argparse`, JSON snapshots, and CSV exports

## Mini self-tests
### 1. When does a swap happen?
If the incoming key has probe distance `d_in` and the resident key has `d_res`, swap when `d_in > d_res`.

### 2. Why is backward-shift deletion better than a tombstone here?
It keeps search chains contiguous, avoids permanent dead markers, and lets stats reflect the true current cluster shape.

### 3. What makes a snapshot valid?
- slot count matches capacity
- stored hash matches the key
- stored probe distance matches the slot's distance from the key's home slot
- no gaps exist inside a recorded probe chain

### 4. What should a good benchmark expose?
Average insert probes, average successful lookup probes, max probe distance, and swap count across several load factors.

## Practical rules used in this slice
- prefer deterministic seeds and hashes for reproducible portfolio artifacts
- validate persisted state strictly so broken snapshots fail loudly
- keep the core data structure independent from the CLI so tests can hit the logic directly
