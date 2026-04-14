# Cache Simulator Refresh + Self-Test — 2026-04-14

Quick refresh targets:
- derive number of sets as `cache_size / (block_size * associativity)`
- compute `block_address = address // block_size`
- compute `set_index = block_address % set_count`
- compute `tag = block_address // set_count`
- on write-back eviction, increment memory writes only when the evicted line is dirty
- on write-through hit/write miss, every logical write also increments memory writes

Self-test:
1. 64-byte cache, 16-byte blocks, 2-way associativity => sets = 64 / (16 * 2) = 2
2. Address 52 => block address 3, set index 1, tag 1
3. If set 0 already has two clean lines and a third conflicting access arrives, LRU should evict the oldest line in that set
4. In write-back mode, two writes to the same cached block should count as one memory write only when the dirty block is eventually evicted or flushed

Result: ready to implement.
