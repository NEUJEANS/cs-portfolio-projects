# Review Pass 2 - Count-Min Sketch Lab

## Checks
- reviewed README wording against returned JSON fields
- checked heavy hitter output naming for clarity

## Issue found
- `lower_bound` was misleading because the stored value is the exact observed count in this teaching version.

## Fix
- Renamed the field to `exact_count` and updated README language.
