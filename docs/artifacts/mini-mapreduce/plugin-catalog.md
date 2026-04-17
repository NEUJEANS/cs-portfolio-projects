# Mini MapReduce plugin inspection

- Plugin count: `7`
- Diff count: `6`

## Catalog quick links

- [`plugin-average-score`](plugin-pages/plugin-average-score.md) — Average-score analytics plugin with synthetic cohort benchmark families. (`5 hooks` · `3 dataset families` · `commit pinned` · `github linked`; families: `default, exam-cram, project-week`)
- [`plugin-rolling-window-join`](plugin-pages/plugin-rolling-window-join.md) — Rolling-window join plugin for multi-stream correlation and pipeline-debug demos. (`5 hooks` · `3 dataset families` · `commit pinned` · `github linked`; families: `default, checkout-funnel, incident-correlation`)
- [`plugin-service-latency`](plugin-pages/plugin-service-latency.md) — Service-latency summary plugin for observability-style benchmark demos. (`5 hooks` · `3 dataset families` · `commit pinned` · `github linked`; families: `default, incident-spike, batch-window`)
- [`plugin-sessionization`](plugin-pages/plugin-sessionization.md) — Sessionization analytics plugin for product-usage benchmark demos. (`5 hooks` · `3 dataset families` · `commit pinned` · `github linked`; families: `default, exam-revision, launch-day`)
- [`plugin-streaming-window`](plugin-pages/plugin-streaming-window.md) — Streaming-window aggregation plugin for telemetry-style benchmark demos. (`5 hooks` · `3 dataset families` · `commit pinned` · `github linked`; families: `default, iot-burst, live-ops`)
- [`plugin-max-score`](plugin-pages/plugin-max-score.md) — Maximum-score reducer plugin for simple leaderboard-style demos. (`3 hooks` · `no dataset families` · `commit pinned` · `github linked`; families: `-`)
- [`plugin-watermark-late-summary`](plugin-pages/plugin-watermark-late-summary.md) — Watermark-aware late-event summary plugin for out-of-order stream-processing demos. (`5 hooks` · `3 dataset families` · `commit pinned` · `github linked`; families: `default, sensor-backfill, live-replay`)

## Plugin summary

| Name | Plugin | Commit | Summary | Mapper | Reducer | Combiner | Benchmark generator | Benchmark note hook | Dataset families |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `plugin-average-score` | `projects/mini-mapreduce-lab/plugins_average_score.py` | `2332425c37ad` | Average-score analytics plugin with synthetic cohort benchmark families. | `plugins_average_score.map_records`<br><small>`map_records(lines)`<br>line 7<br>plugins_average_score.py#L7-L13<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L7-L13)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_average_score.py#L7-L13)<br>Emit per-student sum/count records from comma-separated score lines.</small> | `plugins_average_score.reduce_key`<br><small>`reduce_key(_key, values)`<br>line 23<br>plugins_average_score.py#L23-L27<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L23-L27)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_average_score.py#L23-L27)<br>Return a rounded average score for one student key.</small> | `plugins_average_score.combine_values`<br><small>`combine_values(_key, values)`<br>line 16<br>plugins_average_score.py#L16-L20<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L16-L20)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_average_score.py#L16-L20)<br>Merge shard-local sum/count objects before the final reduce step.</small> | `plugins_average_score.benchmark_records`<br><small>`benchmark_records(scenario, records, seed, dataset_family='default')`<br>line 30<br>plugins_average_score.py#L30-L60<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L30-L60)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_average_score.py#L30-L60)<br>Generate deterministic cohort score fixtures for benchmark scenarios.</small> | `plugins_average_score.benchmark_notes`<br><small>`benchmark_notes(scenario, dataset_family='default')`<br>line 63<br>plugins_average_score.py#L63-L132<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L63-L132)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_average_score.py#L63-L132)<br>Describe the intended hot keys for each synthetic benchmark family.</small> | `default, exam-cram, project-week` |
| `plugin-rolling-window-join` | `projects/mini-mapreduce-lab/plugins_rolling_window_join.py` | `2332425c37ad` | Rolling-window join plugin for multi-stream correlation and pipeline-debug demos. | `plugins_rolling_window_join.map_records`<br><small>`map_records(lines)`<br>line 182<br>plugins_rolling_window_join.py#L182-L196<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L182-L196)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L182-L196)<br>Emit per-correlation-key event batches from key,side,timestamp,label rows.</small> | `plugins_rolling_window_join.reduce_key`<br><small>`reduce_key(key, values)`<br>line 204<br>plugins_rolling_window_join.py#L204-L270<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L204-L270)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L204-L270)<br>Pair left/right events within a rolling join window and summarize unmatched spillover.</small> | `plugins_rolling_window_join.combine_values`<br><small>`combine_values(_key, values)`<br>line 199<br>plugins_rolling_window_join.py#L199-L201<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L199-L201)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L199-L201)<br>Keep shard-local join candidates JSON-safe before final pairing.</small> | `plugins_rolling_window_join.benchmark_records`<br><small>`benchmark_records(scenario, records, seed, dataset_family='default')`<br>line 273<br>plugins_rolling_window_join.py#L273-L348<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L273-L348)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L273-L348)<br>Generate deterministic two-stream correlation fixtures for rolling join demos.</small> | `plugins_rolling_window_join.benchmark_notes`<br><small>`benchmark_notes(scenario, dataset_family='default')`<br>line 351<br>plugins_rolling_window_join.py#L351-L420<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L351-L420)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L351-L420)<br>Describe the intended join hotspot and portfolio story for each synthetic family.</small> | `default, checkout-funnel, incident-correlation` |
| `plugin-service-latency` | `projects/mini-mapreduce-lab/plugins_service_latency.py` | `2332425c37ad` | Service-latency summary plugin for observability-style benchmark demos. | `plugins_service_latency.map_records`<br><small>`map_records(lines)`<br>line 33<br>plugins_service_latency.py#L33-L46<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L33-L46)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_service_latency.py#L33-L46)<br>Parse comma-separated service/latency rows into partial latency summaries.</small> | `plugins_service_latency.reduce_key`<br><small>`reduce_key(_key, values)`<br>line 54<br>plugins_service_latency.py#L54-L64<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L54-L64)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_service_latency.py#L54-L64)<br>Return count, average, p95, and max latency for one service key.</small> | `plugins_service_latency.combine_values`<br><small>`combine_values(_key, values)`<br>line 49<br>plugins_service_latency.py#L49-L51<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L49-L51)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_service_latency.py#L49-L51)<br>Merge shard-local latency summaries before the final reduce step.</small> | `plugins_service_latency.benchmark_records`<br><small>`benchmark_records(scenario, records, seed, dataset_family='default')`<br>line 67<br>plugins_service_latency.py#L67-L131<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L67-L131)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_service_latency.py#L67-L131)<br>Generate deterministic latency fixtures for multiple observability-style families.</small> | `plugins_service_latency.benchmark_notes`<br><small>`benchmark_notes(scenario, dataset_family='default')`<br>line 134<br>plugins_service_latency.py#L134-L203<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L134-L203)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_service_latency.py#L134-L203)<br>Describe the intended hot services for each synthetic latency family.</small> | `default, incident-spike, batch-window` |
| `plugin-sessionization` | `projects/mini-mapreduce-lab/plugins_sessionization.py` | `2332425c37ad` | Sessionization analytics plugin for product-usage benchmark demos. | `plugins_sessionization.map_records`<br><small>`map_records(lines)`<br>line 52<br>plugins_sessionization.py#L52-L62<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_sessionization.py#L52-L62)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_sessionization.py#L52-L62)<br>Emit per-user session events from comma-separated user,timestamp,page rows.</small> | `plugins_sessionization.reduce_key`<br><small>`reduce_key(_key, values)`<br>line 70<br>plugins_sessionization.py#L70-L91<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_sessionization.py#L70-L91)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_sessionization.py#L70-L91)<br>Summarize session count, duration, and activity intensity for one user.</small> | `plugins_sessionization.combine_values`<br><small>`combine_values(_key, values)`<br>line 65<br>plugins_sessionization.py#L65-L67<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_sessionization.py#L65-L67)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_sessionization.py#L65-L67)<br>Keep shard-local event batches JSON-safe before global sessionization.</small> | `plugins_sessionization.benchmark_records`<br><small>`benchmark_records(scenario, records, seed, dataset_family='default')`<br>line 135<br>plugins_sessionization.py#L135-L206<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_sessionization.py#L135-L206)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_sessionization.py#L135-L206)<br>Generate deterministic product-analytics event streams for sessionization demos.</small> | `plugins_sessionization.benchmark_notes`<br><small>`benchmark_notes(scenario, dataset_family='default')`<br>line 209<br>plugins_sessionization.py#L209-L278<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_sessionization.py#L209-L278)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_sessionization.py#L209-L278)<br>Describe the intended hotspot users and browsing patterns for each family.</small> | `default, exam-revision, launch-day` |
| `plugin-streaming-window` | `projects/mini-mapreduce-lab/plugins_streaming_window.py` | `2332425c37ad` | Streaming-window aggregation plugin for telemetry-style benchmark demos. | `plugins_streaming_window.map_records`<br><small>`map_records(lines)`<br>line 73<br>plugins_streaming_window.py#L73-L90<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_streaming_window.py#L73-L90)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_streaming_window.py#L73-L90)<br>Emit per-stream, per-window summary objects from stream,timestamp,value rows.</small> | `plugins_streaming_window.reduce_key`<br><small>`reduce_key(key, values)`<br>line 98<br>plugins_streaming_window.py#L98-L123<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_streaming_window.py#L98-L123)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_streaming_window.py#L98-L123)<br>Return window-level count, range, and rate metrics for one stream bucket.</small> | `plugins_streaming_window.combine_values`<br><small>`combine_values(_key, values)`<br>line 93<br>plugins_streaming_window.py#L93-L95<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_streaming_window.py#L93-L95)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_streaming_window.py#L93-L95)<br>Merge shard-local window summaries before the final reduce step.</small> | `plugins_streaming_window.benchmark_records`<br><small>`benchmark_records(scenario, records, seed, dataset_family='default')`<br>line 139<br>plugins_streaming_window.py#L139-L212<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_streaming_window.py#L139-L212)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_streaming_window.py#L139-L212)<br>Generate deterministic windowed telemetry fixtures for benchmark scenarios.</small> | `plugins_streaming_window.benchmark_notes`<br><small>`benchmark_notes(scenario, dataset_family='default')`<br>line 215<br>plugins_streaming_window.py#L215-L284<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_streaming_window.py#L215-L284)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_streaming_window.py#L215-L284)<br>Describe the intended hot windows and portfolio story for each family.</small> | `default, iot-burst, live-ops` |
| `plugin-max-score` | `projects/mini-mapreduce-lab/plugins_top_score.py` | `2332425c37ad` | Maximum-score reducer plugin for simple leaderboard-style demos. | `plugins_top_score.map_records`<br><small>`map_records(lines)`<br>line 6<br>plugins_top_score.py#L6-L13<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_top_score.py#L6-L13)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_top_score.py#L6-L13)<br>Parse comma-separated score rows into integer leaderboard updates.</small> | `plugins_top_score.reduce_key`<br><small>`reduce_key(_key, values)`<br>line 21<br>plugins_top_score.py#L21-L23<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_top_score.py#L21-L23)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_top_score.py#L21-L23)<br>Return the overall maximum score for one student key.</small> | `plugins_top_score.combine_values`<br><small>`combine_values(_key, values)`<br>line 16<br>plugins_top_score.py#L16-L18<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_top_score.py#L16-L18)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_top_score.py#L16-L18)<br>Keep the shard-local maximum score for one student key.</small> | - | - | `-` |
| `plugin-watermark-late-summary` | `projects/mini-mapreduce-lab/plugins_watermark_late_summary.py` | `2332425c37ad` | Watermark-aware late-event summary plugin for out-of-order stream-processing demos. | `plugins_watermark_late_summary.map_records`<br><small>`map_records(lines)`<br>line 136<br>plugins_watermark_late_summary.py#L136-L147<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L136-L147)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L136-L147)<br>Emit per-stream event batches from stream,event_time,arrival_time,value rows.</small> | `plugins_watermark_late_summary.reduce_key`<br><small>`reduce_key(key, values)`<br>line 155<br>plugins_watermark_late_summary.py#L155-L223<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L155-L223)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L155-L223)<br>Summarize watermark-aware acceptance, late updates, and dropped events for one stream.</small> | `plugins_watermark_late_summary.combine_values`<br><small>`combine_values(_key, values)`<br>line 150<br>plugins_watermark_late_summary.py#L150-L152<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L150-L152)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L150-L152)<br>Keep shard-local stream event batches JSON-safe before watermark evaluation.</small> | `plugins_watermark_late_summary.benchmark_records`<br><small>`benchmark_records(scenario, records, seed, dataset_family='default')`<br>line 266<br>plugins_watermark_late_summary.py#L266-L341<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L266-L341)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L266-L341)<br>Generate deterministic out-of-order event streams for watermark-summary demos.</small> | `plugins_watermark_late_summary.benchmark_notes`<br><small>`benchmark_notes(scenario, dataset_family='default')`<br>line 344<br>plugins_watermark_late_summary.py#L344-L413<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L344-L413)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L344-L413)<br>Describe the intended late-event hotspot story for each synthetic family.</small> | `default, sensor-backfill, live-replay` |

## Hook source excerpts

### <a id="plugin-average-score"></a>`plugin-average-score`

- Repository commit: `2332425c37ad2eb7d0399cb11e91a2354e189d22`
#### Mapper: `plugins_average_score.map_records`
- Source anchor: `plugins_average_score.py#L7-L13`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L7-L13>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_average_score.py#L7-L13>

```python
def map_records(lines):
    """Emit per-student sum/count records from comma-separated score lines."""
    for line in lines:
        if not line.strip():
            continue
        name, score = line.split(",", 1)
        yield name.strip().lower(), {"sum": float(score), "count": 1}
```

#### Reducer: `plugins_average_score.reduce_key`
- Source anchor: `plugins_average_score.py#L23-L27`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L23-L27>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_average_score.py#L23-L27>

```python
def reduce_key(_key, values):
    """Return a rounded average score for one student key."""
    total = sum(item["sum"] for item in values)
    count = sum(item["count"] for item in values)
    return round(total / count, 3) if count else 0.0
```

#### Combiner: `plugins_average_score.combine_values`
- Source anchor: `plugins_average_score.py#L16-L20`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L16-L20>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_average_score.py#L16-L20>

```python
def combine_values(_key, values):
    """Merge shard-local sum/count objects before the final reduce step."""
    total = sum(item["sum"] for item in values)
    count = sum(item["count"] for item in values)
    return {"sum": total, "count": count}
```

#### Benchmark generator: `plugins_average_score.benchmark_records`
- Source anchor: `plugins_average_score.py#L30-L60`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L30-L60>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_average_score.py#L30-L60>

```python
def benchmark_records(scenario, records, seed, dataset_family="default"):
    """Generate deterministic cohort score fixtures for benchmark scenarios."""
    import random

    if records <= 0:
        raise ValueError("records must be positive")
    rng = random.Random(seed)

    if dataset_family == "default":
        if scenario == "balanced":
            students = [f"team-{index:02d}" for index in range(12)]
            return [f"{students[index % len(students)]},{72 + ((index * 9) % 19)}" for index in range(records)]
        if scenario == "skewed":
            hot_students = ["capstone-core"] * 16 + [f"rotation-{index}" for index in range(4)] + [f"elective-{index}" for index in range(10)]
            return [f"{rng.choice(hot_students)},{65 + rng.randint(0, 30)}" for _ in range(records)]
    elif dataset_family == "exam-cram":
        if scenario == "balanced":
            cohorts = [f"study-group-{index:02d}" for index in range(10)]
            return [f"{cohorts[index % len(cohorts)]},{78 + ((index * 7) % 15)}" for index in range(records)]
        if scenario == "skewed":
            hot_students = ["midterm-sprint"] * 18 + [f"review-{index}" for index in range(4)] + [f"prep-{index}" for index in range(12)]
            return [f"{rng.choice(hot_students)},{70 + rng.randint(0, 25)}" for _ in range(records)]
    elif dataset_family == "project-week":
        if scenario == "balanced":
            squads = [f"studio-{index:02d}" for index in range(8)]
            return [f"{squads[index % len(squads)]},{74 + ((index * 5) % 21)}" for index in range(records)]
        if scenario == "skewed":
            hot_students = ["demo-day-core"] * 12 + [f"integration-{index}" for index in range(6)] + [f"feature-{index}" for index in range(14)]
            return [f"{rng.choice(hot_students)},{68 + rng.randint(0, 28)}" for _ in range(records)]

    raise ValueError(f"unsupported plugin benchmark scenario/family: {scenario}/{dataset_family}")
```

#### Benchmark note hook: `plugins_average_score.benchmark_notes`
- Source anchor: `plugins_average_score.py#L63-L132`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L63-L132>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_average_score.py#L63-L132>

```python
def benchmark_notes(scenario, dataset_family="default"):
    """Describe the intended hot keys for each synthetic benchmark family."""
    notes = {
        ("balanced", "default"): [
            {
                "title": "Even cohort rotation",
                "detail": "The default balanced cohort rotates evenly across team labels, so average-score aggregation stays spread out and mostly tests framework overhead rather than hot students.",
                "severity": "info",
                "takeaway": "Treat any noticeable reducer imbalance here as partition spread, not as a workload-shaped hotspot.",
            },
        ],
        ("skewed", "default"): [
            {
                "title": "Capstone leader hotspot",
                "detail": "`capstone-core` is the dominant student key here, so the hottest reducer should look like one heavy project lead soaking up repeated score updates.",
                "severity": "watch",
                "hotspot_keys": ["capstone-core"],
                "takeaway": "Use this scenario to explain how a single standout key can dominate reducer traffic even when the final averages remain correct.",
            },
        ],
        ("balanced", "exam-cram"): [
            {
                "title": "Distributed study groups",
                "detail": "Balanced exam-cram fixtures distribute scores across study groups, which makes them a clean baseline before simulating deadline pressure.",
                "severity": "info",
                "takeaway": "This is the calm comparison point for the cram-week hotspot run.",
            },
        ],
        ("skewed", "exam-cram"): [
            {
                "title": "Cram-week surge",
                "detail": "`midterm-sprint` is intentionally overrepresented, so the report should surface one study cohort as the obvious hotspot during cram-week traffic.",
                "severity": "watch",
                "hotspot_keys": ["midterm-sprint"],
                "takeaway": "The skew should read like deadline-driven traffic, not like a partitioner bug.",
            },
        ],
        ("balanced", "project-week"): [
            {
                "title": "Studio squad baseline",
                "detail": "Balanced project-week fixtures rotate across studio squads so reducer load stays close even though the labels feel more portfolio-realistic than generic teams.",
                "severity": "info",
                "takeaway": "This family keeps the story portfolio-friendly without manufacturing a hotspot.",
            },
        ],
        ("skewed", "project-week"): [
            {
                "title": "Demo-day crunch hotspot",
                "detail": "`demo-day-core` is the main hotspot here, with integration and feature tails behind it, so you can narrate the skew as a deadline-driven project crunch.",
                "severity": "risk",
                "hotspot_keys": ["demo-day-core", "integration-0", "feature-0"],
                "takeaway": "This slice is meant to read like a real project-week bottleneck where one squad absorbs the final demo push.",
            },
            {
                "title": "Integration review backlog",
                "detail": "The `integration-*` keys form a second-tier hotspot behind the demo-day core, which makes a good reviewer note when you want to talk about handoff queues instead of only the primary spike.",
                "severity": "watch",
                "hotspot_keys": ["integration-0", "integration-1", "integration-2"],
                "takeaway": "Keep this card when you want a fuller systems story about follow-on bottlenecks after the main project crunch.",
            },
            {
                "title": "Feature-lane tail",
                "detail": "The `feature-*` keys stay spread out and comparatively cooler, so they are useful as a low-priority reviewer note but often safe to collapse in tighter portfolio reports.",
                "severity": "info",
                "hotspot_keys": ["feature-0", "feature-1"],
                "takeaway": "Use annotation filters or overflow summaries when you want to hide softer follow-up notes and keep the report focused on the highest-risk queues.",
            },
        ],
    }
    return notes.get((scenario, dataset_family), [])
```

### <a id="plugin-rolling-window-join"></a>`plugin-rolling-window-join`

- Repository commit: `2332425c37ad2eb7d0399cb11e91a2354e189d22`
#### Mapper: `plugins_rolling_window_join.map_records`
- Source anchor: `plugins_rolling_window_join.py#L182-L196`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L182-L196>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L182-L196>

```python
def map_records(lines):
    """Emit per-correlation-key event batches from key,side,timestamp,label rows."""
    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            continue
        key, side, event_at, label = [part.strip() for part in stripped.split(",", maxsplit=3)]
        normalized_side = side.lower()
        if normalized_side not in {"left", "right"}:
            raise ValueError("rolling-window-join side must be 'left' or 'right'")
        yield key.lower(), {
            "side": normalized_side,
            "event_at": _isoformat_z(_parse_timestamp(event_at)),
            "label": label,
        }
```

#### Reducer: `plugins_rolling_window_join.reduce_key`
- Source anchor: `plugins_rolling_window_join.py#L204-L270`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L204-L270>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L204-L270>

```python
def reduce_key(key, values):
    """Pair left/right events within a rolling join window and summarize unmatched spillover."""
    merged = _merge_event_batches(values)
    events = merged["events"]
    left_events = [event for event in events if event["side"] == "left"]
    right_events = [event for event in events if event["side"] == "right"]
    used_right = set()
    windows = {}
    gap_seconds_values = []

    for left_event in left_events:
        left_time = _parse_timestamp(left_event["event_at"])
        best_index = None
        best_gap = None
        for index, right_event in enumerate(right_events):
            if index in used_right:
                continue
            right_time = _parse_timestamp(right_event["event_at"])
            gap_seconds = abs((right_time - left_time).total_seconds())
            if gap_seconds > JOIN_WINDOW_SECONDS:
                continue
            if best_index is None or gap_seconds < best_gap or (
                gap_seconds == best_gap and right_event["event_at"] < right_events[best_index]["event_at"]
            ):
                best_index = index
                best_gap = gap_seconds
        if best_index is None:
            _record_unmatched(windows, event=left_event, side="left")
            continue
        used_right.add(best_index)
        matched_right = right_events[best_index]
        gap_seconds = float(best_gap if best_gap is not None else 0.0)
        gap_seconds_values.append(gap_seconds)
        _record_matched_pair(windows, left_event=left_event, right_event=matched_right, gap_seconds=gap_seconds)

    for index, right_event in enumerate(right_events):
        if index not in used_right:
            _record_unmatched(windows, event=right_event, side="right")

    finalized_windows = [_finalize_window_summary(windows[window_key]) for window_key in sorted(windows)]
    matched_pairs = sum(item["matched_pairs"] for item in finalized_windows)
    unmatched_left = sum(item["left_only_events"] for item in finalized_windows)
    unmatched_right = sum(item["right_only_events"] for item in finalized_windows)
    total_left = sum(item["left_events"] for item in finalized_windows)
    total_right = sum(item["right_events"] for item in finalized_windows)
    hottest_window = max(
        finalized_windows,
        key=lambda item: (item["matched_pairs"], item["left_events"] + item["right_events"], item["window_start"]),
        default=None,
    )
    matched_candidate_total = min(total_left, total_right)
    return {
        "correlation_key": key,
        "window_count": len(finalized_windows),
        "left_events": total_left,
        "right_events": total_right,
        "matched_pairs": matched_pairs,
        "unmatched_left_events": unmatched_left,
        "unmatched_right_events": unmatched_right,
        "join_coverage_rate": round(matched_pairs / matched_candidate_total, 3) if matched_candidate_total else 0.0,
        "avg_gap_seconds": round(sum(gap_seconds_values) / len(gap_seconds_values), 3) if gap_seconds_values else 0.0,
        "max_gap_seconds": round(max(gap_seconds_values), 3) if gap_seconds_values else 0.0,
        "join_window_minutes": JOIN_WINDOW_MINUTES,
        "hottest_window_start": hottest_window["window_start"] if hottest_window else None,
        "hottest_window_matches": hottest_window["matched_pairs"] if hottest_window else 0,
        "windows": finalized_windows,
    }
```

#### Combiner: `plugins_rolling_window_join.combine_values`
- Source anchor: `plugins_rolling_window_join.py#L199-L201`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L199-L201>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L199-L201>

```python
def combine_values(_key, values):
    """Keep shard-local join candidates JSON-safe before final pairing."""
    return {"events": sorted(values, key=lambda event: (event["event_at"], event["side"], event["label"]))}
```

#### Benchmark generator: `plugins_rolling_window_join.benchmark_records`
- Source anchor: `plugins_rolling_window_join.py#L273-L348`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L273-L348>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L273-L348>

```python
def benchmark_records(scenario, records, seed, dataset_family="default"):
    """Generate deterministic two-stream correlation fixtures for rolling join demos."""
    if records <= 0:
        raise ValueError("records must be positive")
    rng = random.Random(seed)
    base_time = datetime(2026, 4, 17, 9, 0, tzinfo=timezone.utc)

    families = {
        "default": {
            "balanced": [
                {"key": "join-pod-alpha", "weight": 1.0, "window_offsets": [0, 5, 10], "left_label": "request-start", "right_label": "request-finish", "match_ratio": 0.86, "right_lag_seconds": 52},
                {"key": "join-pod-beta", "weight": 1.0, "window_offsets": [0, 5, 10], "left_label": "request-start", "right_label": "request-finish", "match_ratio": 0.84, "right_lag_seconds": 61},
                {"key": "join-pod-gamma", "weight": 1.0, "window_offsets": [5, 10, 15], "left_label": "request-start", "right_label": "request-finish", "match_ratio": 0.83, "right_lag_seconds": 57},
                {"key": "join-pod-delta", "weight": 1.0, "window_offsets": [0, 10, 15], "left_label": "request-start", "right_label": "request-finish", "match_ratio": 0.82, "right_lag_seconds": 68},
            ],
            "skewed": [
                {"key": "join-hotspot", "weight": 4.0, "window_offsets": [10, 10, 15], "left_label": "request-start", "right_label": "request-finish", "match_ratio": 0.72, "right_lag_seconds": 97, "hotspot_offsets": [10], "hotspot_bonus": 40, "left_only_share": 0.7},
                {"key": "join-pod-beta", "weight": 1.1, "window_offsets": [0, 10, 15], "left_label": "request-start", "right_label": "request-finish", "match_ratio": 0.82, "right_lag_seconds": 64},
                {"key": "join-pod-gamma", "weight": 1.0, "window_offsets": [5, 15, 20], "left_label": "request-start", "right_label": "request-finish", "match_ratio": 0.8, "right_lag_seconds": 70},
                {"key": "join-pod-delta", "weight": 0.9, "window_offsets": [0, 15, 20], "left_label": "request-start", "right_label": "request-finish", "match_ratio": 0.78, "right_lag_seconds": 75},
            ],
        },
        "checkout-funnel": {
            "balanced": [
                {"key": "checkout-core", "weight": 1.2, "window_offsets": [5, 10, 15], "left_label": "cart-update", "right_label": "payment-auth", "match_ratio": 0.88, "right_lag_seconds": 48},
                {"key": "express-lane", "weight": 1.0, "window_offsets": [5, 10, 15], "left_label": "cart-update", "right_label": "payment-auth", "match_ratio": 0.9, "right_lag_seconds": 38},
                {"key": "promo-retry", "weight": 1.0, "window_offsets": [0, 10, 20], "left_label": "cart-update", "right_label": "payment-auth", "match_ratio": 0.8, "right_lag_seconds": 66},
                {"key": "inventory-sync", "weight": 0.9, "window_offsets": [0, 5, 15], "left_label": "cart-update", "right_label": "payment-auth", "match_ratio": 0.84, "right_lag_seconds": 58},
            ],
            "skewed": [
                {"key": "checkout-core", "weight": 4.3, "window_offsets": [10, 10, 15], "left_label": "cart-update", "right_label": "payment-auth", "match_ratio": 0.7, "right_lag_seconds": 102, "hotspot_offsets": [10], "hotspot_bonus": 55, "left_only_share": 0.75},
                {"key": "promo-retry", "weight": 1.5, "window_offsets": [10, 15, 20], "left_label": "cart-update", "right_label": "payment-auth", "match_ratio": 0.76, "right_lag_seconds": 88, "hotspot_offsets": [15], "hotspot_bonus": 32, "left_only_share": 0.65},
                {"key": "express-lane", "weight": 1.0, "window_offsets": [5, 15, 20], "left_label": "cart-update", "right_label": "payment-auth", "match_ratio": 0.86, "right_lag_seconds": 42},
                {"key": "inventory-sync", "weight": 0.8, "window_offsets": [0, 10, 20], "left_label": "cart-update", "right_label": "payment-auth", "match_ratio": 0.8, "right_lag_seconds": 63},
            ],
        },
        "incident-correlation": {
            "balanced": [
                {"key": "payments-api", "weight": 1.1, "window_offsets": [0, 5, 10], "left_label": "alert-fired", "right_label": "deploy-event", "match_ratio": 0.83, "right_lag_seconds": 74},
                {"key": "auth-gateway", "weight": 1.0, "window_offsets": [0, 10, 15], "left_label": "alert-fired", "right_label": "deploy-event", "match_ratio": 0.82, "right_lag_seconds": 81},
                {"key": "search-api", "weight": 1.0, "window_offsets": [5, 10, 20], "left_label": "alert-fired", "right_label": "deploy-event", "match_ratio": 0.84, "right_lag_seconds": 72},
                {"key": "edge-cache", "weight": 0.9, "window_offsets": [0, 15, 20], "left_label": "alert-fired", "right_label": "deploy-event", "match_ratio": 0.8, "right_lag_seconds": 90},
            ],
            "skewed": [
                {"key": "payments-api", "weight": 4.1, "window_offsets": [15, 20, 20], "left_label": "alert-fired", "right_label": "deploy-event", "match_ratio": 0.68, "right_lag_seconds": 118, "hotspot_offsets": [20], "hotspot_bonus": 48, "left_only_share": 0.72},
                {"key": "auth-gateway", "weight": 1.4, "window_offsets": [10, 15, 20], "left_label": "alert-fired", "right_label": "deploy-event", "match_ratio": 0.74, "right_lag_seconds": 96, "hotspot_offsets": [15], "hotspot_bonus": 26, "left_only_share": 0.62},
                {"key": "search-api", "weight": 1.0, "window_offsets": [5, 15, 25], "left_label": "alert-fired", "right_label": "deploy-event", "match_ratio": 0.82, "right_lag_seconds": 77},
                {"key": "edge-cache", "weight": 0.8, "window_offsets": [0, 10, 25], "left_label": "alert-fired", "right_label": "deploy-event", "match_ratio": 0.78, "right_lag_seconds": 88},
            ],
        },
    }
    if dataset_family not in families or scenario not in families[dataset_family]:
        raise ValueError(f"unsupported plugin benchmark scenario/family: {scenario}/{dataset_family}")

    profiles = families[dataset_family][scenario]
    counts = _allocate_counts(records, [profile["weight"] for profile in profiles])
    lines = []
    for profile, count in zip(profiles, counts):
        lines.extend(
            _generate_join_events(
                key=profile["key"],
                count=count,
                base_time=base_time,
                window_offsets=profile["window_offsets"],
                left_label=profile["left_label"],
                right_label=profile["right_label"],
                rng=rng,
                match_ratio=profile["match_ratio"],
                right_lag_seconds=profile["right_lag_seconds"],
                hotspot_offsets=profile.get("hotspot_offsets"),
                hotspot_bonus=profile.get("hotspot_bonus", 0),
                left_only_share=profile.get("left_only_share", 0.5),
            )
        )
    lines.sort(key=lambda line: tuple(line.split(",", maxsplit=3)[:3]))
    return lines[:records]
```

