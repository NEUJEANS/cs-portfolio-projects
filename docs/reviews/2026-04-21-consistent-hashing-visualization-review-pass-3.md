# 2026-04-21 consistent-hashing visualization review pass 3

## Focus
Make the load story glanceable in the committed SVG and HTML artifacts.

## Issue found
- The first load-distribution panel showed raw placement counts only, so a reader still had to mentally convert those counts into relative shares.

## Fix applied
- Added percentage labels beside each SVG load bar and in the HTML node summary list so the balance story is readable at a glance.
- Kept the counts as well, so the artifact still shows the exact deterministic workload totals.

## Verification
- `python3 -m unittest projects/consistent-hashing-lab/test_consistent_hashing.py`
- `python3 projects/consistent-hashing-lab/consistent_hashing.py visualize --nodes node-a node-b node-c node-d --key-count 24 --displayed-key-count 12 --virtual-nodes 32 --replication-factor 2 --title 'Consistent hashing ring with replica placement' --svg-out /tmp/consistent-hashing-ring.svg --html-out /tmp/consistent-hashing-ring.html`
