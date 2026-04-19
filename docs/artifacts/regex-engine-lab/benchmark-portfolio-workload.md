# Regex engine benchmark report

- suite: `portfolio-workload`
- iterations per engine: `50`
- warmup iterations per engine: `5`
- agreement across all cases: `True`
- suite tags present: `alternation, anchored, interview-demo, portfolio-batch, search, shorthand, whitespace`
- suite source: `docs/examples/regex-engine-benchmark-suite.json`

| case | mode | tags | agreement | lab ms | python re ms | lab ops/s | python ops/s | faster |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| anchored-id-fullmatch | fullmatch | interview-demo, anchored, shorthand | yes | 0.921 | 0.018 | 54306.6 | 2846731.7 | python_re |
| pet-search | search | interview-demo, search, alternation | yes | 0.517 | 0.013 | 96779.0 | 3963536.4 | python_re |
| release-token-search | search | portfolio-batch, search, shorthand | yes | 1.753 | 0.020 | 28523.9 | 2459419.5 | python_re |
| whitespace-fullmatch | fullmatch | portfolio-batch, whitespace | yes | 0.204 | 0.011 | 245046.4 | 4499639.0 | python_re |

## Case notes

### anchored-id-fullmatch
- mode: `fullmatch`
- tags: `interview-demo, anchored, shorthand`
- pattern: `^ID-\d\d\d\d-\w+$`
- text: `ID-2026-demo_user`
- agreement: `True`
- lab result: `{"matched": true}`
- python result: `{"matched": true}`

### pet-search
- mode: `search`
- tags: `interview-demo, search, alternation`
- pattern: `(cat|dog)s?`
- text: `xxdogs walked by`
- agreement: `True`
- lab result: `{"matched": true, "start": 2, "end": 6, "match": "dogs"}`
- python result: `{"matched": true, "start": 2, "end": 6, "match": "dogs"}`

### release-token-search
- mode: `search`
- tags: `portfolio-batch, search, shorthand`
- pattern: `\d+\s\w+`
- text: `build 2026 portfolio`
- agreement: `True`
- lab result: `{"matched": true, "start": 6, "end": 20, "match": "2026 portfolio"}`
- python result: `{"matched": true, "start": 6, "end": 20, "match": "2026 portfolio"}`

### whitespace-fullmatch
- mode: `fullmatch`
- tags: `portfolio-batch, whitespace`
- pattern: `^\s+$`
- text: ` 	`
- agreement: `True`
- lab result: `{"matched": true}`
- python result: `{"matched": true}`