#### Benchmark note hook: `plugins_rolling_window_join.benchmark_notes`
- Source anchor: `plugins_rolling_window_join.py#L351-L420`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L351-L420>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L351-L420>

```python
def benchmark_notes(scenario, dataset_family="default"):
    """Describe the intended join hotspot and portfolio story for each synthetic family."""
    notes = {
        ("balanced", "default"): [
            {
                "title": "Steady correlation baseline",
                "detail": "The default balanced family keeps four correlation keys close together with only mild spillover, so the report reads like a healthy request/response join workload instead of an incident.",
                "severity": "info",
                "takeaway": "Use this as the before state when explaining how one correlation key can dominate a rolling join workload even if the reducer partitioner stays deterministic.",
            },
        ],
        ("skewed", "default"): [
            {
                "title": "Join hotspot concentration",
                "detail": "`join-hotspot` absorbs most of the left/right traffic here, so the hottest reducer should read like one correlation key monopolizing the join stage and leaving extra unmatched left events behind.",
                "severity": "watch",
                "hotspot_keys": ["join-hotspot"],
                "takeaway": "This is the simplest story for showing why stream joins introduce both hotspot pressure and mismatch cleanup work.",
            },
        ],
        ("balanced", "checkout-funnel"): [
            {
                "title": "Healthy checkout handoff",
                "detail": "The balanced checkout family keeps `cart-update` and `payment-auth` events closely paired across several flows, so the join output reads like a normal purchase funnel rather than a broken queue.",
                "severity": "info",
                "takeaway": "Good for presenting the plugin as a product/commerce analytics example instead of only infra telemetry.",
            },
        ],
        ("skewed", "checkout-funnel"): [
            {
                "title": "Checkout core backlog",
                "detail": "`checkout-core` becomes the dominant join key with the worst pairing lag, so the report looks like a spike of cart updates outrunning payment authorizations during a launch or sale.",
                "severity": "risk",
                "hotspot_keys": ["checkout-core"],
                "takeaway": "Call out the combination of lower coverage and higher gap when telling the story of queue lag or degraded downstream auth capacity.",
            },
            {
                "title": "Promo retry spillover",
                "detail": "`promo-retry` is the second-tier correlation hotspot behind checkout-core, which helps explain how retries can spread join pressure to a supporting flow instead of one isolated key.",
                "severity": "watch",
                "hotspot_keys": ["promo-retry"],
                "takeaway": "Keep this note when you want the benchmark to feel like a fuller checkout system instead of one synthetic broken key.",
            },
        ],
        ("balanced", "incident-correlation"): [
            {
                "title": "Routine alert/deploy audit trail",
                "detail": "The balanced incident-correlation family keeps alerts and deploy events close enough that the join output reads like a calm incident-review dashboard instead of a chaotic release.",
                "severity": "info",
                "takeaway": "Use this as the steady baseline before a noisy release or rollback starts separating alerts from the deploys that explain them.",
            },
        ],
        ("skewed", "incident-correlation"): [
            {
                "title": "Payments incident war room",
                "detail": "`payments-api` dominates the skewed incident family with long join gaps and extra unmatched alerts, so the benchmark looks like a release that triggered alarms faster than deploy metadata propagated.",
                "severity": "risk",
                "hotspot_keys": ["payments-api"],
                "takeaway": "This turns the plugin into a systems-debugging narrative about correlating alerts, deploys, and lagging metadata streams.",
            },
            {
                "title": "Auth gateway follow-on noise",
                "detail": "`auth-gateway` forms a smaller supporting hotspot that helps the report tell a more realistic multi-service release story instead of one isolated outage key.",
                "severity": "watch",
                "hotspot_keys": ["auth-gateway"],
                "takeaway": "Keep this note when you want to explain correlated release fallout across adjacent services.",
            },
        ],
    }
    return notes.get((scenario, dataset_family), [])
```

### <a id="plugin-service-latency"></a>`plugin-service-latency`

- Repository commit: `2332425c37ad2eb7d0399cb11e91a2354e189d22`
#### Mapper: `plugins_service_latency.map_records`
- Source anchor: `plugins_service_latency.py#L33-L46`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L33-L46>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_service_latency.py#L33-L46>

```python
def map_records(lines):
    """Parse comma-separated service/latency rows into partial latency summaries."""
    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            continue
        service, latency_ms = stripped.split(",", maxsplit=1)
        latency_value = round(float(latency_ms.strip()), 3)
        yield service.strip().lower(), {
            "count": 1,
            "sum_ms": latency_value,
            "max_ms": latency_value,
            "samples_ms": [latency_value],
        }
```

#### Reducer: `plugins_service_latency.reduce_key`
- Source anchor: `plugins_service_latency.py#L54-L64`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L54-L64>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_service_latency.py#L54-L64>

```python
def reduce_key(_key, values):
    """Return count, average, p95, and max latency for one service key."""
    merged = _merge_latency_values(values)
    count = int(merged["count"])
    average = round(float(merged["sum_ms"]) / count, 3) if count else 0.0
    return {
        "count": count,
        "avg_ms": average,
        "p95_ms": _nearest_rank_percentile(merged["samples_ms"], 95),
        "max_ms": round(float(merged["max_ms"]), 3),
    }
```

#### Combiner: `plugins_service_latency.combine_values`
- Source anchor: `plugins_service_latency.py#L49-L51`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L49-L51>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_service_latency.py#L49-L51>

```python
def combine_values(_key, values):
    """Merge shard-local latency summaries before the final reduce step."""
    return _merge_latency_values(values)
```

#### Benchmark generator: `plugins_service_latency.benchmark_records`
- Source anchor: `plugins_service_latency.py#L67-L131`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L67-L131>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_service_latency.py#L67-L131>

```python
def benchmark_records(scenario, records, seed, dataset_family="default"):
    """Generate deterministic latency fixtures for multiple observability-style families."""
    if records <= 0:
        raise ValueError("records must be positive")
    rng = random.Random(seed)

    families = {
        "default": {
            "balanced": [
                ("edge-api", 82, 9),
                ("catalog-api", 76, 8),
                ("checkout-api", 88, 10),
                ("search-api", 71, 7),
            ],
            "skewed": [
                ("edge-api", 144, 26),
                ("catalog-api", 84, 10),
                ("checkout-api", 96, 12),
                ("search-api", 74, 8),
            ],
        },
        "incident-spike": {
            "balanced": [
                ("auth-gateway", 118, 12),
                ("session-cache", 89, 8),
                ("token-service", 102, 10),
                ("profile-read", 78, 7),
            ],
            "skewed": [
                ("auth-gateway", 236, 54),
                ("session-cache", 148, 22),
                ("token-service", 121, 14),
                ("profile-read", 83, 9),
            ],
        },
        "batch-window": {
            "balanced": [
                ("warehouse-loader", 264, 30),
                ("index-builder", 221, 24),
                ("backfill-runner", 246, 27),
                ("metrics-rollup", 198, 21),
            ],
            "skewed": [
                ("warehouse-loader", 462, 86),
                ("index-builder", 274, 34),
                ("backfill-runner", 318, 42),
                ("metrics-rollup", 206, 25),
            ],
        },
    }
    if dataset_family not in families or scenario not in families[dataset_family]:
        raise ValueError(f"unsupported plugin benchmark scenario/family: {scenario}/{dataset_family}")

    templates = families[dataset_family][scenario]
    lines = []
    for index in range(records):
        service, base_ms, spread_ms = templates[index % len(templates)]
        jitter = rng.randint(-spread_ms, spread_ms)
        lines.append(f"{service},{round(base_ms + jitter, 3)}")
    if scenario == "skewed":
        hotspot = templates[0][0]
        for index in range(max(1, records // 3)):
            latency = templates[0][1] + templates[0][2] + rng.randint(18, 52)
            lines[index] = f"{hotspot},{round(latency, 3)}"
    return lines
```

#### Benchmark note hook: `plugins_service_latency.benchmark_notes`
- Source anchor: `plugins_service_latency.py#L134-L203`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L134-L203>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_service_latency.py#L134-L203>

```python
def benchmark_notes(scenario, dataset_family="default"):
    """Describe the intended hot services for each synthetic latency family."""
    notes = {
        ("balanced", "default"): [
            {
                "title": "Healthy service spread",
                "detail": "The default balanced latency family rotates evenly across four APIs, so reducer load should stay close while the output still looks like a small production stack.",
                "severity": "info",
                "takeaway": "Use this as the calm baseline before introducing latency hotspots or on-call incident narratives.",
            },
        ],
        ("skewed", "default"): [
            {
                "title": "Edge API hotspot",
                "detail": "`edge-api` is intentionally heavier and slower here, so the hottest reducer should read like a front-door latency spike instead of a partitioning accident.",
                "severity": "watch",
                "hotspot_keys": ["edge-api"],
                "takeaway": "This is the simplest observability-style story for discussing why p95 matters more than the mean under hotspot traffic.",
            },
        ],
        ("balanced", "incident-spike"): [
            {
                "title": "Steady auth baseline",
                "detail": "The balanced incident family keeps auth, cache, token, and profile services close enough that the report highlights normal service-to-service variance rather than an outage.",
                "severity": "info",
                "takeaway": "This is the before state for the incident-spike storyline.",
            },
        ],
        ("skewed", "incident-spike"): [
            {
                "title": "Auth gateway timeout storm",
                "detail": "`auth-gateway` dominates this family with elevated latency, so the hottest reducer should look like an outage-era timeout storm concentrated around one service.",
                "severity": "risk",
                "hotspot_keys": ["auth-gateway"],
                "takeaway": "Call out the gap between average and p95 latency here to explain why long-tail spikes matter during incidents.",
            },
            {
                "title": "Session cache spillover",
                "detail": "`session-cache` forms the second-tier hotspot behind the auth gateway, which helps tell a broader bottleneck story about downstream spillover instead of a single bad node.",
                "severity": "watch",
                "hotspot_keys": ["session-cache"],
                "takeaway": "Keep this annotation when you want a fuller causal narrative about cascading latency during the same incident.",
            },
            {
                "title": "Profile path cool lane",
                "detail": "`profile-read` stays comparatively cool, so it works as a low-priority contrast point or a card to collapse in tighter portfolio reports.",
                "severity": "info",
                "hotspot_keys": ["profile-read"],
                "takeaway": "Use annotation filtering when you want the report to focus only on the riskiest paths.",
            },
        ],
        ("balanced", "batch-window"): [
            {
                "title": "Even batch cadence",
                "detail": "The balanced batch-window family rotates evenly across warehouse, indexing, backfill, and metrics jobs so the reducer heatmap reflects a normal overnight data window.",
                "severity": "info",
                "takeaway": "This family is useful when you want a data-engineering story rather than an incident-response story.",
            },
        ],
        ("skewed", "batch-window"): [
            {
                "title": "Warehouse loader saturation",
                "detail": "`warehouse-loader` is intentionally the hottest and slowest key here, so the benchmark looks like a batch-window saturation problem during an oversized ingest run.",
                "severity": "watch",
                "hotspot_keys": ["warehouse-loader"],
                "takeaway": "Use this family to talk about long-running ETL contention and why reducer skew can line up with operational bottlenecks.",
            },
        ],
    }
    return notes.get((scenario, dataset_family), [])
```

### <a id="plugin-sessionization"></a>`plugin-sessionization`

- Repository commit: `2332425c37ad2eb7d0399cb11e91a2354e189d22`
#### Mapper: `plugins_sessionization.map_records`
- Source anchor: `plugins_sessionization.py#L52-L62`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_sessionization.py#L52-L62>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_sessionization.py#L52-L62>

```python
def map_records(lines):
    """Emit per-user session events from comma-separated user,timestamp,page rows."""
    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            continue
        user_id, timestamp, page = [part.strip() for part in stripped.split(",", maxsplit=2)]
        yield user_id.lower(), {
            "timestamp": _isoformat_z(_parse_timestamp(timestamp)),
            "page": page,
        }
```

#### Reducer: `plugins_sessionization.reduce_key`
- Source anchor: `plugins_sessionization.py#L70-L91`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_sessionization.py#L70-L91>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_sessionization.py#L70-L91>

```python
def reduce_key(_key, values):
    """Summarize session count, duration, and activity intensity for one user."""
    merged = _merge_event_batches(values)
    events = merged["events"]
    sessions = _session_summaries(events)
    durations = []
    for session in sessions:
        start = _parse_timestamp(session[0]["timestamp"])
        end = _parse_timestamp(session[-1]["timestamp"])
        durations.append(round((end - start).total_seconds() / 60, 3))
    total_events = len(events)
    session_count = len(sessions)
    return {
        "session_count": session_count,
        "total_events": total_events,
        "avg_events_per_session": round(total_events / session_count, 3) if session_count else 0.0,
        "avg_session_minutes": round(sum(durations) / session_count, 3) if session_count else 0.0,
        "longest_session_events": max((len(session) for session in sessions), default=0),
        "longest_session_minutes": max(durations, default=0.0),
        "first_event_at": events[0]["timestamp"] if events else None,
        "last_event_at": events[-1]["timestamp"] if events else None,
    }
```

#### Combiner: `plugins_sessionization.combine_values`
- Source anchor: `plugins_sessionization.py#L65-L67`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_sessionization.py#L65-L67>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_sessionization.py#L65-L67>

```python
def combine_values(_key, values):
    """Keep shard-local event batches JSON-safe before global sessionization."""
    return {"events": sorted(values, key=lambda event: event["timestamp"])}
```

#### Benchmark generator: `plugins_sessionization.benchmark_records`
- Source anchor: `plugins_sessionization.py#L135-L206`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_sessionization.py#L135-L206>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_sessionization.py#L135-L206>

```python
def benchmark_records(scenario, records, seed, dataset_family="default"):
    """Generate deterministic product-analytics event streams for sessionization demos."""
    if records <= 0:
        raise ValueError("records must be positive")
    rng = random.Random(seed)
    base_time = datetime(2026, 4, 17, 8, 0, tzinfo=timezone.utc)

    families = {
        "default": {
            "balanced": [
                {"user": "student-alpha", "weight": 1.0, "session_size": 3, "session_gap": 52, "intra_gap": 5, "pages": ["home", "lecture-notes", "quiz"]},
                {"user": "student-beta", "weight": 1.0, "session_size": 3, "session_gap": 48, "intra_gap": 4, "pages": ["home", "lab", "forum"]},
                {"user": "student-gamma", "weight": 1.0, "session_size": 4, "session_gap": 56, "intra_gap": 5, "pages": ["home", "editor", "submissions"]},
                {"user": "student-delta", "weight": 1.0, "session_size": 3, "session_gap": 50, "intra_gap": 4, "pages": ["home", "flashcards", "quiz"]},
            ],
            "skewed": [
                {"user": "student-alpha", "weight": 3.3, "session_size": 5, "session_gap": 38, "intra_gap": 4, "pages": ["home", "lecture-notes", "quiz", "editor"]},
                {"user": "student-beta", "weight": 1.0, "session_size": 3, "session_gap": 55, "intra_gap": 5, "pages": ["home", "lab", "forum"]},
                {"user": "student-gamma", "weight": 0.9, "session_size": 3, "session_gap": 58, "intra_gap": 5, "pages": ["home", "editor", "submissions"]},
                {"user": "student-delta", "weight": 0.8, "session_size": 2, "session_gap": 62, "intra_gap": 6, "pages": ["home", "flashcards", "quiz"]},
            ],
        },
        "exam-revision": {
            "balanced": [
                {"user": "night-owl", "weight": 1.1, "session_size": 4, "session_gap": 46, "intra_gap": 4, "pages": ["review-guide", "quiz", "flashcards"]},
                {"user": "lab-partner", "weight": 1.0, "session_size": 3, "session_gap": 50, "intra_gap": 5, "pages": ["practice-exam", "solutions", "forum"]},
                {"user": "project-mate", "weight": 1.0, "session_size": 3, "session_gap": 54, "intra_gap": 5, "pages": ["review-guide", "editor", "submission"]},
                {"user": "commuter", "weight": 0.9, "session_size": 2, "session_gap": 58, "intra_gap": 6, "pages": ["flashcards", "quiz", "summary"]},
            ],
            "skewed": [
                {"user": "night-owl", "weight": 3.8, "session_size": 6, "session_gap": 34, "intra_gap": 4, "pages": ["review-guide", "quiz", "quiz-review", "flashcards"]},
                {"user": "lab-partner", "weight": 1.0, "session_size": 3, "session_gap": 52, "intra_gap": 5, "pages": ["practice-exam", "solutions", "forum"]},
                {"user": "project-mate", "weight": 0.9, "session_size": 3, "session_gap": 56, "intra_gap": 5, "pages": ["review-guide", "editor", "submission"]},
                {"user": "commuter", "weight": 0.7, "session_size": 2, "session_gap": 64, "intra_gap": 6, "pages": ["flashcards", "quiz", "summary"]},
            ],
        },
        "launch-day": {
            "balanced": [
                {"user": "release-lead", "weight": 1.1, "session_size": 4, "session_gap": 42, "intra_gap": 4, "pages": ["overview", "health", "errors", "deploy"]},
                {"user": "qa-desk", "weight": 1.0, "session_size": 3, "session_gap": 48, "intra_gap": 5, "pages": ["smoke-tests", "errors", "feedback"]},
                {"user": "support-ops", "weight": 1.0, "session_size": 3, "session_gap": 50, "intra_gap": 5, "pages": ["tickets", "feedback", "health"]},
                {"user": "analytics-watch", "weight": 0.9, "session_size": 3, "session_gap": 54, "intra_gap": 5, "pages": ["overview", "conversion", "health"]},
            ],
            "skewed": [
                {"user": "release-lead", "weight": 4.0, "session_size": 6, "session_gap": 31, "intra_gap": 4, "pages": ["overview", "health", "errors", "deploy", "rollback"]},
                {"user": "qa-desk", "weight": 1.1, "session_size": 4, "session_gap": 44, "intra_gap": 5, "pages": ["smoke-tests", "errors", "feedback"]},
                {"user": "support-ops", "weight": 1.0, "session_size": 3, "session_gap": 50, "intra_gap": 5, "pages": ["tickets", "feedback", "health"]},
                {"user": "analytics-watch", "weight": 0.8, "session_size": 2, "session_gap": 58, "intra_gap": 6, "pages": ["overview", "conversion", "health"]},
            ],
        },
    }
    if dataset_family not in families or scenario not in families[dataset_family]:
        raise ValueError(f"unsupported plugin benchmark scenario/family: {scenario}/{dataset_family}")

    profiles = families[dataset_family][scenario]
    counts = _allocate_counts(records, [profile["weight"] for profile in profiles])
    events = []
    for index, (profile, count) in enumerate(zip(profiles, counts)):
        start_offset = timedelta(minutes=(index * 9) + rng.randint(0, 4))
        events.extend(
            _generate_user_events(
                user=profile["user"],
                count=count,
                start_at=base_time + start_offset,
                session_size=profile["session_size"],
                session_gap_minutes=profile["session_gap"] + rng.randint(-3, 3),
                intra_gap_minutes=profile["intra_gap"],
                pages=profile["pages"],
            )
        )
    events.sort(key=lambda item: item["timestamp"])
    return [f"{event['user']},{event['timestamp']},{event['page']}" for event in events[:records]]
```

#### Benchmark note hook: `plugins_sessionization.benchmark_notes`
- Source anchor: `plugins_sessionization.py#L209-L278`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_sessionization.py#L209-L278>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_sessionization.py#L209-L278>

```python
def benchmark_notes(scenario, dataset_family="default"):
    """Describe the intended hotspot users and browsing patterns for each family."""
    notes = {
        ("balanced", "default"): [
            {
                "title": "Even study cadence",
                "detail": "The default balanced family spreads activity across four students with similarly sized bursts, so reducer load should stay close while the output still demonstrates session boundaries.",
                "severity": "info",
                "takeaway": "Use this as the calm baseline before showing why repeated bursts from one user change the session story.",
            },
        ],
        ("skewed", "default"): [
            {
                "title": "Student alpha cram loop",
                "detail": "`student-alpha` revisits notes, quizzes, and the editor in repeated short bursts, so the hottest reducer should look like one user driving most session starts and events.",
                "severity": "watch",
                "hotspot_keys": ["student-alpha"],
                "takeaway": "This is the simplest sessionization story for discussing hot users versus evenly distributed class traffic.",
            },
        ],
        ("balanced", "exam-revision"): [
            {
                "title": "Shared review week",
                "detail": "The balanced exam family keeps revision activity spread across multiple learners and shorter study sessions, which makes the session summaries read like a healthy pre-exam baseline.",
                "severity": "info",
                "takeaway": "Good for explaining why session counts alone are not enough without session length and event intensity.",
            },
        ],
        ("skewed", "exam-revision"): [
            {
                "title": "Night-owl marathon",
                "detail": "`night-owl` owns most of the benchmark volume here with repeated late-session bursts, so the reducer heatmap should show one learner dominating both activity and longest-session metrics.",
                "severity": "risk",
                "hotspot_keys": ["night-owl"],
                "takeaway": "Call out how sessionization turns a raw clickstream into a workload story about sustained study behavior instead of isolated page hits.",
            },
            {
                "title": "Commuter quick checks",
                "detail": "`commuter` stays small and bursty, which makes it a useful low-priority contrast key when tightening the portfolio narrative down to the primary hotspot.",
                "severity": "info",
                "hotspot_keys": ["commuter"],
                "takeaway": "This annotation is a good candidate to collapse in portfolio-tight reports.",
            },
        ],
        ("balanced", "launch-day"): [
            {
                "title": "Coordinated launch monitoring",
                "detail": "The balanced launch-day family keeps release, QA, support, and analytics roles close enough that the session summary reads like a calm release checklist instead of an incident.",
                "severity": "info",
                "takeaway": "Use this as the before state for the launch-day hotspot story.",
            },
        ],
        ("skewed", "launch-day"): [
            {
                "title": "Release lead war room",
                "detail": "`release-lead` dominates this family with back-to-back dashboard, deploy, and rollback visits, so the hottest reducer should look like one operator repeatedly re-entering a release war room.",
                "severity": "risk",
                "hotspot_keys": ["release-lead"],
                "takeaway": "This turns the plugin into a product-analytics case study about launch-day behavior rather than generic score aggregation.",
            },
            {
                "title": "QA desk verification loop",
                "detail": "`qa-desk` forms a second-tier hotspot behind the release lead, which helps the report show supporting verification traffic instead of a single isolated key.",
                "severity": "watch",
                "hotspot_keys": ["qa-desk"],
                "takeaway": "Keep this note when you want a fuller multi-role launch narrative in the benchmark report.",
            },
        ],
    }
    return notes.get((scenario, dataset_family), [])
```

### <a id="plugin-streaming-window"></a>`plugin-streaming-window`

- Repository commit: `2332425c37ad2eb7d0399cb11e91a2354e189d22`
#### Mapper: `plugins_streaming_window.map_records`
- Source anchor: `plugins_streaming_window.py#L73-L90`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_streaming_window.py#L73-L90>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_streaming_window.py#L73-L90>

```python
def map_records(lines):
    """Emit per-stream, per-window summary objects from stream,timestamp,value rows."""
    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            continue
        stream, timestamp, value = [part.strip() for part in stripped.split(",", maxsplit=2)]
        parsed_timestamp = _parse_timestamp(timestamp)
        window_start = _window_start(parsed_timestamp)
        numeric_value = round(float(value), 3)
        yield f"{stream.lower()}@{_isoformat_z(window_start)}", {
            "count": 1,
            "sum": numeric_value,
            "min": numeric_value,
            "max": numeric_value,
            "first_event_at": _isoformat_z(parsed_timestamp),
            "last_event_at": _isoformat_z(parsed_timestamp),
        }
```

#### Reducer: `plugins_streaming_window.reduce_key`
- Source anchor: `plugins_streaming_window.py#L98-L123`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_streaming_window.py#L98-L123>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_streaming_window.py#L98-L123>

```python
def reduce_key(key, values):
    """Return window-level count, range, and rate metrics for one stream bucket."""
    stream, window_start = _split_window_key(key)
    merged = _merge_window_values(values)
    count = int(merged["count"])
    first_event_at = merged["first_event_at"]
    last_event_at = merged["last_event_at"]
    span_minutes = 0.0
    if first_event_at and last_event_at:
        span_minutes = round(
            (_parse_timestamp(last_event_at) - _parse_timestamp(first_event_at)).total_seconds() / 60,
            3,
        )
    return {
        "stream": stream,
        "window_start": window_start,
        "window_end": _isoformat_z(_parse_timestamp(window_start) + timedelta(minutes=WINDOW_MINUTES)),
        "count": count,
        "avg_value": round(float(merged["sum"]) / count, 3) if count else 0.0,
        "min_value": round(float(merged["min"]), 3) if count else 0.0,
        "max_value": round(float(merged["max"]), 3) if count else 0.0,
        "event_rate_per_minute": round(count / WINDOW_MINUTES, 3) if count else 0.0,
        "first_event_at": first_event_at,
        "last_event_at": last_event_at,
        "span_minutes": span_minutes,
    }
```

#### Combiner: `plugins_streaming_window.combine_values`
- Source anchor: `plugins_streaming_window.py#L93-L95`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_streaming_window.py#L93-L95>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_streaming_window.py#L93-L95>

```python
def combine_values(_key, values):
    """Merge shard-local window summaries before the final reduce step."""
    return _merge_window_values(values)
```

#### Benchmark generator: `plugins_streaming_window.benchmark_records`
- Source anchor: `plugins_streaming_window.py#L139-L212`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_streaming_window.py#L139-L212>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_streaming_window.py#L139-L212>

```python
def benchmark_records(scenario, records, seed, dataset_family="default"):
    """Generate deterministic windowed telemetry fixtures for benchmark scenarios."""
    if records <= 0:
        raise ValueError("records must be positive")
    rng = random.Random(seed)
    base_time = datetime(2026, 4, 17, 9, 0, tzinfo=timezone.utc)

    families = {
        "default": {
            "balanced": [
                {"stream": "sensor-alpha", "weight": 1.0, "window_offsets": [0, 5, 10, 15], "base_value": 21.5, "spread": 1.1, "drift": 0.3},
                {"stream": "sensor-beta", "weight": 1.0, "window_offsets": [0, 5, 10, 15], "base_value": 23.2, "spread": 1.0, "drift": 0.2},
                {"stream": "sensor-gamma", "weight": 1.0, "window_offsets": [0, 5, 10, 15], "base_value": 19.8, "spread": 1.2, "drift": 0.4},
                {"stream": "sensor-delta", "weight": 1.0, "window_offsets": [0, 5, 10, 15], "base_value": 24.0, "spread": 1.1, "drift": 0.2},
            ],
            "skewed": [
                {"stream": "sensor-alpha", "weight": 3.6, "window_offsets": [5, 5, 10], "base_value": 27.5, "spread": 1.4, "drift": 0.5, "hotspot_offsets": [5], "hotspot_bonus": 4.5},
                {"stream": "sensor-beta", "weight": 1.0, "window_offsets": [0, 10, 15], "base_value": 23.0, "spread": 1.1, "drift": 0.2},
                {"stream": "sensor-gamma", "weight": 0.9, "window_offsets": [0, 10, 15], "base_value": 20.1, "spread": 1.2, "drift": 0.3},
                {"stream": "sensor-delta", "weight": 0.8, "window_offsets": [5, 15], "base_value": 22.7, "spread": 1.0, "drift": 0.3},
            ],
        },
        "iot-burst": {
            "balanced": [
                {"stream": "turnstile-east", "weight": 1.1, "window_offsets": [5, 10, 15], "base_value": 31.0, "spread": 1.5, "drift": 0.6},
                {"stream": "camera-lobby", "weight": 1.0, "window_offsets": [5, 10, 15], "base_value": 28.5, "spread": 1.3, "drift": 0.4},
                {"stream": "hvac-north", "weight": 1.0, "window_offsets": [0, 10, 20], "base_value": 24.3, "spread": 1.0, "drift": 0.2},
                {"stream": "badge-reader", "weight": 0.9, "window_offsets": [0, 5, 15], "base_value": 26.0, "spread": 1.1, "drift": 0.3},
            ],
            "skewed": [
                {"stream": "turnstile-east", "weight": 4.2, "window_offsets": [10, 10, 15], "base_value": 36.0, "spread": 1.8, "drift": 0.8, "hotspot_offsets": [10], "hotspot_bonus": 14.0},
                {"stream": "camera-lobby", "weight": 1.5, "window_offsets": [15, 15, 20], "base_value": 30.5, "spread": 1.5, "drift": 0.5, "hotspot_offsets": [15], "hotspot_bonus": 6.5},
                {"stream": "hvac-north", "weight": 1.0, "window_offsets": [0, 10, 20], "base_value": 24.8, "spread": 1.0, "drift": 0.2},
                {"stream": "badge-reader", "weight": 0.8, "window_offsets": [5, 20], "base_value": 26.4, "spread": 1.1, "drift": 0.3},
            ],
        },
        "live-ops": {
            "balanced": [
                {"stream": "ingest-primary", "weight": 1.0, "window_offsets": [0, 5, 10, 15], "base_value": 42.0, "spread": 1.8, "drift": 0.7},
                {"stream": "chat-presence", "weight": 1.0, "window_offsets": [0, 5, 10, 15], "base_value": 38.0, "spread": 1.6, "drift": 0.5},
                {"stream": "moderation-queue", "weight": 1.0, "window_offsets": [0, 5, 10, 15], "base_value": 35.5, "spread": 1.4, "drift": 0.4},
                {"stream": "reaction-fanout", "weight": 1.0, "window_offsets": [0, 5, 10, 15], "base_value": 39.0, "spread": 1.7, "drift": 0.6},
            ],
            "skewed": [
                {"stream": "moderation-queue", "weight": 3.9, "window_offsets": [20, 20, 25], "base_value": 49.0, "spread": 2.1, "drift": 0.9, "hotspot_offsets": [20], "hotspot_bonus": 11.0},
                {"stream": "reaction-fanout", "weight": 1.6, "window_offsets": [15, 15, 20], "base_value": 43.0, "spread": 1.8, "drift": 0.7, "hotspot_offsets": [15], "hotspot_bonus": 5.5},
                {"stream": "ingest-primary", "weight": 1.0, "window_offsets": [0, 10, 20], "base_value": 41.5, "spread": 1.7, "drift": 0.5},
                {"stream": "chat-presence", "weight": 0.9, "window_offsets": [5, 10, 25], "base_value": 37.6, "spread": 1.4, "drift": 0.4},
            ],
        },
    }
    if dataset_family not in families or scenario not in families[dataset_family]:
        raise ValueError(f"unsupported plugin benchmark scenario/family: {scenario}/{dataset_family}")

    profiles = families[dataset_family][scenario]
    counts = _allocate_counts(records, [profile["weight"] for profile in profiles])
    lines = []
    for profile, count in zip(profiles, counts):
        lines.extend(
            _generate_stream_events(
                stream=profile["stream"],
                count=count,
                base_time=base_time,
                window_offsets=profile["window_offsets"],
                base_value=profile["base_value"],
                spread=profile["spread"],
                drift=profile["drift"],
                rng=rng,
                hotspot_offsets=profile.get("hotspot_offsets"),
                hotspot_bonus=profile.get("hotspot_bonus", 0.0),
            )
        )
    lines.sort(key=lambda line: line.split(",", maxsplit=2)[1])
    return lines[:records]
```

