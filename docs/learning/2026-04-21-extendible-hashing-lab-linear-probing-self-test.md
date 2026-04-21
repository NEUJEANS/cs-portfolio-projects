# extendible-hashing-lab linear-probing baseline self-test — 2026-04-21

## Quick refresh
- linear probing resolves collisions by checking the next slot(s) in sequence, so probe length is the key operational cost to surface
- tombstones preserve lookup correctness after deletes, but they can inflate future probe chains until a rebuild compacts the table
- extendible hashing is the structural contrast because it spends work on directory growth and bucket splits instead of growing one probe cluster
- for a portfolio artifact bundle, the same benchmark story should stay visible in JSON, Markdown, HTML, and CSV outputs

## Self-test
1. **Q:** Why is linear probing a better added baseline here than another complex hash table?
   **A:** It gives a simpler open-addressing reference point, so readers can compare extendible hashing against both a minimal probe-based design and the more elaborate cuckoo baseline.
2. **Q:** What metrics best explain delete-heavy linear probing behavior?
   **A:** Tombstone count, rebuild count, and average/max probe count, because they show how deleted slots still affect later searches and inserts.
3. **Q:** What should be made explicit in the benchmark suite file for resumability?
   **A:** The linear table’s starting capacity plus its load-factor and tombstone-rebuild thresholds, so committed artifacts stay reproducible and self-describing.
