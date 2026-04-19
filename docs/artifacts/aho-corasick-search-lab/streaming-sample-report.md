# Streaming incident keyword report

- Source: `projects/aho-corasick-search-lab/sample_text.txt`
- Input mode: `stream (16 chunks @ 8 chars, boundary overlap 4)`
- Case sensitive: `yes`
- Characters processed: `124`
- Pattern count: `3`
- Match count: `3`
- Context mode: `6 chars (sampled around matches)`
- Patterns: `error`, `warn`, `panic`

## Pattern counts

| Pattern | Count |
| --- | ---: |
| error | 1 |
| warn | 1 |
| panic | 1 |

## Match excerpts

### Match 1 — `warn`
- Location: line 2, column 2
- Offsets: `28:32`
- Excerpt:
```text
tart
[⟦warn⟧] cach
```
- Before / match / after: `"tart\n["` · `"warn"` · `"] cach"`

### Match 2 — `error`
- Location: line 3, column 2
- Offsets: `59:64`
- Excerpt:
```text
lete
[⟦error⟧] fail
```
- Before / match / after: `"lete\n["` · `"error"` · `"] fail"`

### Match 3 — `panic`
- Location: line 4, column 2
- Offsets: `89:94`
- Excerpt:
```text
nfig
[⟦panic⟧] unre
```
- Before / match / after: `"nfig\n["` · `"panic"` · `"] unre"`