#### Benchmark note hook: `plugins_streaming_window.benchmark_notes`
- Source anchor: `plugins_streaming_window.py#L215-L284`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_streaming_window.py#L215-L284>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_streaming_window.py#L215-L284>

```python
def benchmark_notes(scenario, dataset_family="default"):
    """Describe the intended hot windows and portfolio story for each family."""
    notes = {
        ("balanced", "default"): [
            {
                "title": "Even telemetry cadence",
                "detail": "The default balanced family spreads sensor updates across multiple windows and streams, so reducer load should stay close while still demonstrating time-bucket aggregation.",
                "severity": "info",
                "takeaway": "Use this as the calm baseline before introducing a window hotspot that is caused by workload shape rather than partitioning noise.",
            },
        ],
        ("skewed", "default"): [
            {
                "title": "Sensor alpha window spike",
                "detail": "`sensor-alpha@2026-04-17T09:05:00Z` is intentionally overweighted, so the hottest reducer should look like one telemetry stream concentrating most of its work into a single five-minute bucket.",
                "severity": "watch",
                "hotspot_keys": ["sensor-alpha@2026-04-17T09:05:00Z"],
                "takeaway": "This is the simplest windowing story for explaining why time buckets can become hotspots even when the upstream stream names look balanced overall.",
            },
        ],
        ("balanced", "iot-burst"): [
            {
                "title": "Staggered building telemetry",
                "detail": "The balanced IoT family rotates turnstiles, cameras, HVAC, and badge readers across adjacent windows so the output reads like a healthy campus-building control loop.",
                "severity": "info",
                "takeaway": "Good for showing the plugin as a normal ops dashboard baseline before a rush-hour burst distorts one window.",
            },
        ],
        ("skewed", "iot-burst"): [
            {
                "title": "Turnstile rush-hour burst",
                "detail": "`turnstile-east@2026-04-17T09:10:00Z` dominates this family with both heavier volume and elevated values, so the hottest reducer should read like a lobby ingress spike during class changeover.",
                "severity": "risk",
                "hotspot_keys": ["turnstile-east@2026-04-17T09:10:00Z"],
                "takeaway": "This turns the plugin into a windowed-streaming case study about burst concentration, not just generic per-key aggregation.",
            },
            {
                "title": "Lobby camera spillover",
                "detail": "`camera-lobby@2026-04-17T09:15:00Z` forms a second-tier hotspot right behind the turnstile window, which helps the benchmark tell a fuller story about adjacent systems reacting to the same surge.",
                "severity": "watch",
                "hotspot_keys": ["camera-lobby@2026-04-17T09:15:00Z"],
                "takeaway": "Keep this note when you want the report to show cross-stream spillover instead of only the single biggest bucket.",
            },
        ],
        ("balanced", "live-ops"): [
            {
                "title": "Steady live-ops baseline",
                "detail": "The balanced live-ops family keeps ingest, presence, moderation, and fanout windows close enough that the report reads like a normal event stream instead of a launch incident.",
                "severity": "info",
                "takeaway": "Use this as the before state for the live moderation surge story.",
            },
        ],
        ("skewed", "live-ops"): [
            {
                "title": "Moderation queue pile-up",
                "detail": "`moderation-queue@2026-04-17T09:20:00Z` becomes the obvious hotspot here, so the window summary looks like one burst of chat events overwhelming moderation capacity during a live launch.",
                "severity": "risk",
                "hotspot_keys": ["moderation-queue@2026-04-17T09:20:00Z"],
                "takeaway": "This family is useful when you want a streaming-systems narrative about time-bucket pressure rather than user sessions or service latency.",
            },
            {
                "title": "Reaction fanout echo",
                "detail": "`reaction-fanout@2026-04-17T09:15:00Z` is the supporting hotspot behind moderation, which helps explain how bursty audience behavior can surface in multiple downstream windows.",
                "severity": "watch",
                "hotspot_keys": ["reaction-fanout@2026-04-17T09:15:00Z"],
                "takeaway": "Keep this annotation when you want the benchmark to tell a richer multi-stage streaming pipeline story.",
            },
        ],
    }
    return notes.get((scenario, dataset_family), [])
```

### <a id="plugin-max-score"></a>`plugin-max-score`

- Repository commit: `2332425c37ad2eb7d0399cb11e91a2354e189d22`
#### Mapper: `plugins_top_score.map_records`
- Source anchor: `plugins_top_score.py#L6-L13`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_top_score.py#L6-L13>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_top_score.py#L6-L13>

```python
def map_records(lines):
    """Parse comma-separated score rows into integer leaderboard updates."""
    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            continue
        name, score = stripped.split(",", maxsplit=1)
        yield name.strip().lower(), int(score.strip())
```

#### Reducer: `plugins_top_score.reduce_key`
- Source anchor: `plugins_top_score.py#L21-L23`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_top_score.py#L21-L23>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_top_score.py#L21-L23>

```python
def reduce_key(_key, values):
    """Return the overall maximum score for one student key."""
    return max(values)
```

#### Combiner: `plugins_top_score.combine_values`
- Source anchor: `plugins_top_score.py#L16-L18`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_top_score.py#L16-L18>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_top_score.py#L16-L18>

```python
def combine_values(_key, values):
    """Keep the shard-local maximum score for one student key."""
    return max(values)
```

### <a id="plugin-watermark-late-summary"></a>`plugin-watermark-late-summary`

- Repository commit: `2332425c37ad2eb7d0399cb11e91a2354e189d22`
#### Mapper: `plugins_watermark_late_summary.map_records`
- Source anchor: `plugins_watermark_late_summary.py#L136-L147`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L136-L147>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L136-L147>

```python
def map_records(lines):
    """Emit per-stream event batches from stream,event_time,arrival_time,value rows."""
    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            continue
        stream, event_at, arrived_at, value = [part.strip() for part in stripped.split(",", maxsplit=3)]
        yield stream.lower(), {
            "event_at": _isoformat_z(_parse_timestamp(event_at)),
            "arrived_at": _isoformat_z(_parse_timestamp(arrived_at)),
            "value": round(float(value), 3),
        }
```

#### Reducer: `plugins_watermark_late_summary.reduce_key`
- Source anchor: `plugins_watermark_late_summary.py#L155-L223`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L155-L223>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L155-L223>

```python
def reduce_key(key, values):
    """Summarize watermark-aware acceptance, late updates, and dropped events for one stream."""
    merged = _merge_event_batches(values)
    events = merged["events"]
    windows = {}
    max_seen_event_time = None
    first_arrival_at = None
    last_arrival_at = None
    max_watermark_gap_minutes = 0.0
    late_events_seen = 0

    for item in events:
        event_at = _parse_timestamp(item["event_at"])
        arrived_at = _parse_timestamp(item["arrived_at"])
        value = float(item["value"])
        if first_arrival_at is None or arrived_at < first_arrival_at:
            first_arrival_at = arrived_at
        if last_arrival_at is None or arrived_at > last_arrival_at:
            last_arrival_at = arrived_at

        watermark_before = _watermark_for(max_seen_event_time)
        window_start = _window_start(event_at)
        window_key = _isoformat_z(window_start)
        summary = windows.setdefault(window_key, _new_window_summary(window_start))
        window_close_at = _parse_timestamp(summary["window_close_at"])
        late = watermark_before is not None and event_at < watermark_before
        dropped = watermark_before is not None and watermark_before > window_close_at
        if late and watermark_before is not None:
            late_events_seen += 1
            max_watermark_gap_minutes = max(
                max_watermark_gap_minutes,
                round((watermark_before - event_at).total_seconds() / 60, 3),
            )

        _update_window_summary(summary, event_at=event_at, arrived_at=arrived_at, value=value, late=late, dropped=dropped)
        max_seen_event_time = event_at if max_seen_event_time is None else max(max_seen_event_time, event_at)

    finalized_windows = [_finalize_window_summary(windows[key]) for key in sorted(windows)]
    accepted_events = sum(item["accepted_events"] for item in finalized_windows)
    on_time_events = sum(item["on_time_events"] for item in finalized_windows)
    late_accepted_events = sum(item["late_accepted_events"] for item in finalized_windows)
    dropped_late_events = sum(item["dropped_late_events"] for item in finalized_windows)
    total_events_seen = sum(item["events_seen"] for item in finalized_windows)
    hottest_window = max(
        finalized_windows,
        key=lambda item: (item["late_accepted_events"] + item["dropped_late_events"], item["accepted_events"], item["window_start"]),
        default=None,
    )
    return {
        "stream": key,
        "window_count": len(finalized_windows),
        "total_events_seen": total_events_seen,
        "accepted_events": accepted_events,
        "on_time_events": on_time_events,
        "late_events_seen": late_events_seen,
        "late_accepted_events": late_accepted_events,
        "dropped_late_events": dropped_late_events,
        "late_acceptance_rate": round(late_accepted_events / accepted_events, 3) if accepted_events else 0.0,
        "drop_rate": round(dropped_late_events / total_events_seen, 3) if total_events_seen else 0.0,
        "first_arrival_at": _isoformat_z(first_arrival_at) if first_arrival_at else None,
        "last_arrival_at": _isoformat_z(last_arrival_at) if last_arrival_at else None,
        "final_watermark": _isoformat_z(_watermark_for(max_seen_event_time)) if max_seen_event_time else None,
        "max_watermark_gap_minutes": round(max_watermark_gap_minutes, 3),
        "hottest_window_start": hottest_window["window_start"] if hottest_window else None,
        "hottest_window_late_events": (
            hottest_window["late_accepted_events"] + hottest_window["dropped_late_events"]
        ) if hottest_window else 0,
        "windows": finalized_windows,
    }
```

#### Combiner: `plugins_watermark_late_summary.combine_values`
- Source anchor: `plugins_watermark_late_summary.py#L150-L152`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L150-L152>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L150-L152>

```python
def combine_values(_key, values):
    """Keep shard-local stream event batches JSON-safe before watermark evaluation."""
    return {"events": sorted(values, key=lambda event: (event["arrived_at"], event["event_at"], event["value"]))}
```

#### Benchmark generator: `plugins_watermark_late_summary.benchmark_records`
- Source anchor: `plugins_watermark_late_summary.py#L266-L341`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L266-L341>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L266-L341>

```python
def benchmark_records(scenario, records, seed, dataset_family="default"):
    """Generate deterministic out-of-order event streams for watermark-summary demos."""
    if records <= 0:
        raise ValueError("records must be positive")
    rng = random.Random(seed)
    base_time = datetime(2026, 4, 17, 9, 0, tzinfo=timezone.utc)

    families = {
        "default": {
            "balanced": [
                {"stream": "sensor-alpha", "weight": 1.0, "window_offsets": [0, 5, 10], "base_value": 20.5, "spread": 0.9, "drift": 0.2, "late_offsets": [5]},
                {"stream": "sensor-beta", "weight": 1.0, "window_offsets": [0, 10, 15], "base_value": 22.0, "spread": 1.0, "drift": 0.2, "late_offsets": [10]},
                {"stream": "sensor-gamma", "weight": 1.0, "window_offsets": [5, 10, 15], "base_value": 19.4, "spread": 0.8, "drift": 0.2, "late_offsets": [5]},
                {"stream": "sensor-delta", "weight": 1.0, "window_offsets": [0, 5, 15], "base_value": 21.2, "spread": 0.9, "drift": 0.1},
            ],
            "skewed": [
                {"stream": "sensor-alpha", "weight": 3.6, "window_offsets": [5, 10, 10], "base_value": 25.6, "spread": 1.2, "drift": 0.4, "late_offsets": [5, 10], "drop_offsets": [5], "hotspot_offsets": [10], "hotspot_bonus": 3.8},
                {"stream": "sensor-beta", "weight": 1.0, "window_offsets": [0, 10, 15], "base_value": 22.4, "spread": 0.9, "drift": 0.2, "late_offsets": [10]},
                {"stream": "sensor-gamma", "weight": 0.9, "window_offsets": [0, 5, 15], "base_value": 19.8, "spread": 0.8, "drift": 0.1},
                {"stream": "sensor-delta", "weight": 0.8, "window_offsets": [5, 15, 20], "base_value": 21.1, "spread": 0.9, "drift": 0.2},
            ],
        },
        "sensor-backfill": {
            "balanced": [
                {"stream": "meter-east", "weight": 1.1, "window_offsets": [0, 5, 10], "base_value": 34.5, "spread": 1.1, "drift": 0.3, "late_offsets": [5]},
                {"stream": "meter-west", "weight": 1.0, "window_offsets": [0, 10, 15], "base_value": 33.8, "spread": 1.0, "drift": 0.2, "late_offsets": [10]},
                {"stream": "pipeline-north", "weight": 1.0, "window_offsets": [5, 10, 20], "base_value": 31.2, "spread": 1.0, "drift": 0.2, "late_offsets": [5]},
                {"stream": "pipeline-south", "weight": 0.9, "window_offsets": [0, 15, 20], "base_value": 32.1, "spread": 0.9, "drift": 0.2},
            ],
            "skewed": [
                {"stream": "meter-east", "weight": 4.0, "window_offsets": [5, 10, 15], "base_value": 39.2, "spread": 1.4, "drift": 0.5, "late_offsets": [5, 10], "drop_offsets": [5, 10], "hotspot_offsets": [10], "hotspot_bonus": 6.2},
                {"stream": "meter-west", "weight": 1.2, "window_offsets": [0, 10, 20], "base_value": 35.1, "spread": 1.1, "drift": 0.2, "late_offsets": [10]},
                {"stream": "pipeline-north", "weight": 1.0, "window_offsets": [5, 15, 20], "base_value": 31.6, "spread": 1.0, "drift": 0.2},
                {"stream": "pipeline-south", "weight": 0.8, "window_offsets": [0, 15, 25], "base_value": 32.4, "spread": 0.9, "drift": 0.2},
            ],
        },
        "live-replay": {
            "balanced": [
                {"stream": "chat-ingest", "weight": 1.0, "window_offsets": [0, 5, 10], "base_value": 44.0, "spread": 1.2, "drift": 0.3, "late_offsets": [5]},
                {"stream": "reaction-fanout", "weight": 1.0, "window_offsets": [0, 10, 15], "base_value": 41.5, "spread": 1.1, "drift": 0.3, "late_offsets": [10]},
                {"stream": "presence-sync", "weight": 1.0, "window_offsets": [5, 10, 20], "base_value": 37.2, "spread": 1.0, "drift": 0.2},
                {"stream": "moderation-queue", "weight": 1.0, "window_offsets": [0, 15, 20], "base_value": 40.1, "spread": 1.1, "drift": 0.3, "late_offsets": [15]},
            ],
            "skewed": [
                {"stream": "moderation-queue", "weight": 3.9, "window_offsets": [15, 20, 20], "base_value": 50.3, "spread": 1.6, "drift": 0.6, "late_offsets": [15, 20], "drop_offsets": [15], "hotspot_offsets": [20], "hotspot_bonus": 7.1},
                {"stream": "reaction-fanout", "weight": 1.5, "window_offsets": [10, 15, 20], "base_value": 43.4, "spread": 1.2, "drift": 0.3, "late_offsets": [15]},
                {"stream": "chat-ingest", "weight": 1.0, "window_offsets": [0, 10, 25], "base_value": 44.2, "spread": 1.1, "drift": 0.2},
                {"stream": "presence-sync", "weight": 0.9, "window_offsets": [5, 15, 25], "base_value": 37.8, "spread": 1.0, "drift": 0.2},
            ],
        },
    }
    if dataset_family not in families or scenario not in families[dataset_family]:
        raise ValueError(f"unsupported plugin benchmark scenario/family: {scenario}/{dataset_family}")

    profiles = families[dataset_family][scenario]
    counts = _allocate_counts(records, [profile["weight"] for profile in profiles])
    lines = []
    for profile, count in zip(profiles, counts):
        lines.extend(
            _generate_stream_events(
                stream=profile["stream"],
                count=count,
                base_time=base_time,
                window_offsets=profile["window_offsets"],
                base_value=profile["base_value"],
                spread=profile["spread"],
                drift=profile["drift"],
                rng=rng,
                late_window_offsets=profile.get("late_offsets"),
                drop_window_offsets=profile.get("drop_offsets"),
                hotspot_window_offsets=profile.get("hotspot_offsets"),
                hotspot_bonus=profile.get("hotspot_bonus", 0.0),
            )
        )
    lines.sort(key=lambda line: tuple(line.split(",", maxsplit=3)[1:3]))
    return lines[:records]
```

#### Benchmark note hook: `plugins_watermark_late_summary.benchmark_notes`
- Source anchor: `plugins_watermark_late_summary.py#L344-L413`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L344-L413>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L344-L413>

```python
def benchmark_notes(scenario, dataset_family="default"):
    """Describe the intended late-event hotspot story for each synthetic family."""
    notes = {
        ("balanced", "default"): [
            {
                "title": "Mostly on-time telemetry baseline",
                "detail": "The default balanced family keeps late updates mild and spread across four streams, so the report should read like a healthy watermark configuration rather than an incident.",
                "severity": "info",
                "takeaway": "Use this as the before state for explaining why a single stream with repeated backfills changes both lateness and drop rates.",
            },
        ],
        ("skewed", "default"): [
            {
                "title": "Sensor alpha late-event hotspot",
                "detail": "`sensor-alpha` is intentionally overloaded with backfilled windows, so the hottest reducer should show one stream dominating both late-accepted updates and dropped events.",
                "severity": "watch",
                "hotspot_keys": ["sensor-alpha"],
                "takeaway": "This is the simplest portfolio story for explaining event time, watermarks, and allowed lateness without needing a full streaming framework.",
            },
        ],
        ("balanced", "sensor-backfill"): [
            {
                "title": "Routine meter replays",
                "detail": "The balanced sensor-backfill family makes every stream tolerate a few delayed packets, so the output reads like normal AMI backfill handling instead of a broken ingest pipeline.",
                "severity": "info",
                "takeaway": "Good for showing how watermark-aware summaries stay useful even when the late path is healthy and controlled.",
            },
        ],
        ("skewed", "sensor-backfill"): [
            {
                "title": "Meter east replay storm",
                "detail": "`meter-east` dominates this family with both accepted and dropped backfills, so the report should look like a utility stream replaying stale packets after a connectivity gap.",
                "severity": "risk",
                "hotspot_keys": ["meter-east"],
                "takeaway": "Call out how the drop rate only climbs after the watermark passes the allowed-lateness boundary for the same windows.",
            },
            {
                "title": "Meter west secondary lag",
                "detail": "`meter-west` forms a smaller second-tier late stream behind meter-east, which helps the benchmark tell a richer story about regional spillover instead of a single broken key.",
                "severity": "watch",
                "hotspot_keys": ["meter-west"],
                "takeaway": "Keep this note when you want a fuller data-engineering narrative instead of focusing only on the worst offender.",
            },
        ],
        ("balanced", "live-replay"): [
            {
                "title": "Steady live-ops baseline",
                "detail": "The balanced live-replay family keeps ingest, reactions, presence, and moderation close enough that the report reads like a normal stream-processing pipeline with occasional harmless replays.",
                "severity": "info",
                "takeaway": "Use this as the calm baseline before showing how moderation replays create visible watermark pressure.",
            },
        ],
        ("skewed", "live-replay"): [
            {
                "title": "Moderation replay pile-up",
                "detail": "`moderation-queue` becomes the obvious hotspot here with repeated stale replays, so the watermark summary looks like one downstream queue absorbing late chat events during a live launch.",
                "severity": "risk",
                "hotspot_keys": ["moderation-queue"],
                "takeaway": "This turns the plugin into a streaming-systems case study about out-of-order handling instead of only fixed windows or batch reducers.",
            },
            {
                "title": "Reaction fanout echo",
                "detail": "`reaction-fanout` is the supporting late stream behind moderation, which helps explain how one replay wave can surface in multiple downstream consumers.",
                "severity": "watch",
                "hotspot_keys": ["reaction-fanout"],
                "takeaway": "Keep this annotation when you want the report to highlight pipeline-wide replay propagation.",
            },
        ],
    }
    return notes.get((scenario, dataset_family), [])
```


## Adjacent diffs

### Diff 1: `projects/mini-mapreduce-lab/plugins_average_score.py` → `projects/mini-mapreduce-lab/plugins_rolling_window_join.py`
- Changed fields: `available_dataset_families, benchmark_generator, benchmark_generator_doc_summary, benchmark_generator_source_anchor, benchmark_generator_source_commit_url, benchmark_generator_source_excerpt, benchmark_generator_source_line, benchmark_generator_source_url, benchmark_note_hook, benchmark_note_hook_doc_summary, benchmark_note_hook_source_anchor, benchmark_note_hook_source_commit_url, benchmark_note_hook_source_excerpt, benchmark_note_hook_source_line, benchmark_note_hook_source_url, combiner, combiner_doc_summary, combiner_source_anchor, combiner_source_commit_url, combiner_source_excerpt, combiner_source_line, combiner_source_url, mapper, mapper_doc_summary, mapper_source_anchor, mapper_source_commit_url, mapper_source_excerpt, mapper_source_line, mapper_source_url, module_doc_summary, name, plugin, reducer, reducer_doc_summary, reducer_signature, reducer_source_anchor, reducer_source_commit_url, reducer_source_excerpt, reducer_source_line, reducer_source_url`

