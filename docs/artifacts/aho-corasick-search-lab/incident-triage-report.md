# Incident triage keyword report

- Source: `projects/aho-corasick-search-lab/sample_incident_log.txt`
- Preset: `incident-triage`
- Input mode: `stream (20 chunks @ 18 chars, boundary overlap 11)`
- Case sensitive: `yes`
- Characters processed: `351`
- Pattern count: `12`
- Match count: `9`
- Context mode: `10 chars (sampled around matches)`
- Patterns: `critical`, `warning`, `error`, `sev1`, `latency`, `timeout`, `degraded`, `outage`, `breach`, `exfiltration`, `credential`, `leak`

## Pattern counts

| Pattern | Count |
| --- | ---: |
| critical | 1 |
| warning | 1 |
| error | 1 |
| sev1 | 0 |
| latency | 1 |
| timeout | 1 |
| degraded | 1 |
| outage | 1 |
| breach | 0 |
| exfiltration | 0 |
| credential | 1 |
| leak | 1 |

## Group counts

| Group | Matches | Patterns |
| --- | ---: | --- |
| severity | 3 | `critical`, `warning`, `error`, `sev1`<br><sub>How urgent the event sounds on first read.</sub> |
| customer-impact | 4 | `latency`, `timeout`, `degraded`, `outage`<br><sub>Keywords that hint at user-facing degradation or outage symptoms.</sub> |
| security | 2 | `breach`, `exfiltration`, `credential`, `leak`<br><sub>Security-response indicators worth escalating quickly.</sub> |

## Match excerpts

### Match 1 — `warning`
- Location: line 2, column 22
- Offsets: `71:78`
- Groups: `severity`
- Excerpt:
```text
09:02:14Z ⟦warning⟧ checkout 
```
- Before / match / after: `"09:02:14Z "` · `"warning"` · `" checkout "`

### Match 2 — `latency`
- Location: line 2, column 39
- Offsets: `88:95`
- Groups: `customer-impact`
- Excerpt:
```text
 checkout ⟦latency⟧ crossed 4
```
- Before / match / after: `" checkout "` · `"latency"` · `" crossed 4"`

### Match 3 — `critical`
- Location: line 3, column 22
- Offsets: `143:151`
- Groups: `severity`
- Excerpt:
```text
09:03:55Z ⟦critical⟧ api timeo
```
- Before / match / after: `"09:03:55Z "` · `"critical"` · `" api timeo"`

### Match 4 — `timeout`
- Location: line 3, column 35
- Offsets: `156:163`
- Groups: `customer-impact`
- Excerpt:
```text
tical api ⟦timeout⟧ caused de
```
- Before / match / after: `"tical api "` · `"timeout"` · `" caused de"`

### Match 5 — `degraded`
- Location: line 3, column 50
- Offsets: `171:179`
- Groups: `customer-impact`
- Excerpt:
```text
ut caused ⟦degraded⟧ search re
```
- Before / match / after: `"ut caused "` · `"degraded"` · `" search re"`

### Match 6 — `error`
- Location: line 4, column 22
- Offsets: `218:223`
- Groups: `severity`
- Excerpt:
```text
09:05:10Z ⟦error⟧ possible 
```
- Before / match / after: `"09:05:10Z "` · `"error"` · `" possible "`

### Match 7 — `credential`
- Location: line 4, column 37
- Offsets: `233:243`
- Groups: `security`
- Excerpt:
```text
 possible ⟦credential⟧ leak whil
```
- Before / match / after: `" possible "` · `"credential"` · `" leak whil"`

### Match 8 — `leak`
- Location: line 4, column 48
- Offsets: `244:248`
- Groups: `security`
- Excerpt:
```text
redential ⟦leak⟧ while rot
```
- Before / match / after: `"redential "` · `"leak"` · `" while rot"`

### Match 9 — `outage`
- Location: line 5, column 46
- Offsets: `323:329`
- Groups: `customer-impact`
- Excerpt:
```text
n cleared ⟦outage⟧ banner af
```
- Before / match / after: `"n cleared "` · `"outage"` · `" banner af"`
