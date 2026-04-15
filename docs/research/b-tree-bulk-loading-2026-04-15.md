# B-tree bulk loading notes — 2026-04-15

## Goal for this slice
Add a meaningful "sorted input" build path so the project better matches database-style index construction workloads.

## Practical approach chosen
- Use a strictly increasing dataset contract.
- Build through an append-only right-spine path instead of generic insert navigation.
- Keep the existing B-tree split logic so the resulting structure stays compatible with search, delete, save/load, and validation code.

## Why this fits the project
- Real index builders often distinguish between random inserts and bulk loads from sorted runs.
- Even without a full page-packing loader, append-oriented loading removes unnecessary bisect work for already sorted input.
- The approach is compact, testable, and easy to explain in a portfolio README.

## Constraints to document
- Sorted mode requires strictly increasing keys.
- Duplicate keys are rejected in bulk-load mode rather than treated as updates.
- A future slice could benchmark bulk load vs generic inserts or add fixed-size page encoding.