| Field | Previous | Current |
| --- | --- | --- |
| `available_dataset_families` | `["default", "exam-cram", "project-week"]` | `["default", "checkout-funnel", "incident-correlation"]` |
| `benchmark_generator` | `"plugins_average_score.benchmark_records"` | `"plugins_rolling_window_join.benchmark_records"` |
| `benchmark_generator_doc_summary` | `"Generate deterministic cohort score fixtures for benchmark scenarios."` | `"Generate deterministic two-stream correlation fixtures for rolling join demos."` |
| `benchmark_generator_source_anchor` | `"plugins_average_score.py#L30-L60"` | `"plugins_rolling_window_join.py#L273-L348"` |
| `benchmark_generator_source_commit_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_average_score.py#L30-L60"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L273-L348"` |
| `benchmark_generator_source_excerpt` | `"def benchmark_records(scenario, records, seed, dataset_family=\"default\"):\n    \"\"\"Generate deterministic cohort score fixtures for benchmark scenarios.\"\"\"\n    import random\n\n    if records <= 0:\n        raise ValueError(\"records must be positive\")\n    rng = random.Random(seed)\n\n    if dataset_family == \"default\":\n        if scenario == \"balanced\":\n            students = [f\"team-{index:02d}\" for index in range(12)]\n            return [f\"{students[index % len(students)]},{72 + ((index * 9) % 19)}\" for index in range(records)]\n        if scenario == \"skewed\":\n            hot_students = [\"capstone-core\"] * 16 + [f\"rotation-{index}\" for index in range(4)] + [f\"elective-{index}\" for index in range(10)]\n            return [f\"{rng.choice(hot_students)},{65 + rng.randint(0, 30)}\" for _ in range(records)]\n    elif dataset_family == \"exam-cram\":\n        if scenario == \"balanced\":\n            cohorts = [f\"study-group-{index:02d}\" for index in range(10)]\n            return [f\"{cohorts[index % len(cohorts)]},{78 + ((index * 7) % 15)}\" for index in range(records)]\n        if scenario == \"skewed\":\n            hot_students = [\"midterm-sprint\"] * 18 + [f\"review-{index}\" for index in range(4)] + [f\"prep-{index}\" for index in range(12)]\n            return [f\"{rng.choice(hot_students)},{70 + rng.randint(0, 25)}\" for _ in range(records)]\n    elif dataset_family == \"project-week\":\n        if scenario == \"balanced\":\n            squads = [f\"studio-{index:02d}\" for index in range(8)]\n            return [f\"{squads[index % len(squads)]},{74 + ((index * 5) % 21)}\" for index in range(records)]\n        if scenario == \"skewed\":\n            hot_students = [\"demo-day-core\"] * 12 + [f\"integration-{index}\" for index in range(6)] + [f\"feature-{index}\" for index in range(14)]\n            return [f\"{rng.choice(hot_students)},{68 + rng.randint(0, 28)}\" for _ in range(records)]\n\n    raise ValueError(f\"unsupported plugin benchmark scenario/family: {scenario}/{dataset_family}\")"` | `"def benchmark_records(scenario, records, seed, dataset_family=\"default\"):\n    \"\"\"Generate deterministic two-stream correlation fixtures for rolling join demos.\"\"\"\n    if records <= 0:\n        raise ValueError(\"records must be positive\")\n    rng = random.Random(seed)\n    base_time = datetime(2026, 4, 17, 9, 0, tzinfo=timezone.utc)\n\n    families = {\n        \"default\": {\n            \"balanced\": [\n                {\"key\": \"join-pod-alpha\", \"weight\": 1.0, \"window_offsets\": [0, 5, 10], \"left_label\": \"request-start\", \"right_label\": \"request-finish\", \"match_ratio\": 0.86, \"right_lag_seconds\": 52},\n                {\"key\": \"join-pod-beta\", \"weight\": 1.0, \"window_offsets\": [0, 5, 10], \"left_label\": \"request-start\", \"right_label\": \"request-finish\", \"match_ratio\": 0.84, \"right_lag_seconds\": 61},\n                {\"key\": \"join-pod-gamma\", \"weight\": 1.0, \"window_offsets\": [5, 10, 15], \"left_label\": \"request-start\", \"right_label\": \"request-finish\", \"match_ratio\": 0.83, \"right_lag_seconds\": 57},\n                {\"key\": \"join-pod-delta\", \"weight\": 1.0, \"window_offsets\": [0, 10, 15], \"left_label\": \"request-start\", \"right_label\": \"request-finish\", \"match_ratio\": 0.82, \"right_lag_seconds\": 68},\n            ],\n            \"skewed\": [\n                {\"key\": \"join-hotspot\", \"weight\": 4.0, \"window_offsets\": [10, 10, 15], \"left_label\": \"request-start\", \"right_label\": \"request-finish\", \"match_ratio\": 0.72, \"right_lag_seconds\": 97, \"hotspot_offsets\": [10], \"hotspot_bonus\": 40, \"left_only_share\": 0.7},\n                {\"key\": \"join-pod-beta\", \"weight\": 1.1, \"window_offsets\": [0, 10, 15], \"left_label\": \"request-start\", \"right_label\": \"request-finish\", \"match_ratio\": 0.82, \"right_lag_seconds\": 64},\n                {\"key\": \"join-pod-gamma\", \"weight\": 1.0, \"window_offsets\": [5, 15, 20], \"left_label\": \"request-start\", \"right_label\": \"request-finish\", \"match_ratio\": 0.8, \"right_lag_seconds\": 70},\n                {\"key\": \"join-pod-delta\", \"weight\": 0.9, \"window_offsets\": [0, 15, 20], \"left_label\": \"request-start\", \"right_label\": \"request-finish\", \"match_ratio\": 0.78, \"right_lag_seconds\": 75},\n            ],\n        },\n        \"checkout-funnel\": {\n            \"balanced\": [\n                {\"key\": \"checkout-core\", \"weight\": 1.2, \"window_offsets\": [5, 10, 15], \"left_label\": \"cart-update\", \"right_label\": \"payment-auth\", \"match_ratio\": 0.88, \"right_lag_seconds\": 48},\n                {\"key\": \"express-lane\", \"weight\": 1.0, \"window_offsets\": [5, 10, 15], \"left_label\": \"cart-update\", \"right_label\": \"payment-auth\", \"match_ratio\": 0.9, \"right_lag_seconds\": 38},\n                {\"key\": \"promo-retry\", \"weight\": 1.0, \"window_offsets\": [0, 10, 20], \"left_label\": \"cart-update\", \"right_label\": \"payment-auth\", \"match_ratio\": 0.8, \"right_lag_seconds\": 66},\n                {\"key\": \"inventory-sync\", \"weight\": 0.9, \"window_offsets\": [0, 5, 15], \"left_label\": \"cart-update\", \"right_label\": \"payment-auth\", \"match_ratio\": 0.84, \"right_lag_seconds\": 58},\n            ],\n            \"skewed\": [\n                {\"key\": \"checkout-core\", \"weight\": 4.3, \"window_offsets\": [10, 10, 15], \"left_label\": \"cart-update\", \"right_label\": \"payment-auth\", \"match_ratio\": 0.7, \"right_lag_seconds\": 102, \"hotspot_offsets\": [10], \"hotspot_bonus\": 55, \"left_only_share\": 0.75},\n                {\"key\": \"promo-retry\", \"weight\": 1.5, \"window_offsets\": [10, 15, 20], \"left_label\": \"cart-update\", \"right_label\": \"payment-auth\", \"match_ratio\": 0.76, \"right_lag_seconds\": 88, \"hotspot_offsets\": [15], \"hotspot_bonus\": 32, \"left_only_share\": 0.65},\n                {\"key\": \"express-lane\", \"weight\": 1.0, \"window_offsets\": [5, 15, 20], \"left_label\": \"cart-update\", \"right_label\": \"payment-auth\", \"match_ratio\": 0.86, \"right_lag_seconds\": 42},\n                {\"key\": \"inventory-sync\", \"weight\": 0.8, \"window_offsets\": [0, 10, 20], \"left_label\": \"cart-update\", \"right_label\": \"payment-auth\", \"match_ratio\": 0.8, \"right_lag_seconds\": 63},\n            ],\n        },\n        \"incident-correlation\": {\n            \"balanced\": [\n                {\"key\": \"payments-api\", \"weight\": 1.1, \"window_offsets\": [0, 5, 10], \"left_label\": \"alert-fired\", \"right_label\": \"deploy-event\", \"match_ratio\": 0.83, \"right_lag_seconds\": 74},\n                {\"key\": \"auth-gateway\", \"weight\": 1.0, \"window_offsets\": [0, 10, 15], \"left_label\": \"alert-fired\", \"right_label\": \"deploy-event\", \"match_ratio\": 0.82, \"right_lag_seconds\": 81},\n                {\"key\": \"search-api\", \"weight\": 1.0, \"window_offsets\": [5, 10, 20], \"left_label\": \"alert-fired\", \"right_label\": \"deploy-event\", \"match_ratio\": 0.84, \"right_lag_seconds\": 72},\n                {\"key\": \"edge-cache\", \"weight\": 0.9, \"window_offsets\": [0, 15, 20], \"left_label\": \"alert-fired\", \"right_label\": \"deploy-event\", \"match_ratio\": 0.8, \"right_lag_seconds\": 90},\n            ],\n            \"skewed\": [\n                {\"key\": \"payments-api\", \"weight\": 4.1, \"window_offsets\": [15, 20, 20], \"left_label\": \"alert-fired\", \"right_label\": \"deploy-event\", \"match_ratio\": 0.68, \"right_lag_seconds\": 118, \"hotspot_offsets\": [20], \"hotspot_bonus\": 48, \"left_only_share\": 0.72},\n                {\"key\": \"auth-gateway\", \"weight\": 1.4, \"window_offsets\": [10, 15, 20], \"left_label\": \"alert-fired\", \"right_label\": \"deploy-event\", \"match_ratio\": 0.74, \"right_lag_seconds\": 96, \"hotspot_offsets\": [15], \"hotspot_bonus\": 26, \"left_only_share\": 0.62},\n                {\"key\": \"search-api\", \"weight\": 1.0, \"window_offsets\": [5, 15, 25], \"left_label\": \"alert-fired\", \"right_label\": \"deploy-event\", \"match_ratio\": 0.82, \"right_lag_seconds\": 77},\n                {\"key\": \"edge-cache\", \"weight\": 0.8, \"window_offsets\": [0, 10, 25], \"left_label\": \"alert-fired\", \"right_label\": \"deploy-event\", \"match_ratio\": 0.78, \"right_lag_seconds\": 88},\n            ],\n        },\n    }\n    if dataset_family not in families or scenario not in families[dataset_family]:\n        raise ValueError(f\"unsupported plugin benchmark scenario/family: {scenario}/{dataset_family}\")\n\n    profiles = families[dataset_family][scenario]\n    counts = _allocate_counts(records, [profile[\"weight\"] for profile in profiles])\n    lines = []\n    for profile, count in zip(profiles, counts):\n        lines.extend(\n            _generate_join_events(\n                key=profile[\"key\"],\n                count=count,\n                base_time=base_time,\n                window_offsets=profile[\"window_offsets\"],\n                left_label=profile[\"left_label\"],\n                right_label=profile[\"right_label\"],\n                rng=rng,\n                match_ratio=profile[\"match_ratio\"],\n                right_lag_seconds=profile[\"right_lag_seconds\"],\n                hotspot_offsets=profile.get(\"hotspot_offsets\"),\n                hotspot_bonus=profile.get(\"hotspot_bonus\", 0),\n                left_only_share=profile.get(\"left_only_share\", 0.5),\n            )\n        )\n    lines.sort(key=lambda line: tuple(line.split(\",\", maxsplit=3)[:3]))\n    return lines[:records]"` |
| `benchmark_generator_source_line` | `30` | `273` |
| `benchmark_generator_source_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L30-L60"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L273-L348"` |
| `benchmark_note_hook` | `"plugins_average_score.benchmark_notes"` | `"plugins_rolling_window_join.benchmark_notes"` |
| `benchmark_note_hook_doc_summary` | `"Describe the intended hot keys for each synthetic benchmark family."` | `"Describe the intended join hotspot and portfolio story for each synthetic family."` |
| `benchmark_note_hook_source_anchor` | `"plugins_average_score.py#L63-L132"` | `"plugins_rolling_window_join.py#L351-L420"` |
| `benchmark_note_hook_source_commit_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_average_score.py#L63-L132"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L351-L420"` |
| `benchmark_note_hook_source_excerpt` | `"def benchmark_notes(scenario, dataset_family=\"default\"):\n    \"\"\"Describe the intended hot keys for each synthetic benchmark family.\"\"\"\n    notes = {\n        (\"balanced\", \"default\"): [\n            {\n                \"title\": \"Even cohort rotation\",\n                \"detail\": \"The default balanced cohort rotates evenly across team labels, so average-score aggregation stays spread out and mostly tests framework overhead rather than hot students.\",\n                \"severity\": \"info\",\n                \"takeaway\": \"Treat any noticeable reducer imbalance here as partition spread, not as a workload-shaped hotspot.\",\n            },\n        ],\n        (\"skewed\", \"default\"): [\n            {\n                \"title\": \"Capstone leader hotspot\",\n                \"detail\": \"`capstone-core` is the dominant student key here, so the hottest reducer should look like one heavy project lead soaking up repeated score updates.\",\n                \"severity\": \"watch\",\n                \"hotspot_keys\": [\"capstone-core\"],\n                \"takeaway\": \"Use this scenario to explain how a single standout key can dominate reducer traffic even when the final averages remain correct.\",\n            },\n        ],\n        (\"balanced\", \"exam-cram\"): [\n            {\n                \"title\": \"Distributed study groups\",\n                \"detail\": \"Balanced exam-cram fixtures distribute scores across study groups, which makes them a clean baseline before simulating deadline pressure.\",\n                \"severity\": \"info\",\n                \"takeaway\": \"This is the calm comparison point for the cram-week hotspot run.\",\n            },\n        ],\n        (\"skewed\", \"exam-cram\"): [\n            {\n                \"title\": \"Cram-week surge\",\n                \"detail\": \"`midterm-sprint` is intentionally overrepresented, so the report should surface one study cohort as the obvious hotspot during cram-week traffic.\",\n                \"severity\": \"watch\",\n                \"hotspot_keys\": [\"midterm-sprint\"],\n                \"takeaway\": \"The skew should read like deadline-driven traffic, not like a partitioner bug.\",\n            },\n        ],\n        (\"balanced\", \"project-week\"): [\n            {\n                \"title\": \"Studio squad baseline\",\n                \"detail\": \"Balanced project-week fixtures rotate across studio squads so reducer load stays close even though the labels feel more portfolio-realistic than generic teams.\",\n                \"severity\": \"info\",\n                \"takeaway\": \"This family keeps the story portfolio-friendly without manufacturing a hotspot.\",\n            },\n        ],\n        (\"skewed\", \"project-week\"): [\n            {\n                \"title\": \"Demo-day crunch hotspot\",\n                \"detail\": \"`demo-day-core` is the main hotspot here, with integration and feature tails behind it, so you can narrate the skew as a deadline-driven project crunch.\",\n                \"severity\": \"risk\",\n                \"hotspot_keys\": [\"demo-day-core\", \"integration-0\", \"feature-0\"],\n                \"takeaway\": \"This slice is meant to read like a real project-week bottleneck where one squad absorbs the final demo push.\",\n            },\n            {\n                \"title\": \"Integration review backlog\",\n                \"detail\": \"The `integration-*` keys form a second-tier hotspot behind the demo-day core, which makes a good reviewer note when you want to talk about handoff queues instead of only the primary spike.\",\n                \"severity\": \"watch\",\n                \"hotspot_keys\": [\"integration-0\", \"integration-1\", \"integration-2\"],\n                \"takeaway\": \"Keep this card when you want a fuller systems story about follow-on bottlenecks after the main project crunch.\",\n            },\n            {\n                \"title\": \"Feature-lane tail\",\n                \"detail\": \"The `feature-*` keys stay spread out and comparatively cooler, so they are useful as a low-priority reviewer note but often safe to collapse in tighter portfolio reports.\",\n                \"severity\": \"info\",\n                \"hotspot_keys\": [\"feature-0\", \"feature-1\"],\n                \"takeaway\": \"Use annotation filters or overflow summaries when you want to hide softer follow-up notes and keep the report focused on the highest-risk queues.\",\n            },\n        ],\n    }\n    return notes.get((scenario, dataset_family), [])"` | `"def benchmark_notes(scenario, dataset_family=\"default\"):\n    \"\"\"Describe the intended join hotspot and portfolio story for each synthetic family.\"\"\"\n    notes = {\n        (\"balanced\", \"default\"): [\n            {\n                \"title\": \"Steady correlation baseline\",\n                \"detail\": \"The default balanced family keeps four correlation keys close together with only mild spillover, so the report reads like a healthy request/response join workload instead of an incident.\",\n                \"severity\": \"info\",\n                \"takeaway\": \"Use this as the before state when explaining how one correlation key can dominate a rolling join workload even if the reducer partitioner stays deterministic.\",\n            },\n        ],\n        (\"skewed\", \"default\"): [\n            {\n                \"title\": \"Join hotspot concentration\",\n                \"detail\": \"`join-hotspot` absorbs most of the left/right traffic here, so the hottest reducer should read like one correlation key monopolizing the join stage and leaving extra unmatched left events behind.\",\n                \"severity\": \"watch\",\n                \"hotspot_keys\": [\"join-hotspot\"],\n                \"takeaway\": \"This is the simplest story for showing why stream joins introduce both hotspot pressure and mismatch cleanup work.\",\n            },\n        ],\n        (\"balanced\", \"checkout-funnel\"): [\n            {\n                \"title\": \"Healthy checkout handoff\",\n                \"detail\": \"The balanced checkout family keeps `cart-update` and `payment-auth` events closely paired across several flows, so the join output reads like a normal purchase funnel rather than a broken queue.\",\n                \"severity\": \"info\",\n                \"takeaway\": \"Good for presenting the plugin as a product/commerce analytics example instead of only infra telemetry.\",\n            },\n        ],\n        (\"skewed\", \"checkout-funnel\"): [\n            {\n                \"title\": \"Checkout core backlog\",\n                \"detail\": \"`checkout-core` becomes the dominant join key with the worst pairing lag, so the report looks like a spike of cart updates outrunning payment authorizations during a launch or sale.\",\n                \"severity\": \"risk\",\n                \"hotspot_keys\": [\"checkout-core\"],\n                \"takeaway\": \"Call out the combination of lower coverage and higher gap when telling the story of queue lag or degraded downstream auth capacity.\",\n            },\n            {\n                \"title\": \"Promo retry spillover\",\n                \"detail\": \"`promo-retry` is the second-tier correlation hotspot behind checkout-core, which helps explain how retries can spread join pressure to a supporting flow instead of one isolated key.\",\n                \"severity\": \"watch\",\n                \"hotspot_keys\": [\"promo-retry\"],\n                \"takeaway\": \"Keep this note when you want the benchmark to feel like a fuller checkout system instead of one synthetic broken key.\",\n            },\n        ],\n        (\"balanced\", \"incident-correlation\"): [\n            {\n                \"title\": \"Routine alert/deploy audit trail\",\n                \"detail\": \"The balanced incident-correlation family keeps alerts and deploy events close enough that the join output reads like a calm incident-review dashboard instead of a chaotic release.\",\n                \"severity\": \"info\",\n                \"takeaway\": \"Use this as the steady baseline before a noisy release or rollback starts separating alerts from the deploys that explain them.\",\n            },\n        ],\n        (\"skewed\", \"incident-correlation\"): [\n            {\n                \"title\": \"Payments incident war room\",\n                \"detail\": \"`payments-api` dominates the skewed incident family with long join gaps and extra unmatched alerts, so the benchmark looks like a release that triggered alarms faster than deploy metadata propagated.\",\n                \"severity\": \"risk\",\n                \"hotspot_keys\": [\"payments-api\"],\n                \"takeaway\": \"This turns the plugin into a systems-debugging narrative about correlating alerts, deploys, and lagging metadata streams.\",\n            },\n            {\n                \"title\": \"Auth gateway follow-on noise\",\n                \"detail\": \"`auth-gateway` forms a smaller supporting hotspot that helps the report tell a more realistic multi-service release story instead of one isolated outage key.\",\n                \"severity\": \"watch\",\n                \"hotspot_keys\": [\"auth-gateway\"],\n                \"takeaway\": \"Keep this note when you want to explain correlated release fallout across adjacent services.\",\n            },\n        ],\n    }\n    return notes.get((scenario, dataset_family), [])"` |
| `benchmark_note_hook_source_line` | `63` | `351` |
| `benchmark_note_hook_source_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L63-L132"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L351-L420"` |
| `combiner` | `"plugins_average_score.combine_values"` | `"plugins_rolling_window_join.combine_values"` |
| `combiner_doc_summary` | `"Merge shard-local sum/count objects before the final reduce step."` | `"Keep shard-local join candidates JSON-safe before final pairing."` |
| `combiner_source_anchor` | `"plugins_average_score.py#L16-L20"` | `"plugins_rolling_window_join.py#L199-L201"` |
| `combiner_source_commit_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_average_score.py#L16-L20"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L199-L201"` |
| `combiner_source_excerpt` | `"def combine_values(_key, values):\n    \"\"\"Merge shard-local sum/count objects before the final reduce step.\"\"\"\n    total = sum(item[\"sum\"] for item in values)\n    count = sum(item[\"count\"] for item in values)\n    return {\"sum\": total, \"count\": count}"` | `"def combine_values(_key, values):\n    \"\"\"Keep shard-local join candidates JSON-safe before final pairing.\"\"\"\n    return {\"events\": sorted(values, key=lambda event: (event[\"event_at\"], event[\"side\"], event[\"label\"]))}"` |
| `combiner_source_line` | `16` | `199` |
| `combiner_source_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L16-L20"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L199-L201"` |
| `mapper` | `"plugins_average_score.map_records"` | `"plugins_rolling_window_join.map_records"` |
| `mapper_doc_summary` | `"Emit per-student sum/count records from comma-separated score lines."` | `"Emit per-correlation-key event batches from key,side,timestamp,label rows."` |
| `mapper_source_anchor` | `"plugins_average_score.py#L7-L13"` | `"plugins_rolling_window_join.py#L182-L196"` |
| `mapper_source_commit_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_average_score.py#L7-L13"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L182-L196"` |
| `mapper_source_excerpt` | `"def map_records(lines):\n    \"\"\"Emit per-student sum/count records from comma-separated score lines.\"\"\"\n    for line in lines:\n        if not line.strip():\n            continue\n        name, score = line.split(\",\", 1)\n        yield name.strip().lower(), {\"sum\": float(score), \"count\": 1}"` | `"def map_records(lines):\n    \"\"\"Emit per-correlation-key event batches from key,side,timestamp,label rows.\"\"\"\n    for raw in lines:\n        stripped = raw.strip()\n        if not stripped:\n            continue\n        key, side, event_at, label = [part.strip() for part in stripped.split(\",\", maxsplit=3)]\n        normalized_side = side.lower()\n        if normalized_side not in {\"left\", \"right\"}:\n            raise ValueError(\"rolling-window-join side must be 'left' or 'right'\")\n        yield key.lower(), {\n            \"side\": normalized_side,\n            \"event_at\": _isoformat_z(_parse_timestamp(event_at)),\n            \"label\": label,\n        }"` |
| `mapper_source_line` | `7` | `182` |
| `mapper_source_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L7-L13"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L182-L196"` |
| `module_doc_summary` | `"Average-score analytics plugin with synthetic cohort benchmark families."` | `"Rolling-window join plugin for multi-stream correlation and pipeline-debug demos."` |
| `name` | `"plugin-average-score"` | `"plugin-rolling-window-join"` |
| `plugin` | `"projects/mini-mapreduce-lab/plugins_average_score.py"` | `"projects/mini-mapreduce-lab/plugins_rolling_window_join.py"` |
| `reducer` | `"plugins_average_score.reduce_key"` | `"plugins_rolling_window_join.reduce_key"` |
| `reducer_doc_summary` | `"Return a rounded average score for one student key."` | `"Pair left/right events within a rolling join window and summarize unmatched spillover."` |
| `reducer_signature` | `"reduce_key(_key, values)"` | `"reduce_key(key, values)"` |
| `reducer_source_anchor` | `"plugins_average_score.py#L23-L27"` | `"plugins_rolling_window_join.py#L204-L270"` |
| `reducer_source_commit_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_average_score.py#L23-L27"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L204-L270"` |
| `reducer_source_excerpt` | `"def reduce_key(_key, values):\n    \"\"\"Return a rounded average score for one student key.\"\"\"\n    total = sum(item[\"sum\"] for item in values)\n    count = sum(item[\"count\"] for item in values)\n    return round(total / count, 3) if count else 0.0"` | `"def reduce_key(key, values):\n    \"\"\"Pair left/right events within a rolling join window and summarize unmatched spillover.\"\"\"\n    merged = _merge_event_batches(values)\n    events = merged[\"events\"]\n    left_events = [event for event in events if event[\"side\"] == \"left\"]\n    right_events = [event for event in events if event[\"side\"] == \"right\"]\n    used_right = set()\n    windows = {}\n    gap_seconds_values = []\n\n    for left_event in left_events:\n        left_time = _parse_timestamp(left_event[\"event_at\"])\n        best_index = None\n        best_gap = None\n        for index, right_event in enumerate(right_events):\n            if index in used_right:\n                continue\n            right_time = _parse_timestamp(right_event[\"event_at\"])\n            gap_seconds = abs((right_time - left_time).total_seconds())\n            if gap_seconds > JOIN_WINDOW_SECONDS:\n                continue\n            if best_index is None or gap_seconds < best_gap or (\n                gap_seconds == best_gap and right_event[\"event_at\"] < right_events[best_index][\"event_at\"]\n            ):\n                best_index = index\n                best_gap = gap_seconds\n        if best_index is None:\n            _record_unmatched(windows, event=left_event, side=\"left\")\n            continue\n        used_right.add(best_index)\n        matched_right = right_events[best_index]\n        gap_seconds = float(best_gap if best_gap is not None else 0.0)\n        gap_seconds_values.append(gap_seconds)\n        _record_matched_pair(windows, left_event=left_event, right_event=matched_right, gap_seconds=gap_seconds)\n\n    for index, right_event in enumerate(right_events):\n        if index not in used_right:\n            _record_unmatched(windows, event=right_event, side=\"right\")\n\n    finalized_windows = [_finalize_window_summary(windows[window_key]) for window_key in sorted(windows)]\n    matched_pairs = sum(item[\"matched_pairs\"] for item in finalized_windows)\n    unmatched_left = sum(item[\"left_only_events\"] for item in finalized_windows)\n    unmatched_right = sum(item[\"right_only_events\"] for item in finalized_windows)\n    total_left = sum(item[\"left_events\"] for item in finalized_windows)\n    total_right = sum(item[\"right_events\"] for item in finalized_windows)\n    hottest_window = max(\n        finalized_windows,\n        key=lambda item: (item[\"matched_pairs\"], item[\"left_events\"] + item[\"right_events\"], item[\"window_start\"]),\n        default=None,\n    )\n    matched_candidate_total = min(total_left, total_right)\n    return {\n        \"correlation_key\": key,\n        \"window_count\": len(finalized_windows),\n        \"left_events\": total_left,\n        \"right_events\": total_right,\n        \"matched_pairs\": matched_pairs,\n        \"unmatched_left_events\": unmatched_left,\n        \"unmatched_right_events\": unmatched_right,\n        \"join_coverage_rate\": round(matched_pairs / matched_candidate_total, 3) if matched_candidate_total else 0.0,\n        \"avg_gap_seconds\": round(sum(gap_seconds_values) / len(gap_seconds_values), 3) if gap_seconds_values else 0.0,\n        \"max_gap_seconds\": round(max(gap_seconds_values), 3) if gap_seconds_values else 0.0,\n        \"join_window_minutes\": JOIN_WINDOW_MINUTES,\n        \"hottest_window_start\": hottest_window[\"window_start\"] if hottest_window else None,\n        \"hottest_window_matches\": hottest_window[\"matched_pairs\"] if hottest_window else 0,\n        \"windows\": finalized_windows,\n    }"` |
| `reducer_source_line` | `23` | `204` |
| `reducer_source_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L23-L27"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L204-L270"` |

### Diff 2: `projects/mini-mapreduce-lab/plugins_rolling_window_join.py` → `projects/mini-mapreduce-lab/plugins_service_latency.py`
- Changed fields: `available_dataset_families, benchmark_generator, benchmark_generator_doc_summary, benchmark_generator_source_anchor, benchmark_generator_source_commit_url, benchmark_generator_source_excerpt, benchmark_generator_source_line, benchmark_generator_source_url, benchmark_note_hook, benchmark_note_hook_doc_summary, benchmark_note_hook_source_anchor, benchmark_note_hook_source_commit_url, benchmark_note_hook_source_excerpt, benchmark_note_hook_source_line, benchmark_note_hook_source_url, combiner, combiner_doc_summary, combiner_source_anchor, combiner_source_commit_url, combiner_source_excerpt, combiner_source_line, combiner_source_url, mapper, mapper_doc_summary, mapper_source_anchor, mapper_source_commit_url, mapper_source_excerpt, mapper_source_line, mapper_source_url, module_doc_summary, name, plugin, reducer, reducer_doc_summary, reducer_signature, reducer_source_anchor, reducer_source_commit_url, reducer_source_excerpt, reducer_source_line, reducer_source_url`

