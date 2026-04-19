# Regex engine benchmark report

- suite: `sample-suite`
- iterations per engine: `50`
- warmup iterations per engine: `5`
- agreement across all cases: `True`
- suite tags present: `alternation, anchored, interview-demo, portfolio-batch, search, shorthand`
- suite source: `built-in defaults`

| case | mode | tags | agreement | lab ms | python re ms | lab ops/s | python ops/s | faster |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| anchored_id_fullmatch | fullmatch | interview-demo, anchored, shorthand | yes | 1.125 | 0.017 | 44439.2 | 2892681.9 | python_re |
| pet_search | search | interview-demo, search, alternation | yes | 0.667 | 0.013 | 75011.6 | 3898027.5 | python_re |
| release_token_search | search | portfolio-batch, search, shorthand | yes | 2.380 | 0.021 | 21012.7 | 2363730.7 | python_re |

## Case notes

### anchored_id_fullmatch
- mode: `fullmatch`
- tags: `interview-demo, anchored, shorthand`
- pattern: `^ID-\d\d\d\d-\w+$`
- text: `ID-2026-demo_user`
- agreement: `True`
- lab result: `{"matched": true}`
- python result: `{"matched": true}`

### pet_search
- mode: `search`
- tags: `interview-demo, search, alternation`
- pattern: `(cat|dog)s?`
- text: `xxdogs walked by`
- agreement: `True`
- lab result: `{"matched": true, "start": 2, "end": 6, "match": "dogs"}`
- python result: `{"matched": true, "start": 2, "end": 6, "match": "dogs"}`

### release_token_search
- mode: `search`
- tags: `portfolio-batch, search, shorthand`
- pattern: `\d+\s\w+`
- text: `build 2026 portfolio`
- agreement: `True`
- lab result: `{"matched": true, "start": 6, "end": 20, "match": "2026 portfolio"}`
- python result: `{"matched": true, "start": 6, "end": 20, "match": "2026 portfolio"}`
