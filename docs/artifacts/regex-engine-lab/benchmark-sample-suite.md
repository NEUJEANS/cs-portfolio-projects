# Regex engine benchmark report

- suite: `sample-suite`
- iterations per engine: `3000`
- warmup iterations per engine: `200`
- agreement across all cases: `True`

| case | mode | agreement | lab ms | python re ms | lab ops/s | python ops/s | faster |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| anchored_id_fullmatch | fullmatch | yes | 52.512 | 0.984 | 57129.3 | 3049499.5 | python_re |
| pet_search | search | yes | 29.649 | 0.730 | 101185.1 | 4110873.0 | python_re |
| release_token_search | search | yes | 104.803 | 1.248 | 28625.2 | 2404283.5 | python_re |

## Case notes

### anchored_id_fullmatch
- mode: `fullmatch`
- pattern: `^ID-\d\d\d\d-\w+$`
- text: `ID-2026-demo_user`
- agreement: `True`
- lab result: `{"matched": true}`
- python result: `{"matched": true}`

### pet_search
- mode: `search`
- pattern: `(cat|dog)s?`
- text: `xxdogs walked by`
- agreement: `True`
- lab result: `{"matched": true, "start": 2, "end": 6, "match": "dogs"}`
- python result: `{"matched": true, "start": 2, "end": 6, "match": "dogs"}`

### release_token_search
- mode: `search`
- pattern: `\d+\s\w+`
- text: `build 2026 portfolio`
- agreement: `True`
- lab result: `{"matched": true, "start": 6, "end": 20, "match": "2026 portfolio"}`
- python result: `{"matched": true, "start": 6, "end": 20, "match": "2026 portfolio"}`