| Field | Previous | Current |
| --- | --- | --- |
| `available_dataset_families` | `["default", "checkout-funnel", "incident-correlation"]` | `["default", "incident-spike", "batch-window"]` |
| `benchmark_generator` | `"plugins_rolling_window_join.benchmark_records"` | `"plugins_service_latency.benchmark_records"` |
| `benchmark_generator_doc_summary` | `"Generate deterministic two-stream correlation fixtures for rolling join demos."` | `"Generate deterministic latency fixtures for multiple observability-style families."` |
| `benchmark_generator_source_anchor` | `"plugins_rolling_window_join.py#L273-L348"` | `"plugins_service_latency.py#L67-L131"` |
| `benchmark_generator_source_commit_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L273-L348"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_service_latency.py#L67-L131"` |
| `benchmark_generator_source_excerpt` | `"def benchmark_records(scenario, records, seed, dataset_family=\"default\"):\n    \"\"\"Generate deterministic two-stream correlation fixtures for rolling join demos.\"\"\"\n    if records <= 0:\n        raise ValueError(\"records must be positive\")\n    rng = random.Random(seed)\n    base_time = datetime(2026, 4, 17, 9, 0, tzinfo=timezone.utc)\n\n    families = {\n        \"default\": {\n            \"balanced\": [\n                {\"key\": \"join-pod-alpha\", \"weight\": 1.0, \"window_offsets\": [0, 5, 10], \"left_label\": \"request-start\", \"right_label\": \"request-finish\", \"match_ratio\": 0.86, \"right_lag_seconds\": 52},\n                {\"key\": \"join-pod-beta\", \"weight\": 1.0, \"window_offsets\": [0, 5, 10], \"left_label\": \"request-start\", \"right_label\": \"request-finish\", \"match_ratio\": 0.84, \"right_lag_seconds\": 61},\n                {\"key\": \"join-pod-gamma\", \"weight\": 1.0, \"window_offsets\": [5, 10, 15], \"left_label\": \"request-start\", \"right_label\": \"request-finish\", \"match_ratio\": 0.83, \"right_lag_seconds\": 57},\n                {\"key\": \"join-pod-delta\", \"weight\": 1.0, \"window_offsets\": [0, 10, 15], \"left_label\": \"request-start\", \"right_label\": \"request-finish\", \"match_ratio\": 0.82, \"right_lag_seconds\": 68},\n            ],\n            \"skewed\": [\n                {\"key\": \"join-hotspot\", \"weight\": 4.0, \"window_offsets\": [10, 10, 15], \"left_label\": \"request-start\", \"right_label\": \"request-finish\", \"match_ratio\": 0.72, \"right_lag_seconds\": 97, \"hotspot_offsets\": [10], \"hotspot_bonus\": 40, \"left_only_share\": 0.7},\n                {\"key\": \"join-pod-beta\", \"weight\": 1.1, \"window_offsets\": [0, 10, 15], \"left_label\": \"request-start\", \"right_label\": \"request-finish\", \"match_ratio\": 0.82, \"right_lag_seconds\": 64},\n                {\"key\": \"join-pod-gamma\", \"weight\": 1.0, \"window_offsets\": [5, 15, 20], \"left_label\": \"request-start\", \"right_label\": \"request-finish\", \"match_ratio\": 0.8, \"right_lag_seconds\": 70},\n                {\"key\": \"join-pod-delta\", \"weight\": 0.9, \"window_offsets\": [0, 15, 20], \"left_label\": \"request-start\", \"right_label\": \"request-finish\", \"match_ratio\": 0.78, \"right_lag_seconds\": 75},\n            ],\n        },\n        \"checkout-funnel\": {\n            \"balanced\": [\n                {\"key\": \"checkout-core\", \"weight\": 1.2, \"window_offsets\": [5, 10, 15], \"left_label\": \"cart-update\", \"right_label\": \"payment-auth\", \"match_ratio\": 0.88, \"right_lag_seconds\": 48},\n                {\"key\": \"express-lane\", \"weight\": 1.0, \"window_offsets\": [5, 10, 15], \"left_label\": \"cart-update\", \"right_label\": \"payment-auth\", \"match_ratio\": 0.9, \"right_lag_seconds\": 38},\n                {\"key\": \"promo-retry\", \"weight\": 1.0, \"window_offsets\": [0, 10, 20], \"left_label\": \"cart-update\", \"right_label\": \"payment-auth\", \"match_ratio\": 0.8, \"right_lag_seconds\": 66},\n                {\"key\": \"inventory-sync\", \"weight\": 0.9, \"window_offsets\": [0, 5, 15], \"left_label\": \"cart-update\", \"right_label\": \"payment-auth\", \"match_ratio\": 0.84, \"right_lag_seconds\": 58},\n            ],\n            \"skewed\": [\n                {\"key\": \"checkout-core\", \"weight\": 4.3, \"window_offsets\": [10, 10, 15], \"left_label\": \"cart-update\", \"right_label\": \"payment-auth\", \"match_ratio\": 0.7, \"right_lag_seconds\": 102, \"hotspot_offsets\": [10], \"hotspot_bonus\": 55, \"left_only_share\": 0.75},\n                {\"key\": \"promo-retry\", \"weight\": 1.5, \"window_offsets\": [10, 15, 20], \"left_label\": \"cart-update\", \"right_label\": \"payment-auth\", \"match_ratio\": 0.76, \"right_lag_seconds\": 88, \"hotspot_offsets\": [15], \"hotspot_bonus\": 32, \"left_only_share\": 0.65},\n                {\"key\": \"express-lane\", \"weight\": 1.0, \"window_offsets\": [5, 15, 20], \"left_label\": \"cart-update\", \"right_label\": \"payment-auth\", \"match_ratio\": 0.86, \"right_lag_seconds\": 42},\n                {\"key\": \"inventory-sync\", \"weight\": 0.8, \"window_offsets\": [0, 10, 20], \"left_label\": \"cart-update\", \"right_label\": \"payment-auth\", \"match_ratio\": 0.8, \"right_lag_seconds\": 63},\n            ],\n        },\n        \"incident-correlation\": {\n            \"balanced\": [\n                {\"key\": \"payments-api\", \"weight\": 1.1, \"window_offsets\": [0, 5, 10], \"left_label\": \"alert-fired\", \"right_label\": \"deploy-event\", \"match_ratio\": 0.83, \"right_lag_seconds\": 74},\n                {\"key\": \"auth-gateway\", \"weight\": 1.0, \"window_offsets\": [0, 10, 15], \"left_label\": \"alert-fired\", \"right_label\": \"deploy-event\", \"match_ratio\": 0.82, \"right_lag_seconds\": 81},\n                {\"key\": \"search-api\", \"weight\": 1.0, \"window_offsets\": [5, 10, 20], \"left_label\": \"alert-fired\", \"right_label\": \"deploy-event\", \"match_ratio\": 0.84, \"right_lag_seconds\": 72},\n                {\"key\": \"edge-cache\", \"weight\": 0.9, \"window_offsets\": [0, 15, 20], \"left_label\": \"alert-fired\", \"right_label\": \"deploy-event\", \"match_ratio\": 0.8, \"right_lag_seconds\": 90},\n            ],\n            \"skewed\": [\n                {\"key\": \"payments-api\", \"weight\": 4.1, \"window_offsets\": [15, 20, 20], \"left_label\": \"alert-fired\", \"right_label\": \"deploy-event\", \"match_ratio\": 0.68, \"right_lag_seconds\": 118, \"hotspot_offsets\": [20], \"hotspot_bonus\": 48, \"left_only_share\": 0.72},\n                {\"key\": \"auth-gateway\", \"weight\": 1.4, \"window_offsets\": [10, 15, 20], \"left_label\": \"alert-fired\", \"right_label\": \"deploy-event\", \"match_ratio\": 0.74, \"right_lag_seconds\": 96, \"hotspot_offsets\": [15], \"hotspot_bonus\": 26, \"left_only_share\": 0.62},\n                {\"key\": \"search-api\", \"weight\": 1.0, \"window_offsets\": [5, 15, 25], \"left_label\": \"alert-fired\", \"right_label\": \"deploy-event\", \"match_ratio\": 0.82, \"right_lag_seconds\": 77},\n                {\"key\": \"edge-cache\", \"weight\": 0.8, \"window_offsets\": [0, 10, 25], \"left_label\": \"alert-fired\", \"right_label\": \"deploy-event\", \"match_ratio\": 0.78, \"right_lag_seconds\": 88},\n            ],\n        },\n    }\n    if dataset_family not in families or scenario not in families[dataset_family]:\n        raise ValueError(f\"unsupported plugin benchmark scenario/family: {scenario}/{dataset_family}\")\n\n    profiles = families[dataset_family][scenario]\n    counts = _allocate_counts(records, [profile[\"weight\"] for profile in profiles])\n    lines = []\n    for profile, count in zip(profiles, counts):\n        lines.extend(\n            _generate_join_events(\n                key=profile[\"key\"],\n                count=count,\n                base_time=base_time,\n                window_offsets=profile[\"window_offsets\"],\n                left_label=profile[\"left_label\"],\n                right_label=profile[\"right_label\"],\n                rng=rng,\n                match_ratio=profile[\"match_ratio\"],\n                right_lag_seconds=profile[\"right_lag_seconds\"],\n                hotspot_offsets=profile.get(\"hotspot_offsets\"),\n                hotspot_bonus=profile.get(\"hotspot_bonus\", 0),\n                left_only_share=profile.get(\"left_only_share\", 0.5),\n            )\n        )\n    lines.sort(key=lambda line: tuple(line.split(\",\", maxsplit=3)[:3]))\n    return lines[:records]"` | `"def benchmark_records(scenario, records, seed, dataset_family=\"default\"):\n    \"\"\"Generate deterministic latency fixtures for multiple observability-style families.\"\"\"\n    if records <= 0:\n        raise ValueError(\"records must be positive\")\n    rng = random.Random(seed)\n\n    families = {\n        \"default\": {\n            \"balanced\": [\n                (\"edge-api\", 82, 9),\n                (\"catalog-api\", 76, 8),\n                (\"checkout-api\", 88, 10),\n                (\"search-api\", 71, 7),\n            ],\n            \"skewed\": [\n                (\"edge-api\", 144, 26),\n                (\"catalog-api\", 84, 10),\n                (\"checkout-api\", 96, 12),\n                (\"search-api\", 74, 8),\n            ],\n        },\n        \"incident-spike\": {\n            \"balanced\": [\n                (\"auth-gateway\", 118, 12),\n                (\"session-cache\", 89, 8),\n                (\"token-service\", 102, 10),\n                (\"profile-read\", 78, 7),\n            ],\n            \"skewed\": [\n                (\"auth-gateway\", 236, 54),\n                (\"session-cache\", 148, 22),\n                (\"token-service\", 121, 14),\n                (\"profile-read\", 83, 9),\n            ],\n        },\n        \"batch-window\": {\n            \"balanced\": [\n                (\"warehouse-loader\", 264, 30),\n                (\"index-builder\", 221, 24),\n                (\"backfill-runner\", 246, 27),\n                (\"metrics-rollup\", 198, 21),\n            ],\n            \"skewed\": [\n                (\"warehouse-loader\", 462, 86),\n                (\"index-builder\", 274, 34),\n                (\"backfill-runner\", 318, 42),\n                (\"metrics-rollup\", 206, 25),\n            ],\n        },\n    }\n    if dataset_family not in families or scenario not in families[dataset_family]:\n        raise ValueError(f\"unsupported plugin benchmark scenario/family: {scenario}/{dataset_family}\")\n\n    templates = families[dataset_family][scenario]\n    lines = []\n    for index in range(records):\n        service, base_ms, spread_ms = templates[index % len(templates)]\n        jitter = rng.randint(-spread_ms, spread_ms)\n        lines.append(f\"{service},{round(base_ms + jitter, 3)}\")\n    if scenario == \"skewed\":\n        hotspot = templates[0][0]\n        for index in range(max(1, records // 3)):\n            latency = templates[0][1] + templates[0][2] + rng.randint(18, 52)\n            lines[index] = f\"{hotspot},{round(latency, 3)}\"\n    return lines"` |
| `benchmark_generator_source_line` | `273` | `67` |
| `benchmark_generator_source_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L273-L348"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L67-L131"` |
| `benchmark_note_hook` | `"plugins_rolling_window_join.benchmark_notes"` | `"plugins_service_latency.benchmark_notes"` |
| `benchmark_note_hook_doc_summary` | `"Describe the intended join hotspot and portfolio story for each synthetic family."` | `"Describe the intended hot services for each synthetic latency family."` |
| `benchmark_note_hook_source_anchor` | `"plugins_rolling_window_join.py#L351-L420"` | `"plugins_service_latency.py#L134-L203"` |
| `benchmark_note_hook_source_commit_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L351-L420"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_service_latency.py#L134-L203"` |
| `benchmark_note_hook_source_excerpt` | `"def benchmark_notes(scenario, dataset_family=\"default\"):\n    \"\"\"Describe the intended join hotspot and portfolio story for each synthetic family.\"\"\"\n    notes = {\n        (\"balanced\", \"default\"): [\n            {\n                \"title\": \"Steady correlation baseline\",\n                \"detail\": \"The default balanced family keeps four correlation keys close together with only mild spillover, so the report reads like a healthy request/response join workload instead of an incident.\",\n                \"severity\": \"info\",\n                \"takeaway\": \"Use this as the before state when explaining how one correlation key can dominate a rolling join workload even if the reducer partitioner stays deterministic.\",\n            },\n        ],\n        (\"skewed\", \"default\"): [\n            {\n                \"title\": \"Join hotspot concentration\",\n                \"detail\": \"`join-hotspot` absorbs most of the left/right traffic here, so the hottest reducer should read like one correlation key monopolizing the join stage and leaving extra unmatched left events behind.\",\n                \"severity\": \"watch\",\n                \"hotspot_keys\": [\"join-hotspot\"],\n                \"takeaway\": \"This is the simplest story for showing why stream joins introduce both hotspot pressure and mismatch cleanup work.\",\n            },\n        ],\n        (\"balanced\", \"checkout-funnel\"): [\n            {\n                \"title\": \"Healthy checkout handoff\",\n                \"detail\": \"The balanced checkout family keeps `cart-update` and `payment-auth` events closely paired across several flows, so the join output reads like a normal purchase funnel rather than a broken queue.\",\n                \"severity\": \"info\",\n                \"takeaway\": \"Good for presenting the plugin as a product/commerce analytics example instead of only infra telemetry.\",\n            },\n        ],\n        (\"skewed\", \"checkout-funnel\"): [\n            {\n                \"title\": \"Checkout core backlog\",\n                \"detail\": \"`checkout-core` becomes the dominant join key with the worst pairing lag, so the report looks like a spike of cart updates outrunning payment authorizations during a launch or sale.\",\n                \"severity\": \"risk\",\n                \"hotspot_keys\": [\"checkout-core\"],\n                \"takeaway\": \"Call out the combination of lower coverage and higher gap when telling the story of queue lag or degraded downstream auth capacity.\",\n            },\n            {\n                \"title\": \"Promo retry spillover\",\n                \"detail\": \"`promo-retry` is the second-tier correlation hotspot behind checkout-core, which helps explain how retries can spread join pressure to a supporting flow instead of one isolated key.\",\n                \"severity\": \"watch\",\n                \"hotspot_keys\": [\"promo-retry\"],\n                \"takeaway\": \"Keep this note when you want the benchmark to feel like a fuller checkout system instead of one synthetic broken key.\",\n            },\n        ],\n        (\"balanced\", \"incident-correlation\"): [\n            {\n                \"title\": \"Routine alert/deploy audit trail\",\n                \"detail\": \"The balanced incident-correlation family keeps alerts and deploy events close enough that the join output reads like a calm incident-review dashboard instead of a chaotic release.\",\n                \"severity\": \"info\",\n                \"takeaway\": \"Use this as the steady baseline before a noisy release or rollback starts separating alerts from the deploys that explain them.\",\n            },\n        ],\n        (\"skewed\", \"incident-correlation\"): [\n            {\n                \"title\": \"Payments incident war room\",\n                \"detail\": \"`payments-api` dominates the skewed incident family with long join gaps and extra unmatched alerts, so the benchmark looks like a release that triggered alarms faster than deploy metadata propagated.\",\n                \"severity\": \"risk\",\n                \"hotspot_keys\": [\"payments-api\"],\n                \"takeaway\": \"This turns the plugin into a systems-debugging narrative about correlating alerts, deploys, and lagging metadata streams.\",\n            },\n            {\n                \"title\": \"Auth gateway follow-on noise\",\n                \"detail\": \"`auth-gateway` forms a smaller supporting hotspot that helps the report tell a more realistic multi-service release story instead of one isolated outage key.\",\n                \"severity\": \"watch\",\n                \"hotspot_keys\": [\"auth-gateway\"],\n                \"takeaway\": \"Keep this note when you want to explain correlated release fallout across adjacent services.\",\n            },\n        ],\n    }\n    return notes.get((scenario, dataset_family), [])"` | `"def benchmark_notes(scenario, dataset_family=\"default\"):\n    \"\"\"Describe the intended hot services for each synthetic latency family.\"\"\"\n    notes = {\n        (\"balanced\", \"default\"): [\n            {\n                \"title\": \"Healthy service spread\",\n                \"detail\": \"The default balanced latency family rotates evenly across four APIs, so reducer load should stay close while the output still looks like a small production stack.\",\n                \"severity\": \"info\",\n                \"takeaway\": \"Use this as the calm baseline before introducing latency hotspots or on-call incident narratives.\",\n            },\n        ],\n        (\"skewed\", \"default\"): [\n            {\n                \"title\": \"Edge API hotspot\",\n                \"detail\": \"`edge-api` is intentionally heavier and slower here, so the hottest reducer should read like a front-door latency spike instead of a partitioning accident.\",\n                \"severity\": \"watch\",\n                \"hotspot_keys\": [\"edge-api\"],\n                \"takeaway\": \"This is the simplest observability-style story for discussing why p95 matters more than the mean under hotspot traffic.\",\n            },\n        ],\n        (\"balanced\", \"incident-spike\"): [\n            {\n                \"title\": \"Steady auth baseline\",\n                \"detail\": \"The balanced incident family keeps auth, cache, token, and profile services close enough that the report highlights normal service-to-service variance rather than an outage.\",\n                \"severity\": \"info\",\n                \"takeaway\": \"This is the before state for the incident-spike storyline.\",\n            },\n        ],\n        (\"skewed\", \"incident-spike\"): [\n            {\n                \"title\": \"Auth gateway timeout storm\",\n                \"detail\": \"`auth-gateway` dominates this family with elevated latency, so the hottest reducer should look like an outage-era timeout storm concentrated around one service.\",\n                \"severity\": \"risk\",\n                \"hotspot_keys\": [\"auth-gateway\"],\n                \"takeaway\": \"Call out the gap between average and p95 latency here to explain why long-tail spikes matter during incidents.\",\n            },\n            {\n                \"title\": \"Session cache spillover\",\n                \"detail\": \"`session-cache` forms the second-tier hotspot behind the auth gateway, which helps tell a broader bottleneck story about downstream spillover instead of a single bad node.\",\n                \"severity\": \"watch\",\n                \"hotspot_keys\": [\"session-cache\"],\n                \"takeaway\": \"Keep this annotation when you want a fuller causal narrative about cascading latency during the same incident.\",\n            },\n            {\n                \"title\": \"Profile path cool lane\",\n                \"detail\": \"`profile-read` stays comparatively cool, so it works as a low-priority contrast point or a card to collapse in tighter portfolio reports.\",\n                \"severity\": \"info\",\n                \"hotspot_keys\": [\"profile-read\"],\n                \"takeaway\": \"Use annotation filtering when you want the report to focus only on the riskiest paths.\",\n            },\n        ],\n        (\"balanced\", \"batch-window\"): [\n            {\n                \"title\": \"Even batch cadence\",\n                \"detail\": \"The balanced batch-window family rotates evenly across warehouse, indexing, backfill, and metrics jobs so the reducer heatmap reflects a normal overnight data window.\",\n                \"severity\": \"info\",\n                \"takeaway\": \"This family is useful when you want a data-engineering story rather than an incident-response story.\",\n            },\n        ],\n        (\"skewed\", \"batch-window\"): [\n            {\n                \"title\": \"Warehouse loader saturation\",\n                \"detail\": \"`warehouse-loader` is intentionally the hottest and slowest key here, so the benchmark looks like a batch-window saturation problem during an oversized ingest run.\",\n                \"severity\": \"watch\",\n                \"hotspot_keys\": [\"warehouse-loader\"],\n                \"takeaway\": \"Use this family to talk about long-running ETL contention and why reducer skew can line up with operational bottlenecks.\",\n            },\n        ],\n    }\n    return notes.get((scenario, dataset_family), [])"` |
| `benchmark_note_hook_source_line` | `351` | `134` |
| `benchmark_note_hook_source_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L351-L420"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L134-L203"` |
| `combiner` | `"plugins_rolling_window_join.combine_values"` | `"plugins_service_latency.combine_values"` |
| `combiner_doc_summary` | `"Keep shard-local join candidates JSON-safe before final pairing."` | `"Merge shard-local latency summaries before the final reduce step."` |
| `combiner_source_anchor` | `"plugins_rolling_window_join.py#L199-L201"` | `"plugins_service_latency.py#L49-L51"` |
| `combiner_source_commit_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L199-L201"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_service_latency.py#L49-L51"` |
| `combiner_source_excerpt` | `"def combine_values(_key, values):\n    \"\"\"Keep shard-local join candidates JSON-safe before final pairing.\"\"\"\n    return {\"events\": sorted(values, key=lambda event: (event[\"event_at\"], event[\"side\"], event[\"label\"]))}"` | `"def combine_values(_key, values):\n    \"\"\"Merge shard-local latency summaries before the final reduce step.\"\"\"\n    return _merge_latency_values(values)"` |
| `combiner_source_line` | `199` | `49` |
| `combiner_source_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L199-L201"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L49-L51"` |
| `mapper` | `"plugins_rolling_window_join.map_records"` | `"plugins_service_latency.map_records"` |
| `mapper_doc_summary` | `"Emit per-correlation-key event batches from key,side,timestamp,label rows."` | `"Parse comma-separated service/latency rows into partial latency summaries."` |
| `mapper_source_anchor` | `"plugins_rolling_window_join.py#L182-L196"` | `"plugins_service_latency.py#L33-L46"` |
| `mapper_source_commit_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L182-L196"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_service_latency.py#L33-L46"` |
| `mapper_source_excerpt` | `"def map_records(lines):\n    \"\"\"Emit per-correlation-key event batches from key,side,timestamp,label rows.\"\"\"\n    for raw in lines:\n        stripped = raw.strip()\n        if not stripped:\n            continue\n        key, side, event_at, label = [part.strip() for part in stripped.split(\",\", maxsplit=3)]\n        normalized_side = side.lower()\n        if normalized_side not in {\"left\", \"right\"}:\n            raise ValueError(\"rolling-window-join side must be 'left' or 'right'\")\n        yield key.lower(), {\n            \"side\": normalized_side,\n            \"event_at\": _isoformat_z(_parse_timestamp(event_at)),\n            \"label\": label,\n        }"` | `"def map_records(lines):\n    \"\"\"Parse comma-separated service/latency rows into partial latency summaries.\"\"\"\n    for raw in lines:\n        stripped = raw.strip()\n        if not stripped:\n            continue\n        service, latency_ms = stripped.split(\",\", maxsplit=1)\n        latency_value = round(float(latency_ms.strip()), 3)\n        yield service.strip().lower(), {\n            \"count\": 1,\n            \"sum_ms\": latency_value,\n            \"max_ms\": latency_value,\n            \"samples_ms\": [latency_value],\n        }"` |
| `mapper_source_line` | `182` | `33` |
| `mapper_source_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L182-L196"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L33-L46"` |
| `module_doc_summary` | `"Rolling-window join plugin for multi-stream correlation and pipeline-debug demos."` | `"Service-latency summary plugin for observability-style benchmark demos."` |
| `name` | `"plugin-rolling-window-join"` | `"plugin-service-latency"` |
| `plugin` | `"projects/mini-mapreduce-lab/plugins_rolling_window_join.py"` | `"projects/mini-mapreduce-lab/plugins_service_latency.py"` |
| `reducer` | `"plugins_rolling_window_join.reduce_key"` | `"plugins_service_latency.reduce_key"` |
| `reducer_doc_summary` | `"Pair left/right events within a rolling join window and summarize unmatched spillover."` | `"Return count, average, p95, and max latency for one service key."` |
| `reducer_signature` | `"reduce_key(key, values)"` | `"reduce_key(_key, values)"` |
| `reducer_source_anchor` | `"plugins_rolling_window_join.py#L204-L270"` | `"plugins_service_latency.py#L54-L64"` |
| `reducer_source_commit_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L204-L270"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_service_latency.py#L54-L64"` |
| `reducer_source_excerpt` | `"def reduce_key(key, values):\n    \"\"\"Pair left/right events within a rolling join window and summarize unmatched spillover.\"\"\"\n    merged = _merge_event_batches(values)\n    events = merged[\"events\"]\n    left_events = [event for event in events if event[\"side\"] == \"left\"]\n    right_events = [event for event in events if event[\"side\"] == \"right\"]\n    used_right = set()\n    windows = {}\n    gap_seconds_values = []\n\n    for left_event in left_events:\n        left_time = _parse_timestamp(left_event[\"event_at\"])\n        best_index = None\n        best_gap = None\n        for index, right_event in enumerate(right_events):\n            if index in used_right:\n                continue\n            right_time = _parse_timestamp(right_event[\"event_at\"])\n            gap_seconds = abs((right_time - left_time).total_seconds())\n            if gap_seconds > JOIN_WINDOW_SECONDS:\n                continue\n            if best_index is None or gap_seconds < best_gap or (\n                gap_seconds == best_gap and right_event[\"event_at\"] < right_events[best_index][\"event_at\"]\n            ):\n                best_index = index\n                best_gap = gap_seconds\n        if best_index is None:\n            _record_unmatched(windows, event=left_event, side=\"left\")\n            continue\n        used_right.add(best_index)\n        matched_right = right_events[best_index]\n        gap_seconds = float(best_gap if best_gap is not None else 0.0)\n        gap_seconds_values.append(gap_seconds)\n        _record_matched_pair(windows, left_event=left_event, right_event=matched_right, gap_seconds=gap_seconds)\n\n    for index, right_event in enumerate(right_events):\n        if index not in used_right:\n            _record_unmatched(windows, event=right_event, side=\"right\")\n\n    finalized_windows = [_finalize_window_summary(windows[window_key]) for window_key in sorted(windows)]\n    matched_pairs = sum(item[\"matched_pairs\"] for item in finalized_windows)\n    unmatched_left = sum(item[\"left_only_events\"] for item in finalized_windows)\n    unmatched_right = sum(item[\"right_only_events\"] for item in finalized_windows)\n    total_left = sum(item[\"left_events\"] for item in finalized_windows)\n    total_right = sum(item[\"right_events\"] for item in finalized_windows)\n    hottest_window = max(\n        finalized_windows,\n        key=lambda item: (item[\"matched_pairs\"], item[\"left_events\"] + item[\"right_events\"], item[\"window_start\"]),\n        default=None,\n    )\n    matched_candidate_total = min(total_left, total_right)\n    return {\n        \"correlation_key\": key,\n        \"window_count\": len(finalized_windows),\n        \"left_events\": total_left,\n        \"right_events\": total_right,\n        \"matched_pairs\": matched_pairs,\n        \"unmatched_left_events\": unmatched_left,\n        \"unmatched_right_events\": unmatched_right,\n        \"join_coverage_rate\": round(matched_pairs / matched_candidate_total, 3) if matched_candidate_total else 0.0,\n        \"avg_gap_seconds\": round(sum(gap_seconds_values) / len(gap_seconds_values), 3) if gap_seconds_values else 0.0,\n        \"max_gap_seconds\": round(max(gap_seconds_values), 3) if gap_seconds_values else 0.0,\n        \"join_window_minutes\": JOIN_WINDOW_MINUTES,\n        \"hottest_window_start\": hottest_window[\"window_start\"] if hottest_window else None,\n        \"hottest_window_matches\": hottest_window[\"matched_pairs\"] if hottest_window else 0,\n        \"windows\": finalized_windows,\n    }"` | `"def reduce_key(_key, values):\n    \"\"\"Return count, average, p95, and max latency for one service key.\"\"\"\n    merged = _merge_latency_values(values)\n    count = int(merged[\"count\"])\n    average = round(float(merged[\"sum_ms\"]) / count, 3) if count else 0.0\n    return {\n        \"count\": count,\n        \"avg_ms\": average,\n        \"p95_ms\": _nearest_rank_percentile(merged[\"samples_ms\"], 95),\n        \"max_ms\": round(float(merged[\"max_ms\"]), 3),\n    }"` |
| `reducer_source_line` | `204` | `54` |
| `reducer_source_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L204-L270"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L54-L64"` |

### Diff 3: `projects/mini-mapreduce-lab/plugins_service_latency.py` → `projects/mini-mapreduce-lab/plugins_sessionization.py`
- Changed fields: `available_dataset_families, benchmark_generator, benchmark_generator_doc_summary, benchmark_generator_source_anchor, benchmark_generator_source_commit_url, benchmark_generator_source_excerpt, benchmark_generator_source_line, benchmark_generator_source_url, benchmark_note_hook, benchmark_note_hook_doc_summary, benchmark_note_hook_source_anchor, benchmark_note_hook_source_commit_url, benchmark_note_hook_source_excerpt, benchmark_note_hook_source_line, benchmark_note_hook_source_url, combiner, combiner_doc_summary, combiner_source_anchor, combiner_source_commit_url, combiner_source_excerpt, combiner_source_line, combiner_source_url, mapper, mapper_doc_summary, mapper_source_anchor, mapper_source_commit_url, mapper_source_excerpt, mapper_source_line, mapper_source_url, module_doc_summary, name, plugin, reducer, reducer_doc_summary, reducer_source_anchor, reducer_source_commit_url, reducer_source_excerpt, reducer_source_line, reducer_source_url`

