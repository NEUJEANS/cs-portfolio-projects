# Mini MapReduce plugin release comparison

- Before snapshot: `2026-04-17` (`2` plugins; commits: `2312cf246e3b3cab1fe7b3895bc7b55d7b60c3c8`)
- After snapshot: `current` (`7` plugins; commits: `2332425c37ad2eb7d0399cb11e91a2354e189d22`)
- Summary: `5` added · `0` removed · `0` changed · `2` unchanged

## Added plugins

| Plugin | Summary | Dataset families | Commit |
| --- | --- | --- | --- |
| `plugin-rolling-window-join`<br><small>`projects/mini-mapreduce-lab/plugins_rolling_window_join.py`</small> | Rolling-window join plugin for multi-stream correlation and pipeline-debug demos. | `default, checkout-funnel, incident-correlation` | `2332425c37ad` |
| `plugin-service-latency`<br><small>`projects/mini-mapreduce-lab/plugins_service_latency.py`</small> | Service-latency summary plugin for observability-style benchmark demos. | `default, incident-spike, batch-window` | `2332425c37ad` |
| `plugin-sessionization`<br><small>`projects/mini-mapreduce-lab/plugins_sessionization.py`</small> | Sessionization analytics plugin for product-usage benchmark demos. | `default, exam-revision, launch-day` | `2332425c37ad` |
| `plugin-streaming-window`<br><small>`projects/mini-mapreduce-lab/plugins_streaming_window.py`</small> | Streaming-window aggregation plugin for telemetry-style benchmark demos. | `default, iot-burst, live-ops` | `2332425c37ad` |
| `plugin-watermark-late-summary`<br><small>`projects/mini-mapreduce-lab/plugins_watermark_late_summary.py`</small> | Watermark-aware late-event summary plugin for out-of-order stream-processing demos. | `default, sensor-backfill, live-replay` | `2332425c37ad` |

## Removed plugins

- No plugins were removed between these snapshots.

## Changed plugins

- No shared plugins changed contract between these snapshots.

## Unchanged plugins

- `plugin-average-score, plugin-max-score`
