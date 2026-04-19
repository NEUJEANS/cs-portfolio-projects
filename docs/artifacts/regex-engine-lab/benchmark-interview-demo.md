# Regex engine benchmark report

- suite: `interview-demo`
- iterations per engine: `50`
- warmup iterations per engine: `5`
- agreement across all cases: `True`
- suite tags present: `alternation, anchored, interview-demo, search, shorthand`
- suite source: `docs/examples/regex-engine-benchmark-suite.json`
- applied filters: include `interview-demo`; exclude `none`

| case | mode | tags | agreement | lab ms | python re ms | lab ops/s | python ops/s | faster |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| anchored-id-fullmatch | fullmatch | interview-demo, anchored, shorthand | yes | 0.911 | 0.018 | 54877.5 | 2835431.6 | python_re |
| pet-search | search | interview-demo, search, alternation | yes | 0.492 | 0.018 | 101584.1 | 2770696.9 | python_re |

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