| Field | Previous | Current |
| --- | --- | --- |
| `available_dataset_families` | `["default", "incident-spike", "batch-window"]` | `["default", "exam-revision", "launch-day"]` |
| `benchmark_generator` | `"plugins_service_latency.benchmark_records"` | `"plugins_sessionization.benchmark_records"` |
| `benchmark_generator_doc_summary` | `"Generate deterministic latency fixtures for multiple observability-style families."` | `"Generate deterministic product-analytics event streams for sessionization demos."` |
| `benchmark_generator_source_anchor` | `"plugins_service_latency.py#L67-L131"` | `"plugins_sessionization.py#L135-L206"` |
| `benchmark_generator_source_commit_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_service_latency.py#L67-L131"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_sessionization.py#L135-L206"` |
| `benchmark_generator_source_excerpt` | `"def benchmark_records(scenario, records, seed, dataset_family=\"default\"):\n    \"\"\"Generate deterministic latency fixtures for multiple observability-style families.\"\"\"\n    if records <= 0:\n        raise ValueError(\"records must be positive\")\n    rng = random.Random(seed)\n\n    families = {\n        \"default\": {\n            \"balanced\": [\n                (\"edge-api\", 82, 9),\n                (\"catalog-api\", 76, 8),\n                (\"checkout-api\", 88, 10),\n                (\"search-api\", 71, 7),\n            ],\n            \"skewed\": [\n                (\"edge-api\", 144, 26),\n                (\"catalog-api\", 84, 10),\n                (\"checkout-api\", 96, 12),\n                (\"search-api\", 74, 8),\n            ],\n        },\n        \"incident-spike\": {\n            \"balanced\": [\n                (\"auth-gateway\", 118, 12),\n                (\"session-cache\", 89, 8),\n                (\"token-service\", 102, 10),\n                (\"profile-read\", 78, 7),\n            ],\n            \"skewed\": [\n                (\"auth-gateway\", 236, 54),\n                (\"session-cache\", 148, 22),\n                (\"token-service\", 121, 14),\n                (\"profile-read\", 83, 9),\n            ],\n        },\n        \"batch-window\": {\n            \"balanced\": [\n                (\"warehouse-loader\", 264, 30),\n                (\"index-builder\", 221, 24),\n                (\"backfill-runner\", 246, 27),\n                (\"metrics-rollup\", 198, 21),\n            ],\n            \"skewed\": [\n                (\"warehouse-loader\", 462, 86),\n                (\"index-builder\", 274, 34),\n                (\"backfill-runner\", 318, 42),\n                (\"metrics-rollup\", 206, 25),\n            ],\n        },\n    }\n    if dataset_family not in families or scenario not in families[dataset_family]:\n        raise ValueError(f\"unsupported plugin benchmark scenario/family: {scenario}/{dataset_family}\")\n\n    templates = families[dataset_family][scenario]\n    lines = []\n    for index in range(records):\n        service, base_ms, spread_ms = templates[index % len(templates)]\n        jitter = rng.randint(-spread_ms, spread_ms)\n        lines.append(f\"{service},{round(base_ms + jitter, 3)}\")\n    if scenario == \"skewed\":\n        hotspot = templates[0][0]\n        for index in range(max(1, records // 3)):\n            latency = templates[0][1] + templates[0][2] + rng.randint(18, 52)\n            lines[index] = f\"{hotspot},{round(latency, 3)}\"\n    return lines"` | `"def benchmark_records(scenario, records, seed, dataset_family=\"default\"):\n    \"\"\"Generate deterministic product-analytics event streams for sessionization demos.\"\"\"\n    if records <= 0:\n        raise ValueError(\"records must be positive\")\n    rng = random.Random(seed)\n    base_time = datetime(2026, 4, 17, 8, 0, tzinfo=timezone.utc)\n\n    families = {\n        \"default\": {\n            \"balanced\": [\n                {\"user\": \"student-alpha\", \"weight\": 1.0, \"session_size\": 3, \"session_gap\": 52, \"intra_gap\": 5, \"pages\": [\"home\", \"lecture-notes\", \"quiz\"]},\n                {\"user\": \"student-beta\", \"weight\": 1.0, \"session_size\": 3, \"session_gap\": 48, \"intra_gap\": 4, \"pages\": [\"home\", \"lab\", \"forum\"]},\n                {\"user\": \"student-gamma\", \"weight\": 1.0, \"session_size\": 4, \"session_gap\": 56, \"intra_gap\": 5, \"pages\": [\"home\", \"editor\", \"submissions\"]},\n                {\"user\": \"student-delta\", \"weight\": 1.0, \"session_size\": 3, \"session_gap\": 50, \"intra_gap\": 4, \"pages\": [\"home\", \"flashcards\", \"quiz\"]},\n            ],\n            \"skewed\": [\n                {\"user\": \"student-alpha\", \"weight\": 3.3, \"session_size\": 5, \"session_gap\": 38, \"intra_gap\": 4, \"pages\": [\"home\", \"lecture-notes\", \"quiz\", \"editor\"]},\n                {\"user\": \"student-beta\", \"weight\": 1.0, \"session_size\": 3, \"session_gap\": 55, \"intra_gap\": 5, \"pages\": [\"home\", \"lab\", \"forum\"]},\n                {\"user\": \"student-gamma\", \"weight\": 0.9, \"session_size\": 3, \"session_gap\": 58, \"intra_gap\": 5, \"pages\": [\"home\", \"editor\", \"submissions\"]},\n                {\"user\": \"student-delta\", \"weight\": 0.8, \"session_size\": 2, \"session_gap\": 62, \"intra_gap\": 6, \"pages\": [\"home\", \"flashcards\", \"quiz\"]},\n            ],\n        },\n        \"exam-revision\": {\n            \"balanced\": [\n                {\"user\": \"night-owl\", \"weight\": 1.1, \"session_size\": 4, \"session_gap\": 46, \"intra_gap\": 4, \"pages\": [\"review-guide\", \"quiz\", \"flashcards\"]},\n                {\"user\": \"lab-partner\", \"weight\": 1.0, \"session_size\": 3, \"session_gap\": 50, \"intra_gap\": 5, \"pages\": [\"practice-exam\", \"solutions\", \"forum\"]},\n                {\"user\": \"project-mate\", \"weight\": 1.0, \"session_size\": 3, \"session_gap\": 54, \"intra_gap\": 5, \"pages\": [\"review-guide\", \"editor\", \"submission\"]},\n                {\"user\": \"commuter\", \"weight\": 0.9, \"session_size\": 2, \"session_gap\": 58, \"intra_gap\": 6, \"pages\": [\"flashcards\", \"quiz\", \"summary\"]},\n            ],\n            \"skewed\": [\n                {\"user\": \"night-owl\", \"weight\": 3.8, \"session_size\": 6, \"session_gap\": 34, \"intra_gap\": 4, \"pages\": [\"review-guide\", \"quiz\", \"quiz-review\", \"flashcards\"]},\n                {\"user\": \"lab-partner\", \"weight\": 1.0, \"session_size\": 3, \"session_gap\": 52, \"intra_gap\": 5, \"pages\": [\"practice-exam\", \"solutions\", \"forum\"]},\n                {\"user\": \"project-mate\", \"weight\": 0.9, \"session_size\": 3, \"session_gap\": 56, \"intra_gap\": 5, \"pages\": [\"review-guide\", \"editor\", \"submission\"]},\n                {\"user\": \"commuter\", \"weight\": 0.7, \"session_size\": 2, \"session_gap\": 64, \"intra_gap\": 6, \"pages\": [\"flashcards\", \"quiz\", \"summary\"]},\n            ],\n        },\n        \"launch-day\": {\n            \"balanced\": [\n                {\"user\": \"release-lead\", \"weight\": 1.1, \"session_size\": 4, \"session_gap\": 42, \"intra_gap\": 4, \"pages\": [\"overview\", \"health\", \"errors\", \"deploy\"]},\n                {\"user\": \"qa-desk\", \"weight\": 1.0, \"session_size\": 3, \"session_gap\": 48, \"intra_gap\": 5, \"pages\": [\"smoke-tests\", \"errors\", \"feedback\"]},\n                {\"user\": \"support-ops\", \"weight\": 1.0, \"session_size\": 3, \"session_gap\": 50, \"intra_gap\": 5, \"pages\": [\"tickets\", \"feedback\", \"health\"]},\n                {\"user\": \"analytics-watch\", \"weight\": 0.9, \"session_size\": 3, \"session_gap\": 54, \"intra_gap\": 5, \"pages\": [\"overview\", \"conversion\", \"health\"]},\n            ],\n            \"skewed\": [\n                {\"user\": \"release-lead\", \"weight\": 4.0, \"session_size\": 6, \"session_gap\": 31, \"intra_gap\": 4, \"pages\": [\"overview\", \"health\", \"errors\", \"deploy\", \"rollback\"]},\n                {\"user\": \"qa-desk\", \"weight\": 1.1, \"session_size\": 4, \"session_gap\": 44, \"intra_gap\": 5, \"pages\": [\"smoke-tests\", \"errors\", \"feedback\"]},\n                {\"user\": \"support-ops\", \"weight\": 1.0, \"session_size\": 3, \"session_gap\": 50, \"intra_gap\": 5, \"pages\": [\"tickets\", \"feedback\", \"health\"]},\n                {\"user\": \"analytics-watch\", \"weight\": 0.8, \"session_size\": 2, \"session_gap\": 58, \"intra_gap\": 6, \"pages\": [\"overview\", \"conversion\", \"health\"]},\n            ],\n        },\n    }\n    if dataset_family not in families or scenario not in families[dataset_family]:\n        raise ValueError(f\"unsupported plugin benchmark scenario/family: {scenario}/{dataset_family}\")\n\n    profiles = families[dataset_family][scenario]\n    counts = _allocate_counts(records, [profile[\"weight\"] for profile in profiles])\n    events = []\n    for index, (profile, count) in enumerate(zip(profiles, counts)):\n        start_offset = timedelta(minutes=(index * 9) + rng.randint(0, 4))\n        events.extend(\n            _generate_user_events(\n                user=profile[\"user\"],\n                count=count,\n                start_at=base_time + start_offset,\n                session_size=profile[\"session_size\"],\n                session_gap_minutes=profile[\"session_gap\"] + rng.randint(-3, 3),\n                intra_gap_minutes=profile[\"intra_gap\"],\n                pages=profile[\"pages\"],\n            )\n        )\n    events.sort(key=lambda item: item[\"timestamp\"])\n    return [f\"{event['user']},{event['timestamp']},{event['page']}\" for event in events[:records]]"` |
| `benchmark_generator_source_line` | `67` | `135` |
| `benchmark_generator_source_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L67-L131"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_sessionization.py#L135-L206"` |
| `benchmark_note_hook` | `"plugins_service_latency.benchmark_notes"` | `"plugins_sessionization.benchmark_notes"` |
| `benchmark_note_hook_doc_summary` | `"Describe the intended hot services for each synthetic latency family."` | `"Describe the intended hotspot users and browsing patterns for each family."` |
| `benchmark_note_hook_source_anchor` | `"plugins_service_latency.py#L134-L203"` | `"plugins_sessionization.py#L209-L278"` |
| `benchmark_note_hook_source_commit_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_service_latency.py#L134-L203"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_sessionization.py#L209-L278"` |
| `benchmark_note_hook_source_excerpt` | `"def benchmark_notes(scenario, dataset_family=\"default\"):\n    \"\"\"Describe the intended hot services for each synthetic latency family.\"\"\"\n    notes = {\n        (\"balanced\", \"default\"): [\n            {\n                \"title\": \"Healthy service spread\",\n                \"detail\": \"The default balanced latency family rotates evenly across four APIs, so reducer load should stay close while the output still looks like a small production stack.\",\n                \"severity\": \"info\",\n                \"takeaway\": \"Use this as the calm baseline before introducing latency hotspots or on-call incident narratives.\",\n            },\n        ],\n        (\"skewed\", \"default\"): [\n            {\n                \"title\": \"Edge API hotspot\",\n                \"detail\": \"`edge-api` is intentionally heavier and slower here, so the hottest reducer should read like a front-door latency spike instead of a partitioning accident.\",\n                \"severity\": \"watch\",\n                \"hotspot_keys\": [\"edge-api\"],\n                \"takeaway\": \"This is the simplest observability-style story for discussing why p95 matters more than the mean under hotspot traffic.\",\n            },\n        ],\n        (\"balanced\", \"incident-spike\"): [\n            {\n                \"title\": \"Steady auth baseline\",\n                \"detail\": \"The balanced incident family keeps auth, cache, token, and profile services close enough that the report highlights normal service-to-service variance rather than an outage.\",\n                \"severity\": \"info\",\n                \"takeaway\": \"This is the before state for the incident-spike storyline.\",\n            },\n        ],\n        (\"skewed\", \"incident-spike\"): [\n            {\n                \"title\": \"Auth gateway timeout storm\",\n                \"detail\": \"`auth-gateway` dominates this family with elevated latency, so the hottest reducer should look like an outage-era timeout storm concentrated around one service.\",\n                \"severity\": \"risk\",\n                \"hotspot_keys\": [\"auth-gateway\"],\n                \"takeaway\": \"Call out the gap between average and p95 latency here to explain why long-tail spikes matter during incidents.\",\n            },\n            {\n                \"title\": \"Session cache spillover\",\n                \"detail\": \"`session-cache` forms the second-tier hotspot behind the auth gateway, which helps tell a broader bottleneck story about downstream spillover instead of a single bad node.\",\n                \"severity\": \"watch\",\n                \"hotspot_keys\": [\"session-cache\"],\n                \"takeaway\": \"Keep this annotation when you want a fuller causal narrative about cascading latency during the same incident.\",\n            },\n            {\n                \"title\": \"Profile path cool lane\",\n                \"detail\": \"`profile-read` stays comparatively cool, so it works as a low-priority contrast point or a card to collapse in tighter portfolio reports.\",\n                \"severity\": \"info\",\n                \"hotspot_keys\": [\"profile-read\"],\n                \"takeaway\": \"Use annotation filtering when you want the report to focus only on the riskiest paths.\",\n            },\n        ],\n        (\"balanced\", \"batch-window\"): [\n            {\n                \"title\": \"Even batch cadence\",\n                \"detail\": \"The balanced batch-window family rotates evenly across warehouse, indexing, backfill, and metrics jobs so the reducer heatmap reflects a normal overnight data window.\",\n                \"severity\": \"info\",\n                \"takeaway\": \"This family is useful when you want a data-engineering story rather than an incident-response story.\",\n            },\n        ],\n        (\"skewed\", \"batch-window\"): [\n            {\n                \"title\": \"Warehouse loader saturation\",\n                \"detail\": \"`warehouse-loader` is intentionally the hottest and slowest key here, so the benchmark looks like a batch-window saturation problem during an oversized ingest run.\",\n                \"severity\": \"watch\",\n                \"hotspot_keys\": [\"warehouse-loader\"],\n                \"takeaway\": \"Use this family to talk about long-running ETL contention and why reducer skew can line up with operational bottlenecks.\",\n            },\n        ],\n    }\n    return notes.get((scenario, dataset_family), [])"` | `"def benchmark_notes(scenario, dataset_family=\"default\"):\n    \"\"\"Describe the intended hotspot users and browsing patterns for each family.\"\"\"\n    notes = {\n        (\"balanced\", \"default\"): [\n            {\n                \"title\": \"Even study cadence\",\n                \"detail\": \"The default balanced family spreads activity across four students with similarly sized bursts, so reducer load should stay close while the output still demonstrates session boundaries.\",\n                \"severity\": \"info\",\n                \"takeaway\": \"Use this as the calm baseline before showing why repeated bursts from one user change the session story.\",\n            },\n        ],\n        (\"skewed\", \"default\"): [\n            {\n                \"title\": \"Student alpha cram loop\",\n                \"detail\": \"`student-alpha` revisits notes, quizzes, and the editor in repeated short bursts, so the hottest reducer should look like one user driving most session starts and events.\",\n                \"severity\": \"watch\",\n                \"hotspot_keys\": [\"student-alpha\"],\n                \"takeaway\": \"This is the simplest sessionization story for discussing hot users versus evenly distributed class traffic.\",\n            },\n        ],\n        (\"balanced\", \"exam-revision\"): [\n            {\n                \"title\": \"Shared review week\",\n                \"detail\": \"The balanced exam family keeps revision activity spread across multiple learners and shorter study sessions, which makes the session summaries read like a healthy pre-exam baseline.\",\n                \"severity\": \"info\",\n                \"takeaway\": \"Good for explaining why session counts alone are not enough without session length and event intensity.\",\n            },\n        ],\n        (\"skewed\", \"exam-revision\"): [\n            {\n                \"title\": \"Night-owl marathon\",\n                \"detail\": \"`night-owl` owns most of the benchmark volume here with repeated late-session bursts, so the reducer heatmap should show one learner dominating both activity and longest-session metrics.\",\n                \"severity\": \"risk\",\n                \"hotspot_keys\": [\"night-owl\"],\n                \"takeaway\": \"Call out how sessionization turns a raw clickstream into a workload story about sustained study behavior instead of isolated page hits.\",\n            },\n            {\n                \"title\": \"Commuter quick checks\",\n                \"detail\": \"`commuter` stays small and bursty, which makes it a useful low-priority contrast key when tightening the portfolio narrative down to the primary hotspot.\",\n                \"severity\": \"info\",\n                \"hotspot_keys\": [\"commuter\"],\n                \"takeaway\": \"This annotation is a good candidate to collapse in portfolio-tight reports.\",\n            },\n        ],\n        (\"balanced\", \"launch-day\"): [\n            {\n                \"title\": \"Coordinated launch monitoring\",\n                \"detail\": \"The balanced launch-day family keeps release, QA, support, and analytics roles close enough that the session summary reads like a calm release checklist instead of an incident.\",\n                \"severity\": \"info\",\n                \"takeaway\": \"Use this as the before state for the launch-day hotspot story.\",\n            },\n        ],\n        (\"skewed\", \"launch-day\"): [\n            {\n                \"title\": \"Release lead war room\",\n                \"detail\": \"`release-lead` dominates this family with back-to-back dashboard, deploy, and rollback visits, so the hottest reducer should look like one operator repeatedly re-entering a release war room.\",\n                \"severity\": \"risk\",\n                \"hotspot_keys\": [\"release-lead\"],\n                \"takeaway\": \"This turns the plugin into a product-analytics case study about launch-day behavior rather than generic score aggregation.\",\n            },\n            {\n                \"title\": \"QA desk verification loop\",\n                \"detail\": \"`qa-desk` forms a second-tier hotspot behind the release lead, which helps the report show supporting verification traffic instead of a single isolated key.\",\n                \"severity\": \"watch\",\n                \"hotspot_keys\": [\"qa-desk\"],\n                \"takeaway\": \"Keep this note when you want a fuller multi-role launch narrative in the benchmark report.\",\n            },\n        ],\n    }\n    return notes.get((scenario, dataset_family), [])"` |
| `benchmark_note_hook_source_line` | `134` | `209` |
| `benchmark_note_hook_source_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L134-L203"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_sessionization.py#L209-L278"` |
| `combiner` | `"plugins_service_latency.combine_values"` | `"plugins_sessionization.combine_values"` |
| `combiner_doc_summary` | `"Merge shard-local latency summaries before the final reduce step."` | `"Keep shard-local event batches JSON-safe before global sessionization."` |
| `combiner_source_anchor` | `"plugins_service_latency.py#L49-L51"` | `"plugins_sessionization.py#L65-L67"` |
| `combiner_source_commit_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_service_latency.py#L49-L51"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_sessionization.py#L65-L67"` |
| `combiner_source_excerpt` | `"def combine_values(_key, values):\n    \"\"\"Merge shard-local latency summaries before the final reduce step.\"\"\"\n    return _merge_latency_values(values)"` | `"def combine_values(_key, values):\n    \"\"\"Keep shard-local event batches JSON-safe before global sessionization.\"\"\"\n    return {\"events\": sorted(values, key=lambda event: event[\"timestamp\"])}"` |
| `combiner_source_line` | `49` | `65` |
| `combiner_source_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L49-L51"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_sessionization.py#L65-L67"` |
| `mapper` | `"plugins_service_latency.map_records"` | `"plugins_sessionization.map_records"` |
| `mapper_doc_summary` | `"Parse comma-separated service/latency rows into partial latency summaries."` | `"Emit per-user session events from comma-separated user,timestamp,page rows."` |
| `mapper_source_anchor` | `"plugins_service_latency.py#L33-L46"` | `"plugins_sessionization.py#L52-L62"` |
| `mapper_source_commit_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_service_latency.py#L33-L46"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_sessionization.py#L52-L62"` |
| `mapper_source_excerpt` | `"def map_records(lines):\n    \"\"\"Parse comma-separated service/latency rows into partial latency summaries.\"\"\"\n    for raw in lines:\n        stripped = raw.strip()\n        if not stripped:\n            continue\n        service, latency_ms = stripped.split(\",\", maxsplit=1)\n        latency_value = round(float(latency_ms.strip()), 3)\n        yield service.strip().lower(), {\n            \"count\": 1,\n            \"sum_ms\": latency_value,\n            \"max_ms\": latency_value,\n            \"samples_ms\": [latency_value],\n        }"` | `"def map_records(lines):\n    \"\"\"Emit per-user session events from comma-separated user,timestamp,page rows.\"\"\"\n    for raw in lines:\n        stripped = raw.strip()\n        if not stripped:\n            continue\n        user_id, timestamp, page = [part.strip() for part in stripped.split(\",\", maxsplit=2)]\n        yield user_id.lower(), {\n            \"timestamp\": _isoformat_z(_parse_timestamp(timestamp)),\n            \"page\": page,\n        }"` |
| `mapper_source_line` | `33` | `52` |
| `mapper_source_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L33-L46"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_sessionization.py#L52-L62"` |
| `module_doc_summary` | `"Service-latency summary plugin for observability-style benchmark demos."` | `"Sessionization analytics plugin for product-usage benchmark demos."` |
| `name` | `"plugin-service-latency"` | `"plugin-sessionization"` |
| `plugin` | `"projects/mini-mapreduce-lab/plugins_service_latency.py"` | `"projects/mini-mapreduce-lab/plugins_sessionization.py"` |
| `reducer` | `"plugins_service_latency.reduce_key"` | `"plugins_sessionization.reduce_key"` |
| `reducer_doc_summary` | `"Return count, average, p95, and max latency for one service key."` | `"Summarize session count, duration, and activity intensity for one user."` |
| `reducer_source_anchor` | `"plugins_service_latency.py#L54-L64"` | `"plugins_sessionization.py#L70-L91"` |
| `reducer_source_commit_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_service_latency.py#L54-L64"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_sessionization.py#L70-L91"` |
| `reducer_source_excerpt` | `"def reduce_key(_key, values):\n    \"\"\"Return count, average, p95, and max latency for one service key.\"\"\"\n    merged = _merge_latency_values(values)\n    count = int(merged[\"count\"])\n    average = round(float(merged[\"sum_ms\"]) / count, 3) if count else 0.0\n    return {\n        \"count\": count,\n        \"avg_ms\": average,\n        \"p95_ms\": _nearest_rank_percentile(merged[\"samples_ms\"], 95),\n        \"max_ms\": round(float(merged[\"max_ms\"]), 3),\n    }"` | `"def reduce_key(_key, values):\n    \"\"\"Summarize session count, duration, and activity intensity for one user.\"\"\"\n    merged = _merge_event_batches(values)\n    events = merged[\"events\"]\n    sessions = _session_summaries(events)\n    durations = []\n    for session in sessions:\n        start = _parse_timestamp(session[0][\"timestamp\"])\n        end = _parse_timestamp(session[-1][\"timestamp\"])\n        durations.append(round((end - start).total_seconds() / 60, 3))\n    total_events = len(events)\n    session_count = len(sessions)\n    return {\n        \"session_count\": session_count,\n        \"total_events\": total_events,\n        \"avg_events_per_session\": round(total_events / session_count, 3) if session_count else 0.0,\n        \"avg_session_minutes\": round(sum(durations) / session_count, 3) if session_count else 0.0,\n        \"longest_session_events\": max((len(session) for session in sessions), default=0),\n        \"longest_session_minutes\": max(durations, default=0.0),\n        \"first_event_at\": events[0][\"timestamp\"] if events else None,\n        \"last_event_at\": events[-1][\"timestamp\"] if events else None,\n    }"` |
| `reducer_source_line` | `54` | `70` |
| `reducer_source_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L54-L64"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_sessionization.py#L70-L91"` |

### Diff 4: `projects/mini-mapreduce-lab/plugins_sessionization.py` → `projects/mini-mapreduce-lab/plugins_streaming_window.py`
- Changed fields: `available_dataset_families, benchmark_generator, benchmark_generator_doc_summary, benchmark_generator_source_anchor, benchmark_generator_source_commit_url, benchmark_generator_source_excerpt, benchmark_generator_source_line, benchmark_generator_source_url, benchmark_note_hook, benchmark_note_hook_doc_summary, benchmark_note_hook_source_anchor, benchmark_note_hook_source_commit_url, benchmark_note_hook_source_excerpt, benchmark_note_hook_source_line, benchmark_note_hook_source_url, combiner, combiner_doc_summary, combiner_source_anchor, combiner_source_commit_url, combiner_source_excerpt, combiner_source_line, combiner_source_url, mapper, mapper_doc_summary, mapper_source_anchor, mapper_source_commit_url, mapper_source_excerpt, mapper_source_line, mapper_source_url, module_doc_summary, name, plugin, reducer, reducer_doc_summary, reducer_signature, reducer_source_anchor, reducer_source_commit_url, reducer_source_excerpt, reducer_source_line, reducer_source_url`

