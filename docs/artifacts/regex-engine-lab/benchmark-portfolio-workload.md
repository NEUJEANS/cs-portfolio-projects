# Regex engine benchmark report

- suite: `portfolio-workload`
- iterations per engine: `50`
- warmup iterations per engine: `5`
- agreement across all cases: `True`
- suite source: `docs/examples/regex-engine-benchmark-suite.json`

| case | mode | agreement | lab ms | python re ms | lab ops/s | python ops/s | faster |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| anchored-id-fullmatch | fullmatch | yes | 0.884 | 0.018 | 56570.1 | 2775619.3 | python_re |
| pet-search | search | yes | 0.497 | 0.013 | 100565.4 | 3901982.8 | python_re |
| release-token-search | search | yes | 1.726 | 0.022 | 28969.1 | 2319970.2 | python_re |
| whitespace-fullmatch | fullmatch | yes | 0.201 | 0.011 | 248541.1 | 4373688.2 | python_re |

## Case notes

### anchored-id-fullmatch
- mode: `fullmatch`
- pattern: `^ID-\d\d\d\d-\w+$`
- text: `ID-2026-demo_user`
- agreement: `True`
- lab result: `{"matched": true}`
- python result: `{"matched": true}`

### pet-search
- mode: `search`
- pattern: `(cat|dog)s?`
- text: `xxdogs walked by`
- agreement: `True`
- lab result: `{"matched": true, "start": 2, "end": 6, "match": "dogs"}`
- python result: `{"matched": true, "start": 2, "end": 6, "match": "dogs"}`

### release-token-search
- mode: `search`
- pattern: `\d+\s\w+`
- text: `build 2026 portfolio`
- agreement: `True`
- lab result: `{"matched": true, "start": 6, "end": 20, "match": "2026 portfolio"}`
- python result: `{"matched": true, "start": 6, "end": 20, "match": "2026 portfolio"}`

### whitespace-fullmatch
- mode: `fullmatch`
- pattern: `^\s+$`
- text: ` 	`
- agreement: `True`
- lab result: `{"matched": true}`
- python result: `{"matched": true}`
