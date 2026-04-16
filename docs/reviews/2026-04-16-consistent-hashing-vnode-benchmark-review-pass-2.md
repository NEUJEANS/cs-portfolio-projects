# Review pass 2 — consistent-hashing virtual-node benchmark

## Focus
README clarity and portfolio framing.

## Findings
1. The README showed how to run the new benchmark, but it did not explain the new summary field or the add/remove exclusivity rule, which made the JSON output less self-explanatory for portfolio readers.

## Fixes
- Expanded the README notes to explain `best_imbalance_virtual_nodes`.
- Documented that movement-metric runs accept either `--add-node` or `--remove-node`, but not both.