| Field | Previous | Current |
| --- | --- | --- |
| `available_dataset_families` | `["default", "exam-revision", "launch-day"]` | `["default", "iot-burst", "live-ops"]` |
| `benchmark_generator` | `"plugins_sessionization.benchmark_records"` | `"plugins_streaming_window.benchmark_records"` |
| `benchmark_generator_doc_summary` | `"Generate deterministic product-analytics event streams for sessionization demos."` | `"Generate deterministic windowed telemetry fixtures for benchmark scenarios."` |
| `benchmark_generator_source_anchor` | `"plugins_sessionization.py#L135-L206"` | `"plugins_streaming_window.py#L139-L212"` |
| `benchmark_generator_source_commit_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_sessionization.py#L135-L206"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_streaming_window.py#L139-L212"` |
| `benchmark_generator_source_excerpt` | `"def benchmark_records(scenario, records, seed, dataset_family=\"default\"):\n    \"\"\"Generate deterministic product-analytics event streams for sessionization demos.\"\"\"\n    if records <= 0:\n        raise ValueError(\"records must be positive\")\n    rng = random.Random(seed)\n    base_time = datetime(2026, 4, 17, 8, 0, tzinfo=timezone.utc)\n\n    families = {\n        \"default\": {\n            \"balanced\": [\n                {\"user\": \"student-alpha\", \"weight\": 1.0, \"session_size\": 3, \"session_gap\": 52, \"intra_gap\": 5, \"pages\": [\"home\", \"lecture-notes\", \"quiz\"]},\n                {\"user\": \"student-beta\", \"weight\": 1.0, \"session_size\": 3, \"session_gap\": 48, \"intra_gap\": 4, \"pages\": [\"home\", \"lab\", \"forum\"]},\n                {\"user\": \"student-gamma\", \"weight\": 1.0, \"session_size\": 4, \"session_gap\": 56, \"intra_gap\": 5, \"pages\": [\"home\", \"editor\", \"submissions\"]},\n                {\"user\": \"student-delta\", \"weight\": 1.0, \"session_size\": 3, \"session_gap\": 50, \"intra_gap\": 4, \"pages\": [\"home\", \"flashcards\", \"quiz\"]},\n            ],\n            \"skewed\": [\n                {\"user\": \"student-alpha\", \"weight\": 3.3, \"session_size\": 5, \"session_gap\": 38, \"intra_gap\": 4, \"pages\": [\"home\", \"lecture-notes\", \"quiz\", \"editor\"]},\n                {\"user\": \"student-beta\", \"weight\": 1.0, \"session_size\": 3, \"session_gap\": 55, \"intra_gap\": 5, \"pages\": [\"home\", \"lab\", \"forum\"]},\n                {\"user\": \"student-gamma\", \"weight\": 0.9, \"session_size\": 3, \"session_gap\": 58, \"intra_gap\": 5, \"pages\": [\"home\", \"editor\", \"submissions\"]},\n                {\"user\": \"student-delta\", \"weight\": 0.8, \"session_size\": 2, \"session_gap\": 62, \"intra_gap\": 6, \"pages\": [\"home\", \"flashcards\", \"quiz\"]},\n            ],\n        },\n        \"exam-revision\": {\n            \"balanced\": [\n                {\"user\": \"night-owl\", \"weight\": 1.1, \"session_size\": 4, \"session_gap\": 46, \"intra_gap\": 4, \"pages\": [\"review-guide\", \"quiz\", \"flashcards\"]},\n                {\"user\": \"lab-partner\", \"weight\": 1.0, \"session_size\": 3, \"session_gap\": 50, \"intra_gap\": 5, \"pages\": [\"practice-exam\", \"solutions\", \"forum\"]},\n                {\"user\": \"project-mate\", \"weight\": 1.0, \"session_size\": 3, \"session_gap\": 54, \"intra_gap\": 5, \"pages\": [\"review-guide\", \"editor\", \"submission\"]},\n                {\"user\": \"commuter\", \"weight\": 0.9, \"session_size\": 2, \"session_gap\": 58, \"intra_gap\": 6, \"pages\": [\"flashcards\", \"quiz\", \"summary\"]},\n            ],\n            \"skewed\": [\n                {\"user\": \"night-owl\", \"weight\": 3.8, \"session_size\": 6, \"session_gap\": 34, \"intra_gap\": 4, \"pages\": [\"review-guide\", \"quiz\", \"quiz-review\", \"flashcards\"]},\n                {\"user\": \"lab-partner\", \"weight\": 1.0, \"session_size\": 3, \"session_gap\": 52, \"intra_gap\": 5, \"pages\": [\"practice-exam\", \"solutions\", \"forum\"]},\n                {\"user\": \"project-mate\", \"weight\": 0.9, \"session_size\": 3, \"session_gap\": 56, \"intra_gap\": 5, \"pages\": [\"review-guide\", \"editor\", \"submission\"]},\n                {\"user\": \"commuter\", \"weight\": 0.7, \"session_size\": 2, \"session_gap\": 64, \"intra_gap\": 6, \"pages\": [\"flashcards\", \"quiz\", \"summary\"]},\n            ],\n        },\n        \"launch-day\": {\n            \"balanced\": [\n                {\"user\": \"release-lead\", \"weight\": 1.1, \"session_size\": 4, \"session_gap\": 42, \"intra_gap\": 4, \"pages\": [\"overview\", \"health\", \"errors\", \"deploy\"]},\n                {\"user\": \"qa-desk\", \"weight\": 1.0, \"session_size\": 3, \"session_gap\": 48, \"intra_gap\": 5, \"pages\": [\"smoke-tests\", \"errors\", \"feedback\"]},\n                {\"user\": \"support-ops\", \"weight\": 1.0, \"session_size\": 3, \"session_gap\": 50, \"intra_gap\": 5, \"pages\": [\"tickets\", \"feedback\", \"health\"]},\n                {\"user\": \"analytics-watch\", \"weight\": 0.9, \"session_size\": 3, \"session_gap\": 54, \"intra_gap\": 5, \"pages\": [\"overview\", \"conversion\", \"health\"]},\n            ],\n            \"skewed\": [\n                {\"user\": \"release-lead\", \"weight\": 4.0, \"session_size\": 6, \"session_gap\": 31, \"intra_gap\": 4, \"pages\": [\"overview\", \"health\", \"errors\", \"deploy\", \"rollback\"]},\n                {\"user\": \"qa-desk\", \"weight\": 1.1, \"session_size\": 4, \"session_gap\": 44, \"intra_gap\": 5, \"pages\": [\"smoke-tests\", \"errors\", \"feedback\"]},\n                {\"user\": \"support-ops\", \"weight\": 1.0, \"session_size\": 3, \"session_gap\": 50, \"intra_gap\": 5, \"pages\": [\"tickets\", \"feedback\", \"health\"]},\n                {\"user\": \"analytics-watch\", \"weight\": 0.8, \"session_size\": 2, \"session_gap\": 58, \"intra_gap\": 6, \"pages\": [\"overview\", \"conversion\", \"health\"]},\n            ],\n        },\n    }\n    if dataset_family not in families or scenario not in families[dataset_family]:\n        raise ValueError(f\"unsupported plugin benchmark scenario/family: {scenario}/{dataset_family}\")\n\n    profiles = families[dataset_family][scenario]\n    counts = _allocate_counts(records, [profile[\"weight\"] for profile in profiles])\n    events = []\n    for index, (profile, count) in enumerate(zip(profiles, counts)):\n        start_offset = timedelta(minutes=(index * 9) + rng.randint(0, 4))\n        events.extend(\n            _generate_user_events(\n                user=profile[\"user\"],\n                count=count,\n                start_at=base_time + start_offset,\n                session_size=profile[\"session_size\"],\n                session_gap_minutes=profile[\"session_gap\"] + rng.randint(-3, 3),\n                intra_gap_minutes=profile[\"intra_gap\"],\n                pages=profile[\"pages\"],\n            )\n        )\n    events.sort(key=lambda item: item[\"timestamp\"])\n    return [f\"{event['user']},{event['timestamp']},{event['page']}\" for event in events[:records]]"` | `"def benchmark_records(scenario, records, seed, dataset_family=\"default\"):\n    \"\"\"Generate deterministic windowed telemetry fixtures for benchmark scenarios.\"\"\"\n    if records <= 0:\n        raise ValueError(\"records must be positive\")\n    rng = random.Random(seed)\n    base_time = datetime(2026, 4, 17, 9, 0, tzinfo=timezone.utc)\n\n    families = {\n        \"default\": {\n            \"balanced\": [\n                {\"stream\": \"sensor-alpha\", \"weight\": 1.0, \"window_offsets\": [0, 5, 10, 15], \"base_value\": 21.5, \"spread\": 1.1, \"drift\": 0.3},\n                {\"stream\": \"sensor-beta\", \"weight\": 1.0, \"window_offsets\": [0, 5, 10, 15], \"base_value\": 23.2, \"spread\": 1.0, \"drift\": 0.2},\n                {\"stream\": \"sensor-gamma\", \"weight\": 1.0, \"window_offsets\": [0, 5, 10, 15], \"base_value\": 19.8, \"spread\": 1.2, \"drift\": 0.4},\n                {\"stream\": \"sensor-delta\", \"weight\": 1.0, \"window_offsets\": [0, 5, 10, 15], \"base_value\": 24.0, \"spread\": 1.1, \"drift\": 0.2},\n            ],\n            \"skewed\": [\n                {\"stream\": \"sensor-alpha\", \"weight\": 3.6, \"window_offsets\": [5, 5, 10], \"base_value\": 27.5, \"spread\": 1.4, \"drift\": 0.5, \"hotspot_offsets\": [5], \"hotspot_bonus\": 4.5},\n                {\"stream\": \"sensor-beta\", \"weight\": 1.0, \"window_offsets\": [0, 10, 15], \"base_value\": 23.0, \"spread\": 1.1, \"drift\": 0.2},\n                {\"stream\": \"sensor-gamma\", \"weight\": 0.9, \"window_offsets\": [0, 10, 15], \"base_value\": 20.1, \"spread\": 1.2, \"drift\": 0.3},\n                {\"stream\": \"sensor-delta\", \"weight\": 0.8, \"window_offsets\": [5, 15], \"base_value\": 22.7, \"spread\": 1.0, \"drift\": 0.3},\n            ],\n        },\n        \"iot-burst\": {\n            \"balanced\": [\n                {\"stream\": \"turnstile-east\", \"weight\": 1.1, \"window_offsets\": [5, 10, 15], \"base_value\": 31.0, \"spread\": 1.5, \"drift\": 0.6},\n                {\"stream\": \"camera-lobby\", \"weight\": 1.0, \"window_offsets\": [5, 10, 15], \"base_value\": 28.5, \"spread\": 1.3, \"drift\": 0.4},\n                {\"stream\": \"hvac-north\", \"weight\": 1.0, \"window_offsets\": [0, 10, 20], \"base_value\": 24.3, \"spread\": 1.0, \"drift\": 0.2},\n                {\"stream\": \"badge-reader\", \"weight\": 0.9, \"window_offsets\": [0, 5, 15], \"base_value\": 26.0, \"spread\": 1.1, \"drift\": 0.3},\n            ],\n            \"skewed\": [\n                {\"stream\": \"turnstile-east\", \"weight\": 4.2, \"window_offsets\": [10, 10, 15], \"base_value\": 36.0, \"spread\": 1.8, \"drift\": 0.8, \"hotspot_offsets\": [10], \"hotspot_bonus\": 14.0},\n                {\"stream\": \"camera-lobby\", \"weight\": 1.5, \"window_offsets\": [15, 15, 20], \"base_value\": 30.5, \"spread\": 1.5, \"drift\": 0.5, \"hotspot_offsets\": [15], \"hotspot_bonus\": 6.5},\n                {\"stream\": \"hvac-north\", \"weight\": 1.0, \"window_offsets\": [0, 10, 20], \"base_value\": 24.8, \"spread\": 1.0, \"drift\": 0.2},\n                {\"stream\": \"badge-reader\", \"weight\": 0.8, \"window_offsets\": [5, 20], \"base_value\": 26.4, \"spread\": 1.1, \"drift\": 0.3},\n            ],\n        },\n        \"live-ops\": {\n            \"balanced\": [\n                {\"stream\": \"ingest-primary\", \"weight\": 1.0, \"window_offsets\": [0, 5, 10, 15], \"base_value\": 42.0, \"spread\": 1.8, \"drift\": 0.7},\n                {\"stream\": \"chat-presence\", \"weight\": 1.0, \"window_offsets\": [0, 5, 10, 15], \"base_value\": 38.0, \"spread\": 1.6, \"drift\": 0.5},\n                {\"stream\": \"moderation-queue\", \"weight\": 1.0, \"window_offsets\": [0, 5, 10, 15], \"base_value\": 35.5, \"spread\": 1.4, \"drift\": 0.4},\n                {\"stream\": \"reaction-fanout\", \"weight\": 1.0, \"window_offsets\": [0, 5, 10, 15], \"base_value\": 39.0, \"spread\": 1.7, \"drift\": 0.6},\n            ],\n            \"skewed\": [\n                {\"stream\": \"moderation-queue\", \"weight\": 3.9, \"window_offsets\": [20, 20, 25], \"base_value\": 49.0, \"spread\": 2.1, \"drift\": 0.9, \"hotspot_offsets\": [20], \"hotspot_bonus\": 11.0},\n                {\"stream\": \"reaction-fanout\", \"weight\": 1.6, \"window_offsets\": [15, 15, 20], \"base_value\": 43.0, \"spread\": 1.8, \"drift\": 0.7, \"hotspot_offsets\": [15], \"hotspot_bonus\": 5.5},\n                {\"stream\": \"ingest-primary\", \"weight\": 1.0, \"window_offsets\": [0, 10, 20], \"base_value\": 41.5, \"spread\": 1.7, \"drift\": 0.5},\n                {\"stream\": \"chat-presence\", \"weight\": 0.9, \"window_offsets\": [5, 10, 25], \"base_value\": 37.6, \"spread\": 1.4, \"drift\": 0.4},\n            ],\n        },\n    }\n    if dataset_family not in families or scenario not in families[dataset_family]:\n        raise ValueError(f\"unsupported plugin benchmark scenario/family: {scenario}/{dataset_family}\")\n\n    profiles = families[dataset_family][scenario]\n    counts = _allocate_counts(records, [profile[\"weight\"] for profile in profiles])\n    lines = []\n    for profile, count in zip(profiles, counts):\n        lines.extend(\n            _generate_stream_events(\n                stream=profile[\"stream\"],\n                count=count,\n                base_time=base_time,\n                window_offsets=profile[\"window_offsets\"],\n                base_value=profile[\"base_value\"],\n                spread=profile[\"spread\"],\n                drift=profile[\"drift\"],\n                rng=rng,\n                hotspot_offsets=profile.get(\"hotspot_offsets\"),\n                hotspot_bonus=profile.get(\"hotspot_bonus\", 0.0),\n            )\n        )\n    lines.sort(key=lambda line: line.split(\",\", maxsplit=2)[1])\n    return lines[:records]"` |
| `benchmark_generator_source_line` | `135` | `139` |
| `benchmark_generator_source_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_sessionization.py#L135-L206"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_streaming_window.py#L139-L212"` |
| `benchmark_note_hook` | `"plugins_sessionization.benchmark_notes"` | `"plugins_streaming_window.benchmark_notes"` |
| `benchmark_note_hook_doc_summary` | `"Describe the intended hotspot users and browsing patterns for each family."` | `"Describe the intended hot windows and portfolio story for each family."` |
| `benchmark_note_hook_source_anchor` | `"plugins_sessionization.py#L209-L278"` | `"plugins_streaming_window.py#L215-L284"` |
| `benchmark_note_hook_source_commit_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_sessionization.py#L209-L278"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_streaming_window.py#L215-L284"` |
| `benchmark_note_hook_source_excerpt` | `"def benchmark_notes(scenario, dataset_family=\"default\"):\n    \"\"\"Describe the intended hotspot users and browsing patterns for each family.\"\"\"\n    notes = {\n        (\"balanced\", \"default\"): [\n            {\n                \"title\": \"Even study cadence\",\n                \"detail\": \"The default balanced family spreads activity across four students with similarly sized bursts, so reducer load should stay close while the output still demonstrates session boundaries.\",\n                \"severity\": \"info\",\n                \"takeaway\": \"Use this as the calm baseline before showing why repeated bursts from one user change the session story.\",\n            },\n        ],\n        (\"skewed\", \"default\"): [\n            {\n                \"title\": \"Student alpha cram loop\",\n                \"detail\": \"`student-alpha` revisits notes, quizzes, and the editor in repeated short bursts, so the hottest reducer should look like one user driving most session starts and events.\",\n                \"severity\": \"watch\",\n                \"hotspot_keys\": [\"student-alpha\"],\n                \"takeaway\": \"This is the simplest sessionization story for discussing hot users versus evenly distributed class traffic.\",\n            },\n        ],\n        (\"balanced\", \"exam-revision\"): [\n            {\n                \"title\": \"Shared review week\",\n                \"detail\": \"The balanced exam family keeps revision activity spread across multiple learners and shorter study sessions, which makes the session summaries read like a healthy pre-exam baseline.\",\n                \"severity\": \"info\",\n                \"takeaway\": \"Good for explaining why session counts alone are not enough without session length and event intensity.\",\n            },\n        ],\n        (\"skewed\", \"exam-revision\"): [\n            {\n                \"title\": \"Night-owl marathon\",\n                \"detail\": \"`night-owl` owns most of the benchmark volume here with repeated late-session bursts, so the reducer heatmap should show one learner dominating both activity and longest-session metrics.\",\n                \"severity\": \"risk\",\n                \"hotspot_keys\": [\"night-owl\"],\n                \"takeaway\": \"Call out how sessionization turns a raw clickstream into a workload story about sustained study behavior instead of isolated page hits.\",\n            },\n            {\n                \"title\": \"Commuter quick checks\",\n                \"detail\": \"`commuter` stays small and bursty, which makes it a useful low-priority contrast key when tightening the portfolio narrative down to the primary hotspot.\",\n                \"severity\": \"info\",\n                \"hotspot_keys\": [\"commuter\"],\n                \"takeaway\": \"This annotation is a good candidate to collapse in portfolio-tight reports.\",\n            },\n        ],\n        (\"balanced\", \"launch-day\"): [\n            {\n                \"title\": \"Coordinated launch monitoring\",\n                \"detail\": \"The balanced launch-day family keeps release, QA, support, and analytics roles close enough that the session summary reads like a calm release checklist instead of an incident.\",\n                \"severity\": \"info\",\n                \"takeaway\": \"Use this as the before state for the launch-day hotspot story.\",\n            },\n        ],\n        (\"skewed\", \"launch-day\"): [\n            {\n                \"title\": \"Release lead war room\",\n                \"detail\": \"`release-lead` dominates this family with back-to-back dashboard, deploy, and rollback visits, so the hottest reducer should look like one operator repeatedly re-entering a release war room.\",\n                \"severity\": \"risk\",\n                \"hotspot_keys\": [\"release-lead\"],\n                \"takeaway\": \"This turns the plugin into a product-analytics case study about launch-day behavior rather than generic score aggregation.\",\n            },\n            {\n                \"title\": \"QA desk verification loop\",\n                \"detail\": \"`qa-desk` forms a second-tier hotspot behind the release lead, which helps the report show supporting verification traffic instead of a single isolated key.\",\n                \"severity\": \"watch\",\n                \"hotspot_keys\": [\"qa-desk\"],\n                \"takeaway\": \"Keep this note when you want a fuller multi-role launch narrative in the benchmark report.\",\n            },\n        ],\n    }\n    return notes.get((scenario, dataset_family), [])"` | `"def benchmark_notes(scenario, dataset_family=\"default\"):\n    \"\"\"Describe the intended hot windows and portfolio story for each family.\"\"\"\n    notes = {\n        (\"balanced\", \"default\"): [\n            {\n                \"title\": \"Even telemetry cadence\",\n                \"detail\": \"The default balanced family spreads sensor updates across multiple windows and streams, so reducer load should stay close while still demonstrating time-bucket aggregation.\",\n                \"severity\": \"info\",\n                \"takeaway\": \"Use this as the calm baseline before introducing a window hotspot that is caused by workload shape rather than partitioning noise.\",\n            },\n        ],\n        (\"skewed\", \"default\"): [\n            {\n                \"title\": \"Sensor alpha window spike\",\n                \"detail\": \"`sensor-alpha@2026-04-17T09:05:00Z` is intentionally overweighted, so the hottest reducer should look like one telemetry stream concentrating most of its work into a single five-minute bucket.\",\n                \"severity\": \"watch\",\n                \"hotspot_keys\": [\"sensor-alpha@2026-04-17T09:05:00Z\"],\n                \"takeaway\": \"This is the simplest windowing story for explaining why time buckets can become hotspots even when the upstream stream names look balanced overall.\",\n            },\n        ],\n        (\"balanced\", \"iot-burst\"): [\n            {\n                \"title\": \"Staggered building telemetry\",\n                \"detail\": \"The balanced IoT family rotates turnstiles, cameras, HVAC, and badge readers across adjacent windows so the output reads like a healthy campus-building control loop.\",\n                \"severity\": \"info\",\n                \"takeaway\": \"Good for showing the plugin as a normal ops dashboard baseline before a rush-hour burst distorts one window.\",\n            },\n        ],\n        (\"skewed\", \"iot-burst\"): [\n            {\n                \"title\": \"Turnstile rush-hour burst\",\n                \"detail\": \"`turnstile-east@2026-04-17T09:10:00Z` dominates this family with both heavier volume and elevated values, so the hottest reducer should read like a lobby ingress spike during class changeover.\",\n                \"severity\": \"risk\",\n                \"hotspot_keys\": [\"turnstile-east@2026-04-17T09:10:00Z\"],\n                \"takeaway\": \"This turns the plugin into a windowed-streaming case study about burst concentration, not just generic per-key aggregation.\",\n            },\n            {\n                \"title\": \"Lobby camera spillover\",\n                \"detail\": \"`camera-lobby@2026-04-17T09:15:00Z` forms a second-tier hotspot right behind the turnstile window, which helps the benchmark tell a fuller story about adjacent systems reacting to the same surge.\",\n                \"severity\": \"watch\",\n                \"hotspot_keys\": [\"camera-lobby@2026-04-17T09:15:00Z\"],\n                \"takeaway\": \"Keep this note when you want the report to show cross-stream spillover instead of only the single biggest bucket.\",\n            },\n        ],\n        (\"balanced\", \"live-ops\"): [\n            {\n                \"title\": \"Steady live-ops baseline\",\n                \"detail\": \"The balanced live-ops family keeps ingest, presence, moderation, and fanout windows close enough that the report reads like a normal event stream instead of a launch incident.\",\n                \"severity\": \"info\",\n                \"takeaway\": \"Use this as the before state for the live moderation surge story.\",\n            },\n        ],\n        (\"skewed\", \"live-ops\"): [\n            {\n                \"title\": \"Moderation queue pile-up\",\n                \"detail\": \"`moderation-queue@2026-04-17T09:20:00Z` becomes the obvious hotspot here, so the window summary looks like one burst of chat events overwhelming moderation capacity during a live launch.\",\n                \"severity\": \"risk\",\n                \"hotspot_keys\": [\"moderation-queue@2026-04-17T09:20:00Z\"],\n                \"takeaway\": \"This family is useful when you want a streaming-systems narrative about time-bucket pressure rather than user sessions or service latency.\",\n            },\n            {\n                \"title\": \"Reaction fanout echo\",\n                \"detail\": \"`reaction-fanout@2026-04-17T09:15:00Z` is the supporting hotspot behind moderation, which helps explain how bursty audience behavior can surface in multiple downstream windows.\",\n                \"severity\": \"watch\",\n                \"hotspot_keys\": [\"reaction-fanout@2026-04-17T09:15:00Z\"],\n                \"takeaway\": \"Keep this annotation when you want the benchmark to tell a richer multi-stage streaming pipeline story.\",\n            },\n        ],\n    }\n    return notes.get((scenario, dataset_family), [])"` |
| `benchmark_note_hook_source_line` | `209` | `215` |
| `benchmark_note_hook_source_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_sessionization.py#L209-L278"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_streaming_window.py#L215-L284"` |
| `combiner` | `"plugins_sessionization.combine_values"` | `"plugins_streaming_window.combine_values"` |
| `combiner_doc_summary` | `"Keep shard-local event batches JSON-safe before global sessionization."` | `"Merge shard-local window summaries before the final reduce step."` |
| `combiner_source_anchor` | `"plugins_sessionization.py#L65-L67"` | `"plugins_streaming_window.py#L93-L95"` |
| `combiner_source_commit_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_sessionization.py#L65-L67"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_streaming_window.py#L93-L95"` |
| `combiner_source_excerpt` | `"def combine_values(_key, values):\n    \"\"\"Keep shard-local event batches JSON-safe before global sessionization.\"\"\"\n    return {\"events\": sorted(values, key=lambda event: event[\"timestamp\"])}"` | `"def combine_values(_key, values):\n    \"\"\"Merge shard-local window summaries before the final reduce step.\"\"\"\n    return _merge_window_values(values)"` |
| `combiner_source_line` | `65` | `93` |
| `combiner_source_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_sessionization.py#L65-L67"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_streaming_window.py#L93-L95"` |
| `mapper` | `"plugins_sessionization.map_records"` | `"plugins_streaming_window.map_records"` |
| `mapper_doc_summary` | `"Emit per-user session events from comma-separated user,timestamp,page rows."` | `"Emit per-stream, per-window summary objects from stream,timestamp,value rows."` |
| `mapper_source_anchor` | `"plugins_sessionization.py#L52-L62"` | `"plugins_streaming_window.py#L73-L90"` |
| `mapper_source_commit_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_sessionization.py#L52-L62"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_streaming_window.py#L73-L90"` |
| `mapper_source_excerpt` | `"def map_records(lines):\n    \"\"\"Emit per-user session events from comma-separated user,timestamp,page rows.\"\"\"\n    for raw in lines:\n        stripped = raw.strip()\n        if not stripped:\n            continue\n        user_id, timestamp, page = [part.strip() for part in stripped.split(\",\", maxsplit=2)]\n        yield user_id.lower(), {\n            \"timestamp\": _isoformat_z(_parse_timestamp(timestamp)),\n            \"page\": page,\n        }"` | `"def map_records(lines):\n    \"\"\"Emit per-stream, per-window summary objects from stream,timestamp,value rows.\"\"\"\n    for raw in lines:\n        stripped = raw.strip()\n        if not stripped:\n            continue\n        stream, timestamp, value = [part.strip() for part in stripped.split(\",\", maxsplit=2)]\n        parsed_timestamp = _parse_timestamp(timestamp)\n        window_start = _window_start(parsed_timestamp)\n        numeric_value = round(float(value), 3)\n        yield f\"{stream.lower()}@{_isoformat_z(window_start)}\", {\n            \"count\": 1,\n            \"sum\": numeric_value,\n            \"min\": numeric_value,\n            \"max\": numeric_value,\n            \"first_event_at\": _isoformat_z(parsed_timestamp),\n            \"last_event_at\": _isoformat_z(parsed_timestamp),\n        }"` |
| `mapper_source_line` | `52` | `73` |
| `mapper_source_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_sessionization.py#L52-L62"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_streaming_window.py#L73-L90"` |
| `module_doc_summary` | `"Sessionization analytics plugin for product-usage benchmark demos."` | `"Streaming-window aggregation plugin for telemetry-style benchmark demos."` |
| `name` | `"plugin-sessionization"` | `"plugin-streaming-window"` |
| `plugin` | `"projects/mini-mapreduce-lab/plugins_sessionization.py"` | `"projects/mini-mapreduce-lab/plugins_streaming_window.py"` |
| `reducer` | `"plugins_sessionization.reduce_key"` | `"plugins_streaming_window.reduce_key"` |
| `reducer_doc_summary` | `"Summarize session count, duration, and activity intensity for one user."` | `"Return window-level count, range, and rate metrics for one stream bucket."` |
| `reducer_signature` | `"reduce_key(_key, values)"` | `"reduce_key(key, values)"` |
| `reducer_source_anchor` | `"plugins_sessionization.py#L70-L91"` | `"plugins_streaming_window.py#L98-L123"` |
| `reducer_source_commit_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_sessionization.py#L70-L91"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_streaming_window.py#L98-L123"` |
| `reducer_source_excerpt` | `"def reduce_key(_key, values):\n    \"\"\"Summarize session count, duration, and activity intensity for one user.\"\"\"\n    merged = _merge_event_batches(values)\n    events = merged[\"events\"]\n    sessions = _session_summaries(events)\n    durations = []\n    for session in sessions:\n        start = _parse_timestamp(session[0][\"timestamp\"])\n        end = _parse_timestamp(session[-1][\"timestamp\"])\n        durations.append(round((end - start).total_seconds() / 60, 3))\n    total_events = len(events)\n    session_count = len(sessions)\n    return {\n        \"session_count\": session_count,\n        \"total_events\": total_events,\n        \"avg_events_per_session\": round(total_events / session_count, 3) if session_count else 0.0,\n        \"avg_session_minutes\": round(sum(durations) / session_count, 3) if session_count else 0.0,\n        \"longest_session_events\": max((len(session) for session in sessions), default=0),\n        \"longest_session_minutes\": max(durations, default=0.0),\n        \"first_event_at\": events[0][\"timestamp\"] if events else None,\n        \"last_event_at\": events[-1][\"timestamp\"] if events else None,\n    }"` | `"def reduce_key(key, values):\n    \"\"\"Return window-level count, range, and rate metrics for one stream bucket.\"\"\"\n    stream, window_start = _split_window_key(key)\n    merged = _merge_window_values(values)\n    count = int(merged[\"count\"])\n    first_event_at = merged[\"first_event_at\"]\n    last_event_at = merged[\"last_event_at\"]\n    span_minutes = 0.0\n    if first_event_at and last_event_at:\n        span_minutes = round(\n            (_parse_timestamp(last_event_at) - _parse_timestamp(first_event_at)).total_seconds() / 60,\n            3,\n        )\n    return {\n        \"stream\": stream,\n        \"window_start\": window_start,\n        \"window_end\": _isoformat_z(_parse_timestamp(window_start) + timedelta(minutes=WINDOW_MINUTES)),\n        \"count\": count,\n        \"avg_value\": round(float(merged[\"sum\"]) / count, 3) if count else 0.0,\n        \"min_value\": round(float(merged[\"min\"]), 3) if count else 0.0,\n        \"max_value\": round(float(merged[\"max\"]), 3) if count else 0.0,\n        \"event_rate_per_minute\": round(count / WINDOW_MINUTES, 3) if count else 0.0,\n        \"first_event_at\": first_event_at,\n        \"last_event_at\": last_event_at,\n        \"span_minutes\": span_minutes,\n    }"` |
| `reducer_source_line` | `70` | `98` |
| `reducer_source_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_sessionization.py#L70-L91"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_streaming_window.py#L98-L123"` |

### Diff 5: `projects/mini-mapreduce-lab/plugins_streaming_window.py` → `projects/mini-mapreduce-lab/plugins_top_score.py`
- Changed fields: `available_dataset_families, benchmark_generator, benchmark_generator_doc_summary, benchmark_generator_signature, benchmark_generator_source_anchor, benchmark_generator_source_commit_url, benchmark_generator_source_excerpt, benchmark_generator_source_line, benchmark_generator_source_url, benchmark_note_hook, benchmark_note_hook_doc_summary, benchmark_note_hook_signature, benchmark_note_hook_source_anchor, benchmark_note_hook_source_commit_url, benchmark_note_hook_source_excerpt, benchmark_note_hook_source_line, benchmark_note_hook_source_url, combiner, combiner_doc_summary, combiner_source_anchor, combiner_source_commit_url, combiner_source_excerpt, combiner_source_line, combiner_source_url, mapper, mapper_doc_summary, mapper_source_anchor, mapper_source_commit_url, mapper_source_excerpt, mapper_source_line, mapper_source_url, module_doc_summary, name, plugin, reducer, reducer_doc_summary, reducer_signature, reducer_source_anchor, reducer_source_commit_url, reducer_source_excerpt, reducer_source_line, reducer_source_url`

| Field | Previous | Current |
| --- | --- | --- |
| `available_dataset_families` | `["default", "iot-burst", "live-ops"]` | `null` |
| `benchmark_generator` | `"plugins_streaming_window.benchmark_records"` | `null` |
| `benchmark_generator_doc_summary` | `"Generate deterministic windowed telemetry fixtures for benchmark scenarios."` | `null` |
| `benchmark_generator_signature` | `"benchmark_records(scenario, records, seed, dataset_family='default')"` | `null` |
| `benchmark_generator_source_anchor` | `"plugins_streaming_window.py#L139-L212"` | `null` |
| `benchmark_generator_source_commit_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_streaming_window.py#L139-L212"` | `null` |
| `benchmark_generator_source_excerpt` | `"def benchmark_records(scenario, records, seed, dataset_family=\"default\"):\n    \"\"\"Generate deterministic windowed telemetry fixtures for benchmark scenarios.\"\"\"\n    if records <= 0:\n        raise ValueError(\"records must be positive\")\n    rng = random.Random(seed)\n    base_time = datetime(2026, 4, 17, 9, 0, tzinfo=timezone.utc)\n\n    families = {\n        \"default\": {\n            \"balanced\": [\n                {\"stream\": \"sensor-alpha\", \"weight\": 1.0, \"window_offsets\": [0, 5, 10, 15], \"base_value\": 21.5, \"spread\": 1.1, \"drift\": 0.3},\n                {\"stream\": \"sensor-beta\", \"weight\": 1.0, \"window_offsets\": [0, 5, 10, 15], \"base_value\": 23.2, \"spread\": 1.0, \"drift\": 0.2},\n                {\"stream\": \"sensor-gamma\", \"weight\": 1.0, \"window_offsets\": [0, 5, 10, 15], \"base_value\": 19.8, \"spread\": 1.2, \"drift\": 0.4},\n                {\"stream\": \"sensor-delta\", \"weight\": 1.0, \"window_offsets\": [0, 5, 10, 15], \"base_value\": 24.0, \"spread\": 1.1, \"drift\": 0.2},\n            ],\n            \"skewed\": [\n                {\"stream\": \"sensor-alpha\", \"weight\": 3.6, \"window_offsets\": [5, 5, 10], \"base_value\": 27.5, \"spread\": 1.4, \"drift\": 0.5, \"hotspot_offsets\": [5], \"hotspot_bonus\": 4.5},\n                {\"stream\": \"sensor-beta\", \"weight\": 1.0, \"window_offsets\": [0, 10, 15], \"base_value\": 23.0, \"spread\": 1.1, \"drift\": 0.2},\n                {\"stream\": \"sensor-gamma\", \"weight\": 0.9, \"window_offsets\": [0, 10, 15], \"base_value\": 20.1, \"spread\": 1.2, \"drift\": 0.3},\n                {\"stream\": \"sensor-delta\", \"weight\": 0.8, \"window_offsets\": [5, 15], \"base_value\": 22.7, \"spread\": 1.0, \"drift\": 0.3},\n            ],\n        },\n        \"iot-burst\": {\n            \"balanced\": [\n                {\"stream\": \"turnstile-east\", \"weight\": 1.1, \"window_offsets\": [5, 10, 15], \"base_value\": 31.0, \"spread\": 1.5, \"drift\": 0.6},\n                {\"stream\": \"camera-lobby\", \"weight\": 1.0, \"window_offsets\": [5, 10, 15], \"base_value\": 28.5, \"spread\": 1.3, \"drift\": 0.4},\n                {\"stream\": \"hvac-north\", \"weight\": 1.0, \"window_offsets\": [0, 10, 20], \"base_value\": 24.3, \"spread\": 1.0, \"drift\": 0.2},\n                {\"stream\": \"badge-reader\", \"weight\": 0.9, \"window_offsets\": [0, 5, 15], \"base_value\": 26.0, \"spread\": 1.1, \"drift\": 0.3},\n            ],\n            \"skewed\": [\n                {\"stream\": \"turnstile-east\", \"weight\": 4.2, \"window_offsets\": [10, 10, 15], \"base_value\": 36.0, \"spread\": 1.8, \"drift\": 0.8, \"hotspot_offsets\": [10], \"hotspot_bonus\": 14.0},\n                {\"stream\": \"camera-lobby\", \"weight\": 1.5, \"window_offsets\": [15, 15, 20], \"base_value\": 30.5, \"spread\": 1.5, \"drift\": 0.5, \"hotspot_offsets\": [15], \"hotspot_bonus\": 6.5},\n                {\"stream\": \"hvac-north\", \"weight\": 1.0, \"window_offsets\": [0, 10, 20], \"base_value\": 24.8, \"spread\": 1.0, \"drift\": 0.2},\n                {\"stream\": \"badge-reader\", \"weight\": 0.8, \"window_offsets\": [5, 20], \"base_value\": 26.4, \"spread\": 1.1, \"drift\": 0.3},\n            ],\n        },\n        \"live-ops\": {\n            \"balanced\": [\n                {\"stream\": \"ingest-primary\", \"weight\": 1.0, \"window_offsets\": [0, 5, 10, 15], \"base_value\": 42.0, \"spread\": 1.8, \"drift\": 0.7},\n                {\"stream\": \"chat-presence\", \"weight\": 1.0, \"window_offsets\": [0, 5, 10, 15], \"base_value\": 38.0, \"spread\": 1.6, \"drift\": 0.5},\n                {\"stream\": \"moderation-queue\", \"weight\": 1.0, \"window_offsets\": [0, 5, 10, 15], \"base_value\": 35.5, \"spread\": 1.4, \"drift\": 0.4},\n                {\"stream\": \"reaction-fanout\", \"weight\": 1.0, \"window_offsets\": [0, 5, 10, 15], \"base_value\": 39.0, \"spread\": 1.7, \"drift\": 0.6},\n            ],\n            \"skewed\": [\n                {\"stream\": \"moderation-queue\", \"weight\": 3.9, \"window_offsets\": [20, 20, 25], \"base_value\": 49.0, \"spread\": 2.1, \"drift\": 0.9, \"hotspot_offsets\": [20], \"hotspot_bonus\": 11.0},\n                {\"stream\": \"reaction-fanout\", \"weight\": 1.6, \"window_offsets\": [15, 15, 20], \"base_value\": 43.0, \"spread\": 1.8, \"drift\": 0.7, \"hotspot_offsets\": [15], \"hotspot_bonus\": 5.5},\n                {\"stream\": \"ingest-primary\", \"weight\": 1.0, \"window_offsets\": [0, 10, 20], \"base_value\": 41.5, \"spread\": 1.7, \"drift\": 0.5},\n                {\"stream\": \"chat-presence\", \"weight\": 0.9, \"window_offsets\": [5, 10, 25], \"base_value\": 37.6, \"spread\": 1.4, \"drift\": 0.4},\n            ],\n        },\n    }\n    if dataset_family not in families or scenario not in families[dataset_family]:\n        raise ValueError(f\"unsupported plugin benchmark scenario/family: {scenario}/{dataset_family}\")\n\n    profiles = families[dataset_family][scenario]\n    counts = _allocate_counts(records, [profile[\"weight\"] for profile in profiles])\n    lines = []\n    for profile, count in zip(profiles, counts):\n        lines.extend(\n            _generate_stream_events(\n                stream=profile[\"stream\"],\n                count=count,\n                base_time=base_time,\n                window_offsets=profile[\"window_offsets\"],\n                base_value=profile[\"base_value\"],\n                spread=profile[\"spread\"],\n                drift=profile[\"drift\"],\n                rng=rng,\n                hotspot_offsets=profile.get(\"hotspot_offsets\"),\n                hotspot_bonus=profile.get(\"hotspot_bonus\", 0.0),\n            )\n        )\n    lines.sort(key=lambda line: line.split(\",\", maxsplit=2)[1])\n    return lines[:records]"` | `null` |
| `benchmark_generator_source_line` | `139` | `null` |
| `benchmark_generator_source_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_streaming_window.py#L139-L212"` | `null` |
| `benchmark_note_hook` | `"plugins_streaming_window.benchmark_notes"` | `null` |
| `benchmark_note_hook_doc_summary` | `"Describe the intended hot windows and portfolio story for each family."` | `null` |
| `benchmark_note_hook_signature` | `"benchmark_notes(scenario, dataset_family='default')"` | `null` |
| `benchmark_note_hook_source_anchor` | `"plugins_streaming_window.py#L215-L284"` | `null` |
| `benchmark_note_hook_source_commit_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_streaming_window.py#L215-L284"` | `null` |
| `benchmark_note_hook_source_excerpt` | `"def benchmark_notes(scenario, dataset_family=\"default\"):\n    \"\"\"Describe the intended hot windows and portfolio story for each family.\"\"\"\n    notes = {\n        (\"balanced\", \"default\"): [\n            {\n                \"title\": \"Even telemetry cadence\",\n                \"detail\": \"The default balanced family spreads sensor updates across multiple windows and streams, so reducer load should stay close while still demonstrating time-bucket aggregation.\",\n                \"severity\": \"info\",\n                \"takeaway\": \"Use this as the calm baseline before introducing a window hotspot that is caused by workload shape rather than partitioning noise.\",\n            },\n        ],\n        (\"skewed\", \"default\"): [\n            {\n                \"title\": \"Sensor alpha window spike\",\n                \"detail\": \"`sensor-alpha@2026-04-17T09:05:00Z` is intentionally overweighted, so the hottest reducer should look like one telemetry stream concentrating most of its work into a single five-minute bucket.\",\n                \"severity\": \"watch\",\n                \"hotspot_keys\": [\"sensor-alpha@2026-04-17T09:05:00Z\"],\n                \"takeaway\": \"This is the simplest windowing story for explaining why time buckets can become hotspots even when the upstream stream names look balanced overall.\",\n            },\n        ],\n        (\"balanced\", \"iot-burst\"): [\n            {\n                \"title\": \"Staggered building telemetry\",\n                \"detail\": \"The balanced IoT family rotates turnstiles, cameras, HVAC, and badge readers across adjacent windows so the output reads like a healthy campus-building control loop.\",\n                \"severity\": \"info\",\n                \"takeaway\": \"Good for showing the plugin as a normal ops dashboard baseline before a rush-hour burst distorts one window.\",\n            },\n        ],\n        (\"skewed\", \"iot-burst\"): [\n            {\n                \"title\": \"Turnstile rush-hour burst\",\n                \"detail\": \"`turnstile-east@2026-04-17T09:10:00Z` dominates this family with both heavier volume and elevated values, so the hottest reducer should read like a lobby ingress spike during class changeover.\",\n                \"severity\": \"risk\",\n                \"hotspot_keys\": [\"turnstile-east@2026-04-17T09:10:00Z\"],\n                \"takeaway\": \"This turns the plugin into a windowed-streaming case study about burst concentration, not just generic per-key aggregation.\",\n            },\n            {\n                \"title\": \"Lobby camera spillover\",\n                \"detail\": \"`camera-lobby@2026-04-17T09:15:00Z` forms a second-tier hotspot right behind the turnstile window, which helps the benchmark tell a fuller story about adjacent systems reacting to the same surge.\",\n                \"severity\": \"watch\",\n                \"hotspot_keys\": [\"camera-lobby@2026-04-17T09:15:00Z\"],\n                \"takeaway\": \"Keep this note when you want the report to show cross-stream spillover instead of only the single biggest bucket.\",\n            },\n        ],\n        (\"balanced\", \"live-ops\"): [\n            {\n                \"title\": \"Steady live-ops baseline\",\n                \"detail\": \"The balanced live-ops family keeps ingest, presence, moderation, and fanout windows close enough that the report reads like a normal event stream instead of a launch incident.\",\n                \"severity\": \"info\",\n                \"takeaway\": \"Use this as the before state for the live moderation surge story.\",\n            },\n        ],\n        (\"skewed\", \"live-ops\"): [\n            {\n                \"title\": \"Moderation queue pile-up\",\n                \"detail\": \"`moderation-queue@2026-04-17T09:20:00Z` becomes the obvious hotspot here, so the window summary looks like one burst of chat events overwhelming moderation capacity during a live launch.\",\n                \"severity\": \"risk\",\n                \"hotspot_keys\": [\"moderation-queue@2026-04-17T09:20:00Z\"],\n                \"takeaway\": \"This family is useful when you want a streaming-systems narrative about time-bucket pressure rather than user sessions or service latency.\",\n            },\n            {\n                \"title\": \"Reaction fanout echo\",\n                \"detail\": \"`reaction-fanout@2026-04-17T09:15:00Z` is the supporting hotspot behind moderation, which helps explain how bursty audience behavior can surface in multiple downstream windows.\",\n                \"severity\": \"watch\",\n                \"hotspot_keys\": [\"reaction-fanout@2026-04-17T09:15:00Z\"],\n                \"takeaway\": \"Keep this annotation when you want the benchmark to tell a richer multi-stage streaming pipeline story.\",\n            },\n        ],\n    }\n    return notes.get((scenario, dataset_family), [])"` | `null` |
| `benchmark_note_hook_source_line` | `215` | `null` |
| `benchmark_note_hook_source_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_streaming_window.py#L215-L284"` | `null` |
| `combiner` | `"plugins_streaming_window.combine_values"` | `"plugins_top_score.combine_values"` |
| `combiner_doc_summary` | `"Merge shard-local window summaries before the final reduce step."` | `"Keep the shard-local maximum score for one student key."` |
| `combiner_source_anchor` | `"plugins_streaming_window.py#L93-L95"` | `"plugins_top_score.py#L16-L18"` |
| `combiner_source_commit_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_streaming_window.py#L93-L95"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_top_score.py#L16-L18"` |
| `combiner_source_excerpt` | `"def combine_values(_key, values):\n    \"\"\"Merge shard-local window summaries before the final reduce step.\"\"\"\n    return _merge_window_values(values)"` | `"def combine_values(_key, values):\n    \"\"\"Keep the shard-local maximum score for one student key.\"\"\"\n    return max(values)"` |
| `combiner_source_line` | `93` | `16` |
| `combiner_source_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_streaming_window.py#L93-L95"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_top_score.py#L16-L18"` |
| `mapper` | `"plugins_streaming_window.map_records"` | `"plugins_top_score.map_records"` |
| `mapper_doc_summary` | `"Emit per-stream, per-window summary objects from stream,timestamp,value rows."` | `"Parse comma-separated score rows into integer leaderboard updates."` |
| `mapper_source_anchor` | `"plugins_streaming_window.py#L73-L90"` | `"plugins_top_score.py#L6-L13"` |
| `mapper_source_commit_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_streaming_window.py#L73-L90"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_top_score.py#L6-L13"` |
| `mapper_source_excerpt` | `"def map_records(lines):\n    \"\"\"Emit per-stream, per-window summary objects from stream,timestamp,value rows.\"\"\"\n    for raw in lines:\n        stripped = raw.strip()\n        if not stripped:\n            continue\n        stream, timestamp, value = [part.strip() for part in stripped.split(\",\", maxsplit=2)]\n        parsed_timestamp = _parse_timestamp(timestamp)\n        window_start = _window_start(parsed_timestamp)\n        numeric_value = round(float(value), 3)\n        yield f\"{stream.lower()}@{_isoformat_z(window_start)}\", {\n            \"count\": 1,\n            \"sum\": numeric_value,\n            \"min\": numeric_value,\n            \"max\": numeric_value,\n            \"first_event_at\": _isoformat_z(parsed_timestamp),\n            \"last_event_at\": _isoformat_z(parsed_timestamp),\n        }"` | `"def map_records(lines):\n    \"\"\"Parse comma-separated score rows into integer leaderboard updates.\"\"\"\n    for raw in lines:\n        stripped = raw.strip()\n        if not stripped:\n            continue\n        name, score = stripped.split(\",\", maxsplit=1)\n        yield name.strip().lower(), int(score.strip())"` |
| `mapper_source_line` | `73` | `6` |
| `mapper_source_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_streaming_window.py#L73-L90"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_top_score.py#L6-L13"` |
| `module_doc_summary` | `"Streaming-window aggregation plugin for telemetry-style benchmark demos."` | `"Maximum-score reducer plugin for simple leaderboard-style demos."` |
| `name` | `"plugin-streaming-window"` | `"plugin-max-score"` |
| `plugin` | `"projects/mini-mapreduce-lab/plugins_streaming_window.py"` | `"projects/mini-mapreduce-lab/plugins_top_score.py"` |
| `reducer` | `"plugins_streaming_window.reduce_key"` | `"plugins_top_score.reduce_key"` |
| `reducer_doc_summary` | `"Return window-level count, range, and rate metrics for one stream bucket."` | `"Return the overall maximum score for one student key."` |
| `reducer_signature` | `"reduce_key(key, values)"` | `"reduce_key(_key, values)"` |
| `reducer_source_anchor` | `"plugins_streaming_window.py#L98-L123"` | `"plugins_top_score.py#L21-L23"` |
| `reducer_source_commit_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_streaming_window.py#L98-L123"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_top_score.py#L21-L23"` |
| `reducer_source_excerpt` | `"def reduce_key(key, values):\n    \"\"\"Return window-level count, range, and rate metrics for one stream bucket.\"\"\"\n    stream, window_start = _split_window_key(key)\n    merged = _merge_window_values(values)\n    count = int(merged[\"count\"])\n    first_event_at = merged[\"first_event_at\"]\n    last_event_at = merged[\"last_event_at\"]\n    span_minutes = 0.0\n    if first_event_at and last_event_at:\n        span_minutes = round(\n            (_parse_timestamp(last_event_at) - _parse_timestamp(first_event_at)).total_seconds() / 60,\n            3,\n        )\n    return {\n        \"stream\": stream,\n        \"window_start\": window_start,\n        \"window_end\": _isoformat_z(_parse_timestamp(window_start) + timedelta(minutes=WINDOW_MINUTES)),\n        \"count\": count,\n        \"avg_value\": round(float(merged[\"sum\"]) / count, 3) if count else 0.0,\n        \"min_value\": round(float(merged[\"min\"]), 3) if count else 0.0,\n        \"max_value\": round(float(merged[\"max\"]), 3) if count else 0.0,\n        \"event_rate_per_minute\": round(count / WINDOW_MINUTES, 3) if count else 0.0,\n        \"first_event_at\": first_event_at,\n        \"last_event_at\": last_event_at,\n        \"span_minutes\": span_minutes,\n    }"` | `"def reduce_key(_key, values):\n    \"\"\"Return the overall maximum score for one student key.\"\"\"\n    return max(values)"` |
| `reducer_source_line` | `98` | `21` |
| `reducer_source_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_streaming_window.py#L98-L123"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_top_score.py#L21-L23"` |

