# 2026-04-14 Task Tracker CLI Tags/Search Research

Goal: strengthen the existing task tracker with a portfolio-worthy metadata slice instead of creating another shallow CRUD clone.

## Brief notes
- Simple project/task tools become more believable when they support organization primitives like tags, filters, and quick search.
- For a student portfolio, tags are a better next step than color output because they change both the data model and the query path.
- Keeping tags normalized to lowercase slug-like tokens avoids brittle matching and simplifies tests.
- Search should work across descriptions and tags so demo queries feel natural from the terminal.

## Scope chosen for this run
- repeatable `--tag` flags on add/update/list
- keyword search over descriptions and tags
- summary metrics for overdue tasks and tag usage
- no fuzzy search or full-text index yet; keep the slice lightweight and resumable
