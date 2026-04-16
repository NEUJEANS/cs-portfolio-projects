# 2026-04-16 Memory Allocator Alignment Refresh

## Quick refresh
- alignment rounds each request up to the next multiple of the alignment quantum
- the rounded size is the actual occupied block size in an aligned contiguous allocator
- internal fragmentation for a block is `allocated_size - requested_size`
- total internal fragmentation is the sum of per-allocation slack bytes across live allocations
- compaction should preserve each allocation's rounded footprint while moving blocks earlier in memory

## Self-test
1. Request 5 bytes with alignment 4 -> rounded allocation is 8, internal fragmentation is 3.
2. Request 8 bytes with alignment 4 -> rounded allocation is 8, internal fragmentation is 0.
3. Request 7 bytes with alignment 8 -> rounded allocation is 8, internal fragmentation is 1.
4. If blocks of 8 and 4 bytes are live but requested sizes were 5 and 3, total internal fragmentation is 4.

## Implementation plan
- track both requested size and allocated segment size
- expose requested/allocated totals plus internal fragmentation in metrics
- keep existing behavior unchanged when alignment is 1
- surface alignment in CLI JSON and README examples