### Diff 6: `projects/mini-mapreduce-lab/plugins_top_score.py` → `projects/mini-mapreduce-lab/plugins_watermark_late_summary.py`
- Changed fields: `available_dataset_families, benchmark_generator, benchmark_generator_doc_summary, benchmark_generator_signature, benchmark_generator_source_anchor, benchmark_generator_source_commit_url, benchmark_generator_source_excerpt, benchmark_generator_source_line, benchmark_generator_source_url, benchmark_note_hook, benchmark_note_hook_doc_summary, benchmark_note_hook_signature, benchmark_note_hook_source_anchor, benchmark_note_hook_source_commit_url, benchmark_note_hook_source_excerpt, benchmark_note_hook_source_line, benchmark_note_hook_source_url, combiner, combiner_doc_summary, combiner_source_anchor, combiner_source_commit_url, combiner_source_excerpt, combiner_source_line, combiner_source_url, mapper, mapper_doc_summary, mapper_source_anchor, mapper_source_commit_url, mapper_source_excerpt, mapper_source_line, mapper_source_url, module_doc_summary, name, plugin, reducer, reducer_doc_summary, reducer_signature, reducer_source_anchor, reducer_source_commit_url, reducer_source_excerpt, reducer_source_line, reducer_source_url`

| Field | Previous | Current |
| --- | --- | --- |
| `available_dataset_families` | `null` | `["default", "sensor-backfill", "live-replay"]` |
| `benchmark_generator` | `null` | `"plugins_watermark_late_summary.benchmark_records"` |
| `benchmark_generator_doc_summary` | `null` | `"Generate deterministic out-of-order event streams for watermark-summary demos."` |
| `benchmark_generator_signature` | `null` | `"benchmark_records(scenario, records, seed, dataset_family='default')"` |
| `benchmark_generator_source_anchor` | `null` | `"plugins_watermark_late_summary.py#L266-L341"` |
| `benchmark_generator_source_commit_url` | `null` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L266-L341"` |
| `benchmark_generator_source_excerpt` | `null` | `"def benchmark_records(scenario, records, seed, dataset_family=\"default\"):\n    \"\"\"Generate deterministic out-of-order event streams for watermark-summary demos.\"\"\"\n    if records <= 0:\n        raise ValueError(\"records must be positive\")\n    rng = random.Random(seed)\n    base_time = datetime(2026, 4, 17, 9, 0, tzinfo=timezone.utc)\n\n    families = {\n        \"default\": {\n            \"balanced\": [\n                {\"stream\": \"sensor-alpha\", \"weight\": 1.0, \"window_offsets\": [0, 5, 10], \"base_value\": 20.5, \"spread\": 0.9, \"drift\": 0.2, \"late_offsets\": [5]},\n                {\"stream\": \"sensor-beta\", \"weight\": 1.0, \"window_offsets\": [0, 10, 15], \"base_value\": 22.0, \"spread\": 1.0, \"drift\": 0.2, \"late_offsets\": [10]},\n                {\"stream\": \"sensor-gamma\", \"weight\": 1.0, \"window_offsets\": [5, 10, 15], \"base_value\": 19.4, \"spread\": 0.8, \"drift\": 0.2, \"late_offsets\": [5]},\n                {\"stream\": \"sensor-delta\", \"weight\": 1.0, \"window_offsets\": [0, 5, 15], \"base_value\": 21.2, \"spread\": 0.9, \"drift\": 0.1},\n            ],\n            \"skewed\": [\n                {\"stream\": \"sensor-alpha\", \"weight\": 3.6, \"window_offsets\": [5, 10, 10], \"base_value\": 25.6, \"spread\": 1.2, \"drift\": 0.4, \"late_offsets\": [5, 10], \"drop_offsets\": [5], \"hotspot_offsets\": [10], \"hotspot_bonus\": 3.8},\n                {\"stream\": \"sensor-beta\", \"weight\": 1.0, \"window_offsets\": [0, 10, 15], \"base_value\": 22.4, \"spread\": 0.9, \"drift\": 0.2, \"late_offsets\": [10]},\n                {\"stream\": \"sensor-gamma\", \"weight\": 0.9, \"window_offsets\": [0, 5, 15], \"base_value\": 19.8, \"spread\": 0.8, \"drift\": 0.1},\n                {\"stream\": \"sensor-delta\", \"weight\": 0.8, \"window_offsets\": [5, 15, 20], \"base_value\": 21.1, \"spread\": 0.9, \"drift\": 0.2},\n            ],\n        },\n        \"sensor-backfill\": {\n            \"balanced\": [\n                {\"stream\": \"meter-east\", \"weight\": 1.1, \"window_offsets\": [0, 5, 10], \"base_value\": 34.5, \"spread\": 1.1, \"drift\": 0.3, \"late_offsets\": [5]},\n                {\"stream\": \"meter-west\", \"weight\": 1.0, \"window_offsets\": [0, 10, 15], \"base_value\": 33.8, \"spread\": 1.0, \"drift\": 0.2, \"late_offsets\": [10]},\n                {\"stream\": \"pipeline-north\", \"weight\": 1.0, \"window_offsets\": [5, 10, 20], \"base_value\": 31.2, \"spread\": 1.0, \"drift\": 0.2, \"late_offsets\": [5]},\n                {\"stream\": \"pipeline-south\", \"weight\": 0.9, \"window_offsets\": [0, 15, 20], \"base_value\": 32.1, \"spread\": 0.9, \"drift\": 0.2},\n            ],\n            \"skewed\": [\n                {\"stream\": \"meter-east\", \"weight\": 4.0, \"window_offsets\": [5, 10, 15], \"base_value\": 39.2, \"spread\": 1.4, \"drift\": 0.5, \"late_offsets\": [5, 10], \"drop_offsets\": [5, 10], \"hotspot_offsets\": [10], \"hotspot_bonus\": 6.2},\n                {\"stream\": \"meter-west\", \"weight\": 1.2, \"window_offsets\": [0, 10, 20], \"base_value\": 35.1, \"spread\": 1.1, \"drift\": 0.2, \"late_offsets\": [10]},\n                {\"stream\": \"pipeline-north\", \"weight\": 1.0, \"window_offsets\": [5, 15, 20], \"base_value\": 31.6, \"spread\": 1.0, \"drift\": 0.2},\n                {\"stream\": \"pipeline-south\", \"weight\": 0.8, \"window_offsets\": [0, 15, 25], \"base_value\": 32.4, \"spread\": 0.9, \"drift\": 0.2},\n            ],\n        },\n        \"live-replay\": {\n            \"balanced\": [\n                {\"stream\": \"chat-ingest\", \"weight\": 1.0, \"window_offsets\": [0, 5, 10], \"base_value\": 44.0, \"spread\": 1.2, \"drift\": 0.3, \"late_offsets\": [5]},\n                {\"stream\": \"reaction-fanout\", \"weight\": 1.0, \"window_offsets\": [0, 10, 15], \"base_value\": 41.5, \"spread\": 1.1, \"drift\": 0.3, \"late_offsets\": [10]},\n                {\"stream\": \"presence-sync\", \"weight\": 1.0, \"window_offsets\": [5, 10, 20], \"base_value\": 37.2, \"spread\": 1.0, \"drift\": 0.2},\n                {\"stream\": \"moderation-queue\", \"weight\": 1.0, \"window_offsets\": [0, 15, 20], \"base_value\": 40.1, \"spread\": 1.1, \"drift\": 0.3, \"late_offsets\": [15]},\n            ],\n            \"skewed\": [\n                {\"stream\": \"moderation-queue\", \"weight\": 3.9, \"window_offsets\": [15, 20, 20], \"base_value\": 50.3, \"spread\": 1.6, \"drift\": 0.6, \"late_offsets\": [15, 20], \"drop_offsets\": [15], \"hotspot_offsets\": [20], \"hotspot_bonus\": 7.1},\n                {\"stream\": \"reaction-fanout\", \"weight\": 1.5, \"window_offsets\": [10, 15, 20], \"base_value\": 43.4, \"spread\": 1.2, \"drift\": 0.3, \"late_offsets\": [15]},\n                {\"stream\": \"chat-ingest\", \"weight\": 1.0, \"window_offsets\": [0, 10, 25], \"base_value\": 44.2, \"spread\": 1.1, \"drift\": 0.2},\n                {\"stream\": \"presence-sync\", \"weight\": 0.9, \"window_offsets\": [5, 15, 25], \"base_value\": 37.8, \"spread\": 1.0, \"drift\": 0.2},\n            ],\n        },\n    }\n    if dataset_family not in families or scenario not in families[dataset_family]:\n        raise ValueError(f\"unsupported plugin benchmark scenario/family: {scenario}/{dataset_family}\")\n\n    profiles = families[dataset_family][scenario]\n    counts = _allocate_counts(records, [profile[\"weight\"] for profile in profiles])\n    lines = []\n    for profile, count in zip(profiles, counts):\n        lines.extend(\n            _generate_stream_events(\n                stream=profile[\"stream\"],\n                count=count,\n                base_time=base_time,\n                window_offsets=profile[\"window_offsets\"],\n                base_value=profile[\"base_value\"],\n                spread=profile[\"spread\"],\n                drift=profile[\"drift\"],\n                rng=rng,\n                late_window_offsets=profile.get(\"late_offsets\"),\n                drop_window_offsets=profile.get(\"drop_offsets\"),\n                hotspot_window_offsets=profile.get(\"hotspot_offsets\"),\n                hotspot_bonus=profile.get(\"hotspot_bonus\", 0.0),\n            )\n        )\n    lines.sort(key=lambda line: tuple(line.split(\",\", maxsplit=3)[1:3]))\n    return lines[:records]"` |
| `benchmark_generator_source_line` | `null` | `266` |
| `benchmark_generator_source_url` | `null` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L266-L341"` |
| `benchmark_note_hook` | `null` | `"plugins_watermark_late_summary.benchmark_notes"` |
| `benchmark_note_hook_doc_summary` | `null` | `"Describe the intended late-event hotspot story for each synthetic family."` |
| `benchmark_note_hook_signature` | `null` | `"benchmark_notes(scenario, dataset_family='default')"` |
| `benchmark_note_hook_source_anchor` | `null` | `"plugins_watermark_late_summary.py#L344-L413"` |
| `benchmark_note_hook_source_commit_url` | `null` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L344-L413"` |
| `benchmark_note_hook_source_excerpt` | `null` | `"def benchmark_notes(scenario, dataset_family=\"default\"):\n    \"\"\"Describe the intended late-event hotspot story for each synthetic family.\"\"\"\n    notes = {\n        (\"balanced\", \"default\"): [\n            {\n                \"title\": \"Mostly on-time telemetry baseline\",\n                \"detail\": \"The default balanced family keeps late updates mild and spread across four streams, so the report should read like a healthy watermark configuration rather than an incident.\",\n                \"severity\": \"info\",\n                \"takeaway\": \"Use this as the before state for explaining why a single stream with repeated backfills changes both lateness and drop rates.\",\n            },\n        ],\n        (\"skewed\", \"default\"): [\n            {\n                \"title\": \"Sensor alpha late-event hotspot\",\n                \"detail\": \"`sensor-alpha` is intentionally overloaded with backfilled windows, so the hottest reducer should show one stream dominating both late-accepted updates and dropped events.\",\n                \"severity\": \"watch\",\n                \"hotspot_keys\": [\"sensor-alpha\"],\n                \"takeaway\": \"This is the simplest portfolio story for explaining event time, watermarks, and allowed lateness without needing a full streaming framework.\",\n            },\n        ],\n        (\"balanced\", \"sensor-backfill\"): [\n            {\n                \"title\": \"Routine meter replays\",\n                \"detail\": \"The balanced sensor-backfill family makes every stream tolerate a few delayed packets, so the output reads like normal AMI backfill handling instead of a broken ingest pipeline.\",\n                \"severity\": \"info\",\n                \"takeaway\": \"Good for showing how watermark-aware summaries stay useful even when the late path is healthy and controlled.\",\n            },\n        ],\n        (\"skewed\", \"sensor-backfill\"): [\n            {\n                \"title\": \"Meter east replay storm\",\n                \"detail\": \"`meter-east` dominates this family with both accepted and dropped backfills, so the report should look like a utility stream replaying stale packets after a connectivity gap.\",\n                \"severity\": \"risk\",\n                \"hotspot_keys\": [\"meter-east\"],\n                \"takeaway\": \"Call out how the drop rate only climbs after the watermark passes the allowed-lateness boundary for the same windows.\",\n            },\n            {\n                \"title\": \"Meter west secondary lag\",\n                \"detail\": \"`meter-west` forms a smaller second-tier late stream behind meter-east, which helps the benchmark tell a richer story about regional spillover instead of a single broken key.\",\n                \"severity\": \"watch\",\n                \"hotspot_keys\": [\"meter-west\"],\n                \"takeaway\": \"Keep this note when you want a fuller data-engineering narrative instead of focusing only on the worst offender.\",\n            },\n        ],\n        (\"balanced\", \"live-replay\"): [\n            {\n                \"title\": \"Steady live-ops baseline\",\n                \"detail\": \"The balanced live-replay family keeps ingest, reactions, presence, and moderation close enough that the report reads like a normal stream-processing pipeline with occasional harmless replays.\",\n                \"severity\": \"info\",\n                \"takeaway\": \"Use this as the calm baseline before showing how moderation replays create visible watermark pressure.\",\n            },\n        ],\n        (\"skewed\", \"live-replay\"): [\n            {\n                \"title\": \"Moderation replay pile-up\",\n                \"detail\": \"`moderation-queue` becomes the obvious hotspot here with repeated stale replays, so the watermark summary looks like one downstream queue absorbing late chat events during a live launch.\",\n                \"severity\": \"risk\",\n                \"hotspot_keys\": [\"moderation-queue\"],\n                \"takeaway\": \"This turns the plugin into a streaming-systems case study about out-of-order handling instead of only fixed windows or batch reducers.\",\n            },\n            {\n                \"title\": \"Reaction fanout echo\",\n                \"detail\": \"`reaction-fanout` is the supporting late stream behind moderation, which helps explain how one replay wave can surface in multiple downstream consumers.\",\n                \"severity\": \"watch\",\n                \"hotspot_keys\": [\"reaction-fanout\"],\n                \"takeaway\": \"Keep this annotation when you want the report to highlight pipeline-wide replay propagation.\",\n            },\n        ],\n    }\n    return notes.get((scenario, dataset_family), [])"` |
| `benchmark_note_hook_source_line` | `null` | `344` |
| `benchmark_note_hook_source_url` | `null` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L344-L413"` |
| `combiner` | `"plugins_top_score.combine_values"` | `"plugins_watermark_late_summary.combine_values"` |
| `combiner_doc_summary` | `"Keep the shard-local maximum score for one student key."` | `"Keep shard-local stream event batches JSON-safe before watermark evaluation."` |
| `combiner_source_anchor` | `"plugins_top_score.py#L16-L18"` | `"plugins_watermark_late_summary.py#L150-L152"` |
| `combiner_source_commit_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_top_score.py#L16-L18"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L150-L152"` |
| `combiner_source_excerpt` | `"def combine_values(_key, values):\n    \"\"\"Keep the shard-local maximum score for one student key.\"\"\"\n    return max(values)"` | `"def combine_values(_key, values):\n    \"\"\"Keep shard-local stream event batches JSON-safe before watermark evaluation.\"\"\"\n    return {\"events\": sorted(values, key=lambda event: (event[\"arrived_at\"], event[\"event_at\"], event[\"value\"]))}"` |
| `combiner_source_line` | `16` | `150` |
| `combiner_source_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_top_score.py#L16-L18"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L150-L152"` |
| `mapper` | `"plugins_top_score.map_records"` | `"plugins_watermark_late_summary.map_records"` |
| `mapper_doc_summary` | `"Parse comma-separated score rows into integer leaderboard updates."` | `"Emit per-stream event batches from stream,event_time,arrival_time,value rows."` |
| `mapper_source_anchor` | `"plugins_top_score.py#L6-L13"` | `"plugins_watermark_late_summary.py#L136-L147"` |
| `mapper_source_commit_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_top_score.py#L6-L13"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L136-L147"` |
| `mapper_source_excerpt` | `"def map_records(lines):\n    \"\"\"Parse comma-separated score rows into integer leaderboard updates.\"\"\"\n    for raw in lines:\n        stripped = raw.strip()\n        if not stripped:\n            continue\n        name, score = stripped.split(\",\", maxsplit=1)\n        yield name.strip().lower(), int(score.strip())"` | `"def map_records(lines):\n    \"\"\"Emit per-stream event batches from stream,event_time,arrival_time,value rows.\"\"\"\n    for raw in lines:\n        stripped = raw.strip()\n        if not stripped:\n            continue\n        stream, event_at, arrived_at, value = [part.strip() for part in stripped.split(\",\", maxsplit=3)]\n        yield stream.lower(), {\n            \"event_at\": _isoformat_z(_parse_timestamp(event_at)),\n            \"arrived_at\": _isoformat_z(_parse_timestamp(arrived_at)),\n            \"value\": round(float(value), 3),\n        }"` |
| `mapper_source_line` | `6` | `136` |
| `mapper_source_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_top_score.py#L6-L13"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L136-L147"` |
| `module_doc_summary` | `"Maximum-score reducer plugin for simple leaderboard-style demos."` | `"Watermark-aware late-event summary plugin for out-of-order stream-processing demos."` |
| `name` | `"plugin-max-score"` | `"plugin-watermark-late-summary"` |
| `plugin` | `"projects/mini-mapreduce-lab/plugins_top_score.py"` | `"projects/mini-mapreduce-lab/plugins_watermark_late_summary.py"` |
| `reducer` | `"plugins_top_score.reduce_key"` | `"plugins_watermark_late_summary.reduce_key"` |
| `reducer_doc_summary` | `"Return the overall maximum score for one student key."` | `"Summarize watermark-aware acceptance, late updates, and dropped events for one stream."` |
| `reducer_signature` | `"reduce_key(_key, values)"` | `"reduce_key(key, values)"` |
| `reducer_source_anchor` | `"plugins_top_score.py#L21-L23"` | `"plugins_watermark_late_summary.py#L155-L223"` |
| `reducer_source_commit_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_top_score.py#L21-L23"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L155-L223"` |
| `reducer_source_excerpt` | `"def reduce_key(_key, values):\n    \"\"\"Return the overall maximum score for one student key.\"\"\"\n    return max(values)"` | `"def reduce_key(key, values):\n    \"\"\"Summarize watermark-aware acceptance, late updates, and dropped events for one stream.\"\"\"\n    merged = _merge_event_batches(values)\n    events = merged[\"events\"]\n    windows = {}\n    max_seen_event_time = None\n    first_arrival_at = None\n    last_arrival_at = None\n    max_watermark_gap_minutes = 0.0\n    late_events_seen = 0\n\n    for item in events:\n        event_at = _parse_timestamp(item[\"event_at\"])\n        arrived_at = _parse_timestamp(item[\"arrived_at\"])\n        value = float(item[\"value\"])\n        if first_arrival_at is None or arrived_at < first_arrival_at:\n            first_arrival_at = arrived_at\n        if last_arrival_at is None or arrived_at > last_arrival_at:\n            last_arrival_at = arrived_at\n\n        watermark_before = _watermark_for(max_seen_event_time)\n        window_start = _window_start(event_at)\n        window_key = _isoformat_z(window_start)\n        summary = windows.setdefault(window_key, _new_window_summary(window_start))\n        window_close_at = _parse_timestamp(summary[\"window_close_at\"])\n        late = watermark_before is not None and event_at < watermark_before\n        dropped = watermark_before is not None and watermark_before > window_close_at\n        if late and watermark_before is not None:\n            late_events_seen += 1\n            max_watermark_gap_minutes = max(\n                max_watermark_gap_minutes,\n                round((watermark_before - event_at).total_seconds() / 60, 3),\n            )\n\n        _update_window_summary(summary, event_at=event_at, arrived_at=arrived_at, value=value, late=late, dropped=dropped)\n        max_seen_event_time = event_at if max_seen_event_time is None else max(max_seen_event_time, event_at)\n\n    finalized_windows = [_finalize_window_summary(windows[key]) for key in sorted(windows)]\n    accepted_events = sum(item[\"accepted_events\"] for item in finalized_windows)\n    on_time_events = sum(item[\"on_time_events\"] for item in finalized_windows)\n    late_accepted_events = sum(item[\"late_accepted_events\"] for item in finalized_windows)\n    dropped_late_events = sum(item[\"dropped_late_events\"] for item in finalized_windows)\n    total_events_seen = sum(item[\"events_seen\"] for item in finalized_windows)\n    hottest_window = max(\n        finalized_windows,\n        key=lambda item: (item[\"late_accepted_events\"] + item[\"dropped_late_events\"], item[\"accepted_events\"], item[\"window_start\"]),\n        default=None,\n    )\n    return {\n        \"stream\": key,\n        \"window_count\": len(finalized_windows),\n        \"total_events_seen\": total_events_seen,\n        \"accepted_events\": accepted_events,\n        \"on_time_events\": on_time_events,\n        \"late_events_seen\": late_events_seen,\n        \"late_accepted_events\": late_accepted_events,\n        \"dropped_late_events\": dropped_late_events,\n        \"late_acceptance_rate\": round(late_accepted_events / accepted_events, 3) if accepted_events else 0.0,\n        \"drop_rate\": round(dropped_late_events / total_events_seen, 3) if total_events_seen else 0.0,\n        \"first_arrival_at\": _isoformat_z(first_arrival_at) if first_arrival_at else None,\n        \"last_arrival_at\": _isoformat_z(last_arrival_at) if last_arrival_at else None,\n        \"final_watermark\": _isoformat_z(_watermark_for(max_seen_event_time)) if max_seen_event_time else None,\n        \"max_watermark_gap_minutes\": round(max_watermark_gap_minutes, 3),\n        \"hottest_window_start\": hottest_window[\"window_start\"] if hottest_window else None,\n        \"hottest_window_late_events\": (\n            hottest_window[\"late_accepted_events\"] + hottest_window[\"dropped_late_events\"]\n        ) if hottest_window else 0,\n        \"windows\": finalized_windows,\n    }"` |
| `reducer_source_line` | `21` | `155` |
| `reducer_source_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_top_score.py#L21-L23"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L155-L223"` |
