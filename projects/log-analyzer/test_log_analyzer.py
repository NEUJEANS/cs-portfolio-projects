import csv
import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from datetime import datetime, timezone
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from log_analyzer import (
    analyze_lines,
    format_facet_comparison_card_html,
    format_facet_comparison_card_svg,
    format_text_report,
    format_time_bucket_card_html,
    format_time_bucket_card_svg,
    normalize_card_annotations,
    parse_line,
)


class LogAnalyzerTests(unittest.TestCase):
    def test_parse_line_supports_dash_bytes(self):
        parsed = parse_line('10.0.0.1 - - [18/Apr/2026:09:00:00 +0000] "GET / HTTP/1.1" 304 -')
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.bytes_sent, 0)
        self.assertEqual(parsed.method, 'GET')
        self.assertIsNone(parsed.referrer)
        self.assertIsNone(parsed.latency_ms)
        self.assertIsNone(parsed.upstream_response_time_ms)

    def test_parse_line_parses_common_log_timestamp(self):
        parsed = parse_line('10.0.0.1 - - [18/Apr/2026:09:00:00 +0000] "GET / HTTP/1.1" 200 10')
        self.assertIsNotNone(parsed)
        self.assertEqual(
            parsed.timestamp,
            datetime(2026, 4, 18, 9, 0, 0, tzinfo=timezone.utc),
        )

    def test_parse_line_supports_combined_logs_with_latency(self):
        parsed = parse_line(
            '10.0.0.1 - - [18/Apr/2026:09:00:00 +0000] "GET /docs HTTP/1.1" 200 123 '
            '"https://example.com/start" "Mozilla/5.0" 0.245'
        )
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.referrer, 'https://example.com/start')
        self.assertEqual(parsed.user_agent, 'Mozilla/5.0')
        self.assertEqual(parsed.latency_ms, 245.0)
        self.assertIsNone(parsed.request_time_ms)

    def test_parse_line_supports_microsecond_latency(self):
        parsed = parse_line(
            '10.0.0.2 - - [18/Apr/2026:09:01:00 +0000] "POST /ingest HTTP/1.1" 201 42 '
            '"-" "curl/8.0" 12345'
        )
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.latency_ms, 12.345)
        self.assertEqual(parsed.user_agent, 'curl/8.0')
        self.assertIsNone(parsed.referrer)

    def test_parse_line_supports_named_nginx_timing_fields(self):
        parsed = parse_line(
            '10.0.0.3 - - [18/Apr/2026:09:02:00 +0000] "GET /api/report HTTP/1.1" 200 321 '
            '"https://example.com" "Mozilla/5.0" '
            'request_time=0.245 upstream_response_time=0.201 upstream_connect_time=0.010'
        )
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.latency_ms, 245.0)
        self.assertEqual(parsed.request_time_ms, 245.0)
        self.assertEqual(parsed.upstream_response_time_ms, 201.0)

    def test_parse_line_sums_multi_attempt_upstream_response_times(self):
        parsed = parse_line(
            '10.0.0.4 - - [18/Apr/2026:09:03:00 +0000] "GET /retry HTTP/1.1" 200 64 '
            'request_time=0.400 upstream_response_time=0.050, 0.125:0.075'
        )
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.request_time_ms, 400.0)
        self.assertEqual(parsed.upstream_response_time_ms, 250.0)
        self.assertEqual(parsed.latency_ms, 400.0)

    def test_parse_line_ignores_invalid_named_timing_values(self):
        parsed = parse_line(
            '10.0.0.5 - - [18/Apr/2026:09:04:00 +0000] "GET /broken HTTP/1.1" 200 32 '
            'request_time=oops upstream_response_time=0.010'
        )
        self.assertIsNotNone(parsed)
        self.assertIsNone(parsed.request_time_ms)
        self.assertIsNone(parsed.latency_ms)
        self.assertEqual(parsed.upstream_response_time_ms, 10.0)

    def test_parse_line_preserves_named_fields_for_facets(self):
        parsed = parse_line(
            '10.0.0.6 - - [18/Apr/2026:09:05:00 +0000] "GET /api/report HTTP/1.1" 200 64 '
            'request_time=0.120 env=prod region=us-east-1 release=2026.04'
        )
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.named_fields['env'], 'prod')
        self.assertEqual(parsed.named_fields['region'], 'us-east-1')
        self.assertEqual(parsed.named_fields['release'], '2026.04')

    def test_analyze_lines_counts_combined_fields_and_latency(self):
        lines = [
            '10.0.0.1 - - [18/Apr/2026:09:00:00 +0000] "GET / HTTP/1.1" 200 10 "https://example.com/start" "Mozilla/5.0" 0.100',
            '10.0.0.2 - - [18/Apr/2026:09:01:00 +0000] "POST /login HTTP/1.1" 401 5 "https://example.com/start" "curl/8.0" 0.350',
            '10.0.0.1 - - [18/Apr/2026:09:02:00 +0000] "GET / HTTP/1.1" 200 15',
            'garbled log line',
        ]
        result = analyze_lines(lines, top_n=2)
        self.assertEqual(result['total_requests'], 3)
        self.assertEqual(result['invalid_lines'], 1)
        self.assertEqual(result['total_bytes'], 30)
        self.assertEqual(result['average_bytes'], 10.0)
        self.assertEqual(result['status_counts']['200'], 2)
        self.assertEqual(result['method_counts']['GET'], 2)
        self.assertEqual(result['top_ips'][0], ('10.0.0.1', 2))
        self.assertEqual(result['top_paths'][0], ('/', 2))
        self.assertEqual(result['top_referrers'][0], ('https://example.com/start', 2))
        self.assertEqual(result['top_user_agents'][0], ('Mozilla/5.0', 1))
        self.assertIsNotNone(result['latency_summary'])
        self.assertEqual(result['latency_summary']['count'], 2)
        self.assertEqual(result['latency_summary']['average_ms'], 225.0)
        self.assertEqual(result['latency_summary']['p50_ms'], 225.0)
        self.assertEqual(result['latency_summary']['max_ms'], 350.0)
        self.assertIsNone(result['upstream_latency_summary'])
        self.assertEqual(result['path_latency_breakdown'][0]['path'], '/login')
        self.assertEqual(result['path_latency_breakdown'][0]['average_ms'], 350.0)
        self.assertIsNone(result['time_window'])
        self.assertIsNone(result['time_bucketing'])
        self.assertEqual(result['time_buckets'], [])

    def test_analyze_lines_reports_upstream_latency_summary_from_named_fields(self):
        lines = [
            '10.0.0.1 - - [18/Apr/2026:09:00:00 +0000] "GET /api/report HTTP/1.1" 200 100 "-" "agent-a" request_time=0.120 upstream_response_time=0.080',
            '10.0.0.2 - - [18/Apr/2026:09:01:00 +0000] "GET /api/report HTTP/1.1" 200 120 "-" "agent-a" request_time=0.180 upstream_response_time=0.050, 0.070',
            '10.0.0.3 - - [18/Apr/2026:09:02:00 +0000] "GET /status HTTP/1.1" 200 90 request_time=0.040 upstream_response_time=-',
        ]
        result = analyze_lines(lines, top_n=2)
        self.assertEqual(result['latency_summary']['count'], 3)
        self.assertEqual(result['latency_summary']['max_ms'], 180.0)
        self.assertIsNotNone(result['upstream_latency_summary'])
        self.assertEqual(result['upstream_latency_summary']['count'], 2)
        self.assertEqual(result['upstream_latency_summary']['average_ms'], 100.0)
        self.assertEqual(result['upstream_latency_summary']['max_ms'], 120.0)
        self.assertEqual(result['path_latency_breakdown'][0]['path'], '/api/report')
        self.assertEqual(result['upstream_path_latency_breakdown'][0]['path'], '/api/report')
        self.assertEqual(result['upstream_path_latency_breakdown'][0]['average_ms'], 100.0)

    def test_analyze_lines_limits_and_sorts_path_latency_breakdown(self):
        lines = [
            '10.0.0.1 - - [18/Apr/2026:09:00:00 +0000] "GET /fast HTTP/1.1" 200 10 "-" "agent-a" 0.010',
            '10.0.0.2 - - [18/Apr/2026:09:01:00 +0000] "GET /fast HTTP/1.1" 200 11 "-" "agent-a" 0.015',
            '10.0.0.3 - - [18/Apr/2026:09:02:00 +0000] "GET /steady HTTP/1.1" 200 12 "-" "agent-b" 0.200',
            '10.0.0.4 - - [18/Apr/2026:09:03:00 +0000] "GET /steady HTTP/1.1" 200 13 "-" "agent-b" 0.220',
            '10.0.0.5 - - [18/Apr/2026:09:04:00 +0000] "GET /hot HTTP/1.1" 200 14 "-" "agent-c" 0.450',
        ]
        result = analyze_lines(lines, top_n=2, latency_top_n=2)
        self.assertEqual([row['path'] for row in result['path_latency_breakdown']], ['/hot', '/steady'])
        self.assertEqual(result['path_latency_breakdown'][1]['count'], 2)
        self.assertEqual(result['path_latency_breakdown'][1]['p95_ms'], 219.0)

    def test_analyze_lines_limits_and_sorts_upstream_path_latency_breakdown(self):
        lines = [
            '10.0.0.1 - - [18/Apr/2026:09:00:00 +0000] "GET /fast HTTP/1.1" 200 10 request_time=0.050 upstream_response_time=0.010',
            '10.0.0.2 - - [18/Apr/2026:09:01:00 +0000] "GET /retry HTTP/1.1" 200 11 request_time=0.300 upstream_response_time=0.080, 0.070',
            '10.0.0.3 - - [18/Apr/2026:09:02:00 +0000] "GET /retry HTTP/1.1" 200 12 request_time=0.320 upstream_response_time=0.090',
            '10.0.0.4 - - [18/Apr/2026:09:03:00 +0000] "GET /db HTTP/1.1" 200 13 request_time=0.280 upstream_response_time=0.200',
        ]
        result = analyze_lines(lines, top_n=2, latency_top_n=2)
        self.assertEqual(
            [row['path'] for row in result['upstream_path_latency_breakdown']],
            ['/db', '/retry'],
        )
        self.assertEqual(result['upstream_path_latency_breakdown'][1]['count'], 2)
        self.assertEqual(result['upstream_path_latency_breakdown'][1]['average_ms'], 120.0)

    def test_analyze_lines_filters_hotspots_without_changing_global_summaries(self):
        lines = [
            '10.0.0.1 - - [18/Apr/2026:09:00:00 +0000] "GET /health HTTP/1.1" 200 10 request_time=0.005 upstream_response_time=0.001',
            '10.0.0.2 - - [18/Apr/2026:09:01:00 +0000] "POST /api/report HTTP/1.1" 500 12 request_time=0.600 upstream_response_time=0.500',
            '10.0.0.3 - - [18/Apr/2026:09:02:00 +0000] "POST /api/report HTTP/1.1" 502 13 request_time=0.700 upstream_response_time=0.650',
            '10.0.0.4 - - [18/Apr/2026:09:03:00 +0000] "GET /api/report HTTP/1.1" 500 14 request_time=0.450 upstream_response_time=0.300',
        ]
        result = analyze_lines(
            lines,
            top_n=3,
            hotspot_statuses=['500', '502'],
            hotspot_methods=['POST'],
        )
        self.assertEqual(result['latency_summary']['count'], 4)
        self.assertEqual(result['upstream_latency_summary']['count'], 4)
        self.assertEqual(
            result['hotspot_filters'],
            {'statuses': ['500', '502'], 'methods': ['POST']},
        )
        self.assertEqual([row['path'] for row in result['path_latency_breakdown']], ['/api/report'])
        self.assertEqual(result['path_latency_breakdown'][0]['count'], 2)
        self.assertEqual(result['path_latency_breakdown'][0]['average_ms'], 650.0)
        self.assertEqual(result['upstream_path_latency_breakdown'][0]['average_ms'], 575.0)

    def test_analyze_lines_filters_by_time_window(self):
        lines = [
            '10.0.0.1 - - [18/Apr/2026:08:59:00 +0000] "GET /before HTTP/1.1" 200 10 request_time=0.050',
            '10.0.0.2 - - [18/Apr/2026:09:00:00 +0000] "GET /inside HTTP/1.1" 200 11 request_time=0.120 upstream_response_time=0.070',
            '10.0.0.3 - - [18/Apr/2026:09:05:00 +0000] "POST /inside HTTP/1.1" 500 12 request_time=0.400 upstream_response_time=0.300',
            '10.0.0.4 - - [18/Apr/2026:09:10:00 +0000] "GET /after HTTP/1.1" 200 13 request_time=0.080',
        ]
        result = analyze_lines(
            lines,
            top_n=2,
            window_start=datetime(2026, 4, 18, 9, 0, 0, tzinfo=timezone.utc),
            window_end=datetime(2026, 4, 18, 9, 5, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(result['total_requests'], 2)
        self.assertEqual(result['top_paths'][0], ('/inside', 2))
        self.assertEqual(result['latency_summary']['count'], 2)
        self.assertEqual(result['time_window']['matched_requests'], 2)
        self.assertEqual(result['time_window']['excluded_requests'], 2)
        self.assertEqual(result['time_window']['start'], '2026-04-18T09:00:00+00:00')
        self.assertEqual(result['time_window']['end'], '2026-04-18T09:05:00+00:00')

    def test_analyze_lines_summarizes_minute_time_buckets(self):
        lines = [
            '10.0.0.1 - - [18/Apr/2026:09:00:05 +0000] "GET /api/report HTTP/1.1" 200 10 request_time=0.050 upstream_response_time=0.030',
            '10.0.0.2 - - [18/Apr/2026:09:00:40 +0000] "POST /api/report HTTP/1.1" 500 12 request_time=0.400 upstream_response_time=0.250',
            '10.0.0.3 - - [18/Apr/2026:09:01:10 +0000] "POST /slow HTTP/1.1" 502 13 request_time=0.600 upstream_response_time=0.350',
        ]
        result = analyze_lines(lines, top_n=2, time_bucket_granularity='minute')
        self.assertEqual(result['time_bucketing'], {'granularity': 'minute', 'bucket_count': 2})
        self.assertEqual(len(result['time_buckets']), 2)
        first_bucket = result['time_buckets'][0]
        self.assertEqual(first_bucket['bucket_start'], '2026-04-18T09:00:00+00:00')
        self.assertEqual(first_bucket['bucket_end'], '2026-04-18T09:01:00+00:00')
        self.assertEqual(first_bucket['request_count'], 2)
        self.assertEqual(first_bucket['error_count'], 1)
        self.assertEqual(first_bucket['error_rate_pct'], 50.0)
        self.assertEqual(first_bucket['top_path'], '/api/report')
        self.assertEqual(first_bucket['top_path_count'], 2)
        self.assertEqual(first_bucket['latency_sample_count'], 2)
        self.assertEqual(first_bucket['average_latency_ms'], 225.0)
        self.assertEqual(first_bucket['max_latency_ms'], 400.0)
        self.assertEqual(first_bucket['upstream_latency_sample_count'], 2)
        self.assertEqual(first_bucket['average_upstream_latency_ms'], 140.0)

    def test_analyze_lines_normalizes_time_buckets_to_utc(self):
        lines = [
            '10.0.0.1 - - [18/Apr/2026:18:00:05 +0900] "GET /seoul HTTP/1.1" 200 10 request_time=0.050',
        ]
        result = analyze_lines(lines, top_n=1, time_bucket_granularity='hour')
        self.assertEqual(result['time_bucketing'], {'granularity': 'hour', 'bucket_count': 1})
        self.assertEqual(result['time_buckets'][0]['bucket_start'], '2026-04-18T09:00:00+00:00')
        self.assertEqual(result['time_buckets'][0]['bucket_end'], '2026-04-18T10:00:00+00:00')

    def test_analyze_lines_builds_facet_breakdowns(self):
        lines = [
            '10.0.0.1 - - [18/Apr/2026:09:00:05 +0000] "POST /api/report HTTP/1.1" 500 10 request_time=0.400 upstream_response_time=0.250 env=prod region=us-east-1',
            '10.0.0.2 - - [18/Apr/2026:09:00:40 +0000] "POST /api/report HTTP/1.1" 502 12 request_time=0.500 upstream_response_time=0.300 env=prod region=us-east-1',
            '10.0.0.3 - - [18/Apr/2026:09:01:10 +0000] "POST /api/report HTTP/1.1" 500 13 request_time=0.200 upstream_response_time=0.120 env=staging region=us-west-2',
        ]
        result = analyze_lines(
            lines,
            top_n=2,
            latency_top_n=3,
            hotspot_statuses=['500', '502'],
            hotspot_methods=['POST'],
            time_bucket_granularity='minute',
            facet_fields=['env', 'region'],
        )
        self.assertEqual(
            result['faceting'],
            {'fields': ['env', 'region'], 'missing_value': '(missing)'},
        )
        self.assertEqual(result['path_latency_facet_breakdown'][0]['path'], '/api/report')
        self.assertEqual(result['path_latency_facet_breakdown'][0]['facets'], {'env': 'prod', 'region': 'us-east-1'})
        self.assertEqual(result['path_latency_facet_breakdown'][0]['average_ms'], 450.0)
        self.assertEqual(result['upstream_path_latency_facet_breakdown'][1]['facets'], {'env': 'staging', 'region': 'us-west-2'})
        self.assertEqual(result['time_bucket_facet_breakdown'][0]['bucket_start'], '2026-04-18T09:00:00+00:00')
        self.assertEqual(result['time_bucket_facet_breakdown'][0]['facets'], {'env': 'prod', 'region': 'us-east-1'})
        self.assertEqual(result['time_bucket_facet_breakdown'][0]['request_count'], 2)
        self.assertEqual(result['time_bucket_facet_breakdown'][1]['facets'], {'env': 'staging', 'region': 'us-west-2'})

    def test_analyze_lines_builds_facet_comparison(self):
        lines = [
            '10.0.0.1 - - [18/Apr/2026:09:00:05 +0000] "GET /api/report HTTP/1.1" 200 10 request_time=0.050 upstream_response_time=0.030 env=prod',
            '10.0.0.2 - - [18/Apr/2026:09:00:40 +0000] "POST /api/report HTTP/1.1" 500 12 request_time=0.400 upstream_response_time=0.250 env=prod',
            '10.0.0.3 - - [18/Apr/2026:09:01:10 +0000] "POST /api/report HTTP/1.1" 200 13 request_time=0.200 upstream_response_time=0.120 env=staging',
            '10.0.0.4 - - [18/Apr/2026:09:01:40 +0000] "POST /slow HTTP/1.1" 502 13 request_time=0.600 upstream_response_time=0.350 env=staging',
        ]
        result = analyze_lines(
            lines,
            top_n=2,
            time_bucket_granularity='minute',
            facet_compare_field='env',
            facet_compare_values=('prod', 'staging'),
        )
        comparison = result['facet_comparison']
        self.assertIsNotNone(comparison)
        self.assertEqual(comparison['field'], 'env')
        self.assertEqual(comparison['left']['value'], 'prod')
        self.assertEqual(comparison['right']['value'], 'staging')
        self.assertEqual(comparison['delta_direction'], 'staging minus prod')
        self.assertEqual(comparison['left']['summary']['request_count'], 2)
        self.assertEqual(comparison['right']['summary']['request_count'], 2)
        self.assertEqual(comparison['delta']['average_latency_ms_delta'], 175)
        self.assertEqual(comparison['delta']['p95_upstream_latency_ms_delta'], 99.5)
        self.assertEqual(comparison['time_bucketing'], {'granularity': 'minute', 'bucket_count': 2})
        self.assertEqual(comparison['time_buckets'][0]['bucket_start'], '2026-04-18T09:00:00+00:00')
        self.assertEqual(comparison['time_buckets'][0]['left_request_count'], 2)
        self.assertEqual(comparison['time_buckets'][0]['right_request_count'], 0)
        self.assertEqual(comparison['time_buckets'][0]['error_rate_pct_delta'], -50)
        self.assertEqual(comparison['time_buckets'][1]['left_request_count'], 0)
        self.assertEqual(comparison['time_buckets'][1]['right_request_count'], 2)
        self.assertEqual(comparison['time_buckets'][1]['p95_latency_ms_delta'], None)

    def test_format_text_report_mentions_facet_comparison(self):
        report = format_text_report(
            analyze_lines(
                [
                    '10.0.0.1 - - [18/Apr/2026:09:00:05 +0000] "GET /api/report HTTP/1.1" 200 10 request_time=0.050 upstream_response_time=0.030 env=prod',
                    '10.0.0.2 - - [18/Apr/2026:09:00:40 +0000] "POST /api/report HTTP/1.1" 500 12 request_time=0.400 upstream_response_time=0.250 env=prod',
                    '10.0.0.3 - - [18/Apr/2026:09:01:10 +0000] "POST /api/report HTTP/1.1" 200 13 request_time=0.200 upstream_response_time=0.120 env=staging',
                    '10.0.0.4 - - [18/Apr/2026:09:01:40 +0000] "POST /slow HTTP/1.1" 502 13 request_time=0.600 upstream_response_time=0.350 env=staging',
                ],
                top_n=2,
                time_bucket_granularity='minute',
                facet_compare_field='env',
                facet_compare_values=('prod', 'staging'),
            )
        )
        self.assertIn('Facet comparison (env): prod vs staging (delta: staging minus prod)', report)
        self.assertIn('env=prod -> requests=2, errors=1 (50.0%), avg_latency=225 ms, p95_latency=382.5 ms', report)
        self.assertIn('delta -> requests=0, errors=0, error_rate=0 pp, avg_latency=175 ms, p95_latency=197.5 ms, avg_upstream=95 ms, p95_upstream=99.5 ms', report)
        self.assertIn('Facet comparison buckets (minute):', report)

    def test_format_text_report_handles_empty_results(self):
        report = format_text_report(analyze_lines([], top_n=3))
        self.assertIn('Total requests: 0', report)
        self.assertIn('Status counts:', report)
        self.assertIn('Top referrers:', report)
        self.assertIn('Latency summary (ms):', report)
        self.assertIn('Upstream latency summary (ms):', report)
        self.assertIn('Per-path latency hotspots (ms):', report)
        self.assertIn('Per-path upstream latency hotspots (ms):', report)
        self.assertIn('  (none)', report)

    def test_format_text_report_mentions_hotspot_filters(self):
        report = format_text_report(
            analyze_lines(
                [
                    '10.0.0.1 - - [18/Apr/2026:09:00:00 +0000] "POST /api/report HTTP/1.1" 500 12 request_time=0.600 upstream_response_time=0.500',
                ],
                top_n=1,
                hotspot_statuses=['500'],
                hotspot_methods=['POST'],
            )
        )
        self.assertIn('Per-path latency hotspots (ms): (filters: status=500; method=POST)', report)
        self.assertIn('Per-path upstream latency hotspots (ms): (filters: status=500; method=POST)', report)

    def test_format_text_report_mentions_time_window(self):
        report = format_text_report(
            analyze_lines(
                [
                    '10.0.0.1 - - [18/Apr/2026:09:00:00 +0000] "GET /inside HTTP/1.1" 200 10 request_time=0.050',
                    '10.0.0.2 - - [18/Apr/2026:09:10:00 +0000] "GET /outside HTTP/1.1" 200 10 request_time=0.060',
                ],
                top_n=1,
                window_end=datetime(2026, 4, 18, 9, 5, 0, tzinfo=timezone.utc),
            )
        )
        self.assertIn('Time window:', report)
        self.assertIn('End: 2026-04-18T09:05:00+00:00', report)
        self.assertIn('Excluded requests: 1', report)

    def test_format_text_report_mentions_time_bucket_trends(self):
        report = format_text_report(
            analyze_lines(
                [
                    '10.0.0.1 - - [18/Apr/2026:09:00:05 +0000] "GET /api/report HTTP/1.1" 200 10 request_time=0.050 upstream_response_time=0.030',
                    '10.0.0.2 - - [18/Apr/2026:09:00:40 +0000] "POST /api/report HTTP/1.1" 500 12 request_time=0.400 upstream_response_time=0.250',
                ],
                top_n=1,
                time_bucket_granularity='minute',
            )
        )
        self.assertIn('Time bucket trends (minute):', report)
        self.assertIn('2026-04-18T09:00:00+00:00 -> requests=2, errors=1 (50.0%), top_path=/api/report (2)', report)
        self.assertIn('request latency: samples=2, avg=225.0, p95=382.5, max=400.0', report)

    def test_format_text_report_mentions_facet_breakdowns(self):
        report = format_text_report(
            analyze_lines(
                [
                    '10.0.0.1 - - [18/Apr/2026:09:00:05 +0000] "POST /api/report HTTP/1.1" 500 10 request_time=0.450 upstream_response_time=0.300 env=prod region=us-east-1',
                    '10.0.0.2 - - [18/Apr/2026:09:00:40 +0000] "POST /api/report HTTP/1.1" 502 12 request_time=0.500 upstream_response_time=0.320 env=prod region=us-east-1',
                ],
                top_n=1,
                hotspot_statuses=['500', '502'],
                hotspot_methods=['POST'],
                time_bucket_granularity='minute',
                facet_fields=['env', 'region'],
            )
        )
        self.assertIn('Time bucket facet breakdowns: (facets: env, region)', report)
        self.assertIn('2026-04-18T09:00:00+00:00 | env=prod, region=us-east-1 -> requests=2, errors=2 (100.0%), top_path=/api/report (2)', report)
        self.assertIn('Per-path latency hotspots by facet (ms): (filters: status=500,502; method=POST) (facets: env, region)', report)
        self.assertIn('/api/report | env=prod, region=us-east-1: count=2, avg=475.0, p95=497.5, max=500.0', report)

    def test_format_text_report_omits_time_bucket_facet_section_without_bucketing(self):
        report = format_text_report(
            analyze_lines(
                [
                    '10.0.0.1 - - [18/Apr/2026:09:00:05 +0000] "POST /api/report HTTP/1.1" 500 10 request_time=0.450 upstream_response_time=0.300 env=prod region=us-east-1',
                ],
                top_n=1,
                hotspot_statuses=['500'],
                hotspot_methods=['POST'],
                facet_fields=['env', 'region'],
            )
        )
        self.assertNotIn('Time bucket facet breakdowns:', report)
        self.assertIn('Per-path latency hotspots by facet (ms): (filters: status=500; method=POST) (facets: env, region)', report)

    def test_normalize_card_annotations_groups_bucket_labels(self):
        result = analyze_lines(
            [
                '10.0.0.1 - - [18/Apr/2026:09:00:05 +0000] "GET /api/report HTTP/1.1" 200 10 request_time=0.050',
                '10.0.0.2 - - [18/Apr/2026:09:01:05 +0000] "GET /api/report HTTP/1.1" 200 10 request_time=0.060',
            ],
            top_n=2,
            time_bucket_granularity='minute',
        )
        annotations = normalize_card_annotations(
            [
                '2026-04-18T09:00:10Z=Deploy started',
                '2026-04-18T09:00:40Z=Error budget burn',
                '2026-04-18T09:01:10Z=Rollback verified',
            ],
            time_buckets=result['time_buckets'],
        )
        self.assertEqual(len(annotations), 2)
        self.assertEqual(annotations[0]['marker'], '1')
        self.assertEqual(annotations[0]['bucket_start'], '2026-04-18T09:00:00+00:00')
        self.assertEqual(annotations[0]['label'], 'Deploy started · Error budget burn')
        self.assertEqual(annotations[0]['event_time_label'], '09:00:10, 09:00:40')
        self.assertEqual(annotations[0]['theme'], 'note')
        self.assertEqual(annotations[0]['theme_label'], 'Note')
        self.assertEqual(annotations[1]['marker'], '2')
        self.assertEqual(annotations[1]['bucket_start'], '2026-04-18T09:01:00+00:00')

    def test_normalize_card_annotations_supports_themes_and_dominant_bucket_severity(self):
        result = analyze_lines(
            [
                '10.0.0.1 - - [18/Apr/2026:09:00:05 +0000] "GET /api/report HTTP/1.1" 200 10 request_time=0.050',
                '10.0.0.2 - - [18/Apr/2026:09:01:05 +0000] "GET /api/report HTTP/1.1" 200 10 request_time=0.060',
            ],
            top_n=2,
            time_bucket_granularity='minute',
        )
        annotations = normalize_card_annotations(
            [
                '2026-04-18T09:00:10Z=deploy|Deploy started',
                '2026-04-18T09:00:40Z=incident|Error budget burn',
                '2026-04-18T09:01:10Z=rollback|Rollback verified',
            ],
            time_buckets=result['time_buckets'],
        )
        self.assertEqual(annotations[0]['theme'], 'incident')
        self.assertEqual(annotations[0]['theme_label'], 'Incident')
        self.assertEqual(annotations[0]['theme_count'], 2)
        self.assertEqual(annotations[0]['theme_summary'], 'Deploy, Incident')
        self.assertEqual(annotations[1]['theme'], 'rollback')
        self.assertEqual(annotations[1]['theme_label'], 'Rollback')

    def test_normalize_card_annotations_rejects_unknown_theme(self):
        result = analyze_lines(
            [
                '10.0.0.1 - - [18/Apr/2026:09:00:05 +0000] "GET /api/report HTTP/1.1" 200 10 request_time=0.050',
            ],
            top_n=1,
            time_bucket_granularity='minute',
        )
        with self.assertRaisesRegex(ValueError, "Unknown --card-annotation theme 'mystery'"):
            normalize_card_annotations(
                ['2026-04-18T09:00:10Z=mystery|Unknown theme'],
                time_buckets=result['time_buckets'],
            )

    def test_normalize_card_annotations_rejects_out_of_range_timestamp(self):
        result = analyze_lines(
            [
                '10.0.0.1 - - [18/Apr/2026:09:00:05 +0000] "GET /api/report HTTP/1.1" 200 10 request_time=0.050',
            ],
            top_n=1,
            time_bucket_granularity='minute',
        )
        with self.assertRaisesRegex(ValueError, 'falls outside the current bucket coverage'):
            normalize_card_annotations(
                ['2026-04-18T09:05:00Z=Too late'],
                time_buckets=result['time_buckets'],
            )

    def test_format_time_bucket_card_svg_renders_metric_panels(self):
        result = analyze_lines(
            [
                '10.0.0.1 - - [18/Apr/2026:09:00:05 +0000] "GET /api/report HTTP/1.1" 200 10 request_time=0.050 upstream_response_time=0.030',
                '10.0.0.2 - - [18/Apr/2026:09:00:40 +0000] "POST /api/report HTTP/1.1" 500 12 request_time=0.400 upstream_response_time=0.250',
                '10.0.0.3 - - [18/Apr/2026:09:01:10 +0000] "POST /slow HTTP/1.1" 502 13 request_time=0.600 upstream_response_time=0.350',
            ],
            top_n=2,
            time_bucket_granularity='minute',
        )
        annotations = normalize_card_annotations(
            [
                '2026-04-18T09:00:20Z=deploy|Deploy started',
                '2026-04-18T09:01:20Z=incident|Error budget burn',
            ],
            time_buckets=result['time_buckets'],
        )
        svg = format_time_bucket_card_svg(
            result,
            source_label='access.log',
            id_prefix='test-card',
            annotations=annotations,
        )
        self.assertIn('<svg', svg)
        self.assertIn('Observability trend snapshot', svg)
        self.assertIn('Requests / bucket', svg)
        self.assertIn('Error rate / bucket', svg)
        self.assertIn('Avg latency / bucket', svg)
        self.assertIn('Coverage: 2026-04-18 09:00 → 09:02 UTC', svg)
        self.assertIn('#2563eb', svg)
        self.assertIn('#dc2626', svg)

    def test_format_time_bucket_card_html_renders_bucket_table_and_facet_meta(self):
        result = analyze_lines(
            [
                '10.0.0.1 - - [18/Apr/2026:09:00:05 +0000] "POST /api/report HTTP/1.1" 500 10 request_time=0.450 upstream_response_time=0.300 env=prod region=us-east-1',
                '10.0.0.2 - - [18/Apr/2026:09:00:40 +0000] "POST /api/report HTTP/1.1" 502 12 request_time=0.550 upstream_response_time=0.400 env=prod region=us-east-1',
                '10.0.0.3 - - [18/Apr/2026:09:01:10 +0000] "POST /api/report HTTP/1.1" 500 13 request_time=0.250 upstream_response_time=0.100 env=staging',
            ],
            top_n=2,
            time_bucket_granularity='minute',
            facet_fields=['env', 'region'],
        )
        annotations = normalize_card_annotations(
            [
                '2026-04-18T09:00:30Z=deploy|Deploy started',
                '2026-04-18T09:01:10Z=incident|Incident spike',
            ],
            time_buckets=result['time_buckets'],
        )
        html = format_time_bucket_card_html(
            result,
            source_label='release-rollout.log',
            annotations=annotations,
        )
        self.assertIn('<!DOCTYPE html>', html)
        self.assertIn('Log trend card', html)
        self.assertIn('Facet fields', html)
        self.assertIn('env, region', html)
        self.assertIn('Annotation markers', html)
        self.assertIn('Deploy started', html)
        self.assertIn('Deploy', html)
        self.assertIn('Incident', html)
        self.assertIn('Events: 09:00:30', html)
        self.assertIn('<th>Annotation</th>', html)
        self.assertIn('<table>', html)
        self.assertIn('Bucket end', html)
        self.assertIn('<code>2026-04-18T09:01:00+00:00</code>', html)
        self.assertIn('<code>/api/report</code>', html)

    def test_format_facet_comparison_card_svg_renders_release_panels(self):
        result = analyze_lines(
            [
                '10.0.0.1 - - [18/Apr/2026:09:00:05 +0000] "GET /api/report HTTP/1.1" 200 10 request_time=0.050 upstream_response_time=0.030 env=prod',
                '10.0.0.2 - - [18/Apr/2026:09:00:40 +0000] "POST /api/report HTTP/1.1" 500 12 request_time=0.400 upstream_response_time=0.250 env=prod',
                '10.0.0.3 - - [18/Apr/2026:09:01:10 +0000] "POST /api/report HTTP/1.1" 200 13 request_time=0.120 upstream_response_time=0.090 env=staging',
                '10.0.0.4 - - [18/Apr/2026:09:01:45 +0000] "POST /api/report HTTP/1.1" 502 13 request_time=0.600 upstream_response_time=0.450 env=staging',
            ],
            top_n=2,
            time_bucket_granularity='minute',
            facet_compare_field='env',
            facet_compare_values=('prod', 'staging'),
        )
        svg = format_facet_comparison_card_svg(
            result['facet_comparison'],
            source_label='release-rollout.log',
            time_window=result['time_window'],
            id_prefix='compare-card',
        )
        self.assertIn('<svg', svg)
        self.assertIn('Release comparison snapshot', svg)
        self.assertIn('env=prod vs env=staging', svg)
        self.assertIn('Requests / bucket', svg)
        self.assertIn('Error-rate delta', svg)
        self.assertIn('Coverage: 2026-04-18 09:00 → 09:02 UTC', svg)

    def test_format_facet_comparison_card_html_renders_summary_and_bucket_tables(self):
        result = analyze_lines(
            [
                '10.0.0.1 - - [18/Apr/2026:09:00:05 +0000] "GET /api/report HTTP/1.1" 200 10 request_time=0.050 upstream_response_time=0.030 env=prod',
                '10.0.0.2 - - [18/Apr/2026:09:00:40 +0000] "POST /api/report HTTP/1.1" 500 12 request_time=0.400 upstream_response_time=0.250 env=prod',
                '10.0.0.3 - - [18/Apr/2026:09:01:10 +0000] "POST /api/report HTTP/1.1" 200 13 request_time=0.120 upstream_response_time=0.090 env=staging',
                '10.0.0.4 - - [18/Apr/2026:09:01:45 +0000] "POST /api/report HTTP/1.1" 502 13 request_time=0.600 upstream_response_time=0.450 env=staging',
            ],
            top_n=2,
            time_bucket_granularity='minute',
            facet_compare_field='env',
            facet_compare_values=('prod', 'staging'),
        )
        annotations = normalize_card_annotations(
            [
                '2026-04-18T09:00:20Z=deploy|Deploy started',
                '2026-04-18T09:01:40Z=rollback|Rollback triggered',
            ],
            time_buckets=result['facet_comparison']['time_buckets'],
        )
        html = format_facet_comparison_card_html(
            result['facet_comparison'],
            source_label='release-rollout.log',
            time_window=result['time_window'],
            annotations=annotations,
        )
        self.assertIn('<!DOCTYPE html>', html)
        self.assertIn('Release comparison card', html)
        self.assertIn('Summary delta table', html)
        self.assertIn('Aligned bucket rows', html)
        self.assertIn('Annotation markers', html)
        self.assertIn('Rollback triggered', html)
        self.assertIn('Deploy', html)
        self.assertIn('Rollback', html)
        self.assertIn('Events: 09:01:40', html)
        self.assertIn('env=prod', html)
        self.assertIn('env=staging', html)
        self.assertIn('<code>2026-04-18T09:01:00+00:00</code>', html)
        self.assertIn('staging minus prod', html)

    def test_format_facet_comparison_card_html_handles_summary_only_exports(self):
        result = analyze_lines(
            [
                '10.0.0.1 - - [18/Apr/2026:09:00:05 +0000] "GET /api/report HTTP/1.1" 200 10 request_time=0.050 upstream_response_time=0.030 env=prod',
                '10.0.0.2 - - [18/Apr/2026:09:00:40 +0000] "POST /api/report HTTP/1.1" 500 12 request_time=0.400 upstream_response_time=0.250 env=prod',
                '10.0.0.3 - - [18/Apr/2026:09:01:10 +0000] "POST /api/report HTTP/1.1" 200 13 request_time=0.120 upstream_response_time=0.090 env=staging',
            ],
            top_n=2,
            facet_compare_field='env',
            facet_compare_values=('prod', 'staging'),
        )
        html = format_facet_comparison_card_html(
            result['facet_comparison'],
            source_label='release-rollout.log',
            time_window=result['time_window'],
        )
        self.assertIn('Summary-only comparison', html)
        self.assertIn('No aligned bucket rows were produced for this run.', html)
        self.assertIn('Re-run with --time-bucket minute or --time-bucket hour', html)
        self.assertIn('Aligned buckets', html)

    def test_cli_json_output_includes_named_timing_summaries(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'access.log'
            log_path.write_text(
                textwrap.dedent(
                    '''\
                    10.0.0.1 - - [18/Apr/2026:09:00:00 +0000] "GET / HTTP/1.1" 200 10 "https://example.com/start" "Mozilla/5.0" request_time=0.125 upstream_response_time=0.080
                    10.0.0.2 - - [18/Apr/2026:09:01:00 +0000] "POST /login HTTP/1.1" 401 5 "-" "curl/8.0" request_time=0.250 upstream_response_time=0.120
                    '''
                ),
                encoding='utf-8',
            )
            completed = subprocess.run(
                [sys.executable, 'log_analyzer.py', str(log_path), '--format', 'json', '--top', '2'],
                cwd=Path(__file__).parent,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload['total_requests'], 2)
            self.assertEqual(payload['top_referrers'][0], ['https://example.com/start', 1])
            self.assertEqual(payload['latency_summary']['count'], 2)
            self.assertEqual(payload['latency_summary']['max_ms'], 250.0)
            self.assertEqual(payload['upstream_latency_summary']['average_ms'], 100.0)
            self.assertEqual(payload['path_latency_breakdown'][0]['path'], '/login')
            self.assertEqual(payload['upstream_path_latency_breakdown'][0]['path'], '/login')
            self.assertIsNone(payload['hotspot_filters'])
            self.assertIsNone(payload['time_window'])
            self.assertIsNone(payload['time_bucketing'])
            self.assertEqual(payload['time_buckets'], [])

    def test_cli_json_output_supports_hotspot_filters(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'access.log'
            log_path.write_text(
                textwrap.dedent(
                    '''\
                    10.0.0.1 - - [18/Apr/2026:09:00:00 +0000] "GET /health HTTP/1.1" 200 10 request_time=0.005 upstream_response_time=0.001
                    10.0.0.2 - - [18/Apr/2026:09:01:00 +0000] "POST /api/report HTTP/1.1" 500 12 request_time=0.600 upstream_response_time=0.500
                    10.0.0.3 - - [18/Apr/2026:09:02:00 +0000] "POST /api/report HTTP/1.1" 502 13 request_time=0.700 upstream_response_time=0.650
                    10.0.0.4 - - [18/Apr/2026:09:03:00 +0000] "GET /api/report HTTP/1.1" 500 14 request_time=0.450 upstream_response_time=0.300
                    '''
                ),
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    'log_analyzer.py',
                    str(log_path),
                    '--format',
                    'json',
                    '--top',
                    '3',
                    '--hotspot-status',
                    '500',
                    '--hotspot-status',
                    '502',
                    '--hotspot-method',
                    'POST',
                ],
                cwd=Path(__file__).parent,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload['hotspot_filters'], {'statuses': ['500', '502'], 'methods': ['POST']})
            self.assertEqual(payload['latency_summary']['count'], 4)
            self.assertEqual(len(payload['path_latency_breakdown']), 1)
            self.assertEqual(payload['path_latency_breakdown'][0]['path'], '/api/report')
            self.assertEqual(payload['path_latency_breakdown'][0]['count'], 2)
            self.assertEqual(payload['upstream_path_latency_breakdown'][0]['average_ms'], 575.0)

    def test_cli_json_output_supports_time_window_filters(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'access.log'
            log_path.write_text(
                textwrap.dedent(
                    '''\
                    10.0.0.1 - - [18/Apr/2026:08:59:00 +0000] "GET /before HTTP/1.1" 200 10 request_time=0.040
                    10.0.0.2 - - [18/Apr/2026:09:00:00 +0000] "GET /inside HTTP/1.1" 200 11 request_time=0.080 upstream_response_time=0.050
                    10.0.0.3 - - [18/Apr/2026:09:04:00 +0000] "POST /inside HTTP/1.1" 500 12 request_time=0.500 upstream_response_time=0.350
                    10.0.0.4 - - [18/Apr/2026:09:10:00 +0000] "GET /after HTTP/1.1" 200 13 request_time=0.060
                    '''
                ),
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    'log_analyzer.py',
                    str(log_path),
                    '--format',
                    'json',
                    '--top',
                    '2',
                    '--window-start',
                    '2026-04-18T09:00:00Z',
                    '--window-end',
                    '2026-04-18T09:05:00Z',
                ],
                cwd=Path(__file__).parent,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload['total_requests'], 2)
            self.assertEqual(payload['top_paths'][0], ['/inside', 2])
            self.assertEqual(payload['time_window']['start'], '2026-04-18T09:00:00+00:00')
            self.assertEqual(payload['time_window']['end'], '2026-04-18T09:05:00+00:00')
            self.assertEqual(payload['time_window']['matched_requests'], 2)
            self.assertEqual(payload['time_window']['excluded_requests'], 2)

    def test_cli_json_output_supports_time_buckets(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'access.log'
            log_path.write_text(
                textwrap.dedent(
                    '''\
                    10.0.0.1 - - [18/Apr/2026:09:00:05 +0000] "GET /api/report HTTP/1.1" 200 10 request_time=0.050 upstream_response_time=0.030
                    10.0.0.2 - - [18/Apr/2026:09:00:40 +0000] "POST /api/report HTTP/1.1" 500 12 request_time=0.400 upstream_response_time=0.250
                    10.0.0.3 - - [18/Apr/2026:09:01:10 +0000] "POST /slow HTTP/1.1" 502 13 request_time=0.600 upstream_response_time=0.350
                    '''
                ),
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    'log_analyzer.py',
                    str(log_path),
                    '--format',
                    'json',
                    '--time-bucket',
                    'minute',
                ],
                cwd=Path(__file__).parent,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload['time_bucketing'], {'bucket_count': 2, 'granularity': 'minute'})
            self.assertEqual(payload['time_buckets'][0]['bucket_start'], '2026-04-18T09:00:00+00:00')
            self.assertEqual(payload['time_buckets'][0]['request_count'], 2)
            self.assertEqual(payload['time_buckets'][0]['error_rate_pct'], 50.0)
            self.assertEqual(payload['time_buckets'][1]['bucket_start'], '2026-04-18T09:01:00+00:00')
            self.assertEqual(payload['time_buckets'][1]['error_count'], 1)

    def test_cli_json_output_supports_facet_breakdowns(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'access.log'
            log_path.write_text(
                textwrap.dedent(
                    '''\
                    10.0.0.1 - - [18/Apr/2026:09:00:05 +0000] "POST /api/report HTTP/1.1" 500 10 request_time=0.400 upstream_response_time=0.250 env=prod region=us-east-1
                    10.0.0.2 - - [18/Apr/2026:09:00:40 +0000] "POST /api/report HTTP/1.1" 502 12 request_time=0.500 upstream_response_time=0.300 env=prod region=us-east-1
                    10.0.0.3 - - [18/Apr/2026:09:01:10 +0000] "POST /api/report HTTP/1.1" 500 13 request_time=0.200 upstream_response_time=0.120 env=staging region=us-west-2
                    '''
                ),
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    'log_analyzer.py',
                    str(log_path),
                    '--format',
                    'json',
                    '--time-bucket',
                    'minute',
                    '--hotspot-status',
                    '500',
                    '--hotspot-status',
                    '502',
                    '--hotspot-method',
                    'POST',
                    '--facet-field',
                    'env',
                    '--facet-field',
                    'region',
                ],
                cwd=Path(__file__).parent,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload['faceting'], {'fields': ['env', 'region'], 'missing_value': '(missing)'})
            self.assertEqual(payload['path_latency_facet_breakdown'][0]['facets'], {'env': 'prod', 'region': 'us-east-1'})
            self.assertEqual(payload['path_latency_facet_breakdown'][1]['facets'], {'env': 'staging', 'region': 'us-west-2'})
            self.assertEqual(payload['time_bucket_facet_breakdown'][0]['request_count'], 2)
            self.assertEqual(payload['time_bucket_facet_breakdown'][0]['facets'], {'env': 'prod', 'region': 'us-east-1'})


    def test_cli_json_output_supports_facet_comparison(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'access.log'
            log_path.write_text(
                textwrap.dedent(
                    '''\
                    10.0.0.1 - - [18/Apr/2026:09:00:05 +0000] "GET /api/report HTTP/1.1" 200 10 request_time=0.050 upstream_response_time=0.030 env=prod
                    10.0.0.2 - - [18/Apr/2026:09:00:40 +0000] "POST /api/report HTTP/1.1" 500 12 request_time=0.400 upstream_response_time=0.250 env=prod
                    10.0.0.3 - - [18/Apr/2026:09:01:10 +0000] "POST /api/report HTTP/1.1" 200 13 request_time=0.200 upstream_response_time=0.120 env=staging
                    10.0.0.4 - - [18/Apr/2026:09:01:40 +0000] "POST /slow HTTP/1.1" 502 13 request_time=0.600 upstream_response_time=0.350 env=staging
                    '''
                ),
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    'log_analyzer.py',
                    str(log_path),
                    '--format',
                    'json',
                    '--time-bucket',
                    'minute',
                    '--facet-compare-field',
                    'env',
                    '--facet-compare-values',
                    'prod',
                    'staging',
                ],
                cwd=Path(__file__).parent,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            comparison = payload['facet_comparison']
            self.assertEqual(comparison['field'], 'env')
            self.assertEqual(comparison['left']['value'], 'prod')
            self.assertEqual(comparison['right']['value'], 'staging')
            self.assertEqual(comparison['delta']['average_latency_ms_delta'], 175)
            self.assertEqual(comparison['time_buckets'][0]['request_count_delta'], -2)
            self.assertEqual(comparison['time_buckets'][1]['right_top_path'], '/api/report')

    def test_cli_facet_compare_csv_exports_include_summary_and_bucket_rows(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'access.log'
            summary_csv = Path(tmpdir) / 'exports' / 'summary.csv'
            comparison_csv = Path(tmpdir) / 'exports' / 'facet-compare.csv'
            log_path.write_text(
                textwrap.dedent(
                    '''\
                    10.0.0.1 - - [18/Apr/2026:09:00:05 +0000] "GET /api/report HTTP/1.1" 200 10 request_time=0.050 upstream_response_time=0.030 env=prod
                    10.0.0.2 - - [18/Apr/2026:09:00:40 +0000] "POST /api/report HTTP/1.1" 500 12 request_time=0.400 upstream_response_time=0.250 env=prod
                    10.0.0.3 - - [18/Apr/2026:09:01:10 +0000] "POST /api/report HTTP/1.1" 200 13 request_time=0.200 upstream_response_time=0.120 env=staging
                    10.0.0.4 - - [18/Apr/2026:09:01:40 +0000] "POST /slow HTTP/1.1" 502 13 request_time=0.600 upstream_response_time=0.350 env=staging
                    '''
                ),
                encoding='utf-8',
            )
            subprocess.run(
                [
                    sys.executable,
                    'log_analyzer.py',
                    str(log_path),
                    '--format',
                    'json',
                    '--summary-csv',
                    str(summary_csv),
                    '--time-bucket',
                    'minute',
                    '--facet-compare-field',
                    'env',
                    '--facet-compare-values',
                    'prod',
                    'staging',
                    '--facet-compare-csv',
                    str(comparison_csv),
                ],
                cwd=Path(__file__).parent,
                check=True,
                capture_output=True,
                text=True,
            )

            with summary_csv.open(encoding='utf-8', newline='') as handle:
                summary_rows = list(csv.DictReader(handle))
            self.assertTrue(any(row['metric'] == 'facet_compare_field' and row['value'] == 'env' for row in summary_rows))
            self.assertTrue(any(row['metric'] == 'facet_compare_left_value' and row['value'] == 'prod' for row in summary_rows))
            self.assertTrue(any(row['metric'] == 'facet_compare_right_value' and row['value'] == 'staging' for row in summary_rows))
            self.assertTrue(any(row['metric'] == 'facet_compare_bucket_count' and row['value'] == '2' for row in summary_rows))

            with comparison_csv.open(encoding='utf-8', newline='') as handle:
                comparison_rows = list(csv.DictReader(handle))
            self.assertEqual(len(comparison_rows), 3)
            self.assertEqual(comparison_rows[0]['row_type'], 'summary')
            self.assertEqual(comparison_rows[0]['comparison_field'], 'env')
            self.assertEqual(comparison_rows[0]['left_value'], 'prod')
            self.assertEqual(comparison_rows[0]['right_value'], 'staging')
            self.assertEqual(comparison_rows[0]['p95_latency_ms_delta'], '197.5')
            self.assertEqual(comparison_rows[0]['max_upstream_latency_ms_delta'], '100')
            self.assertEqual(comparison_rows[1]['row_type'], 'bucket')
            self.assertEqual(comparison_rows[1]['bucket_start'], '2026-04-18T09:00:00+00:00')
            self.assertEqual(comparison_rows[1]['request_count_delta'], '-2')
            self.assertEqual(comparison_rows[2]['bucket_start'], '2026-04-18T09:01:00+00:00')
            self.assertEqual(comparison_rows[2]['right_request_count'], '2')

    def test_cli_rejects_incomplete_facet_compare_flags(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'access.log'
            comparison_csv = Path(tmpdir) / 'exports' / 'facet-compare.csv'
            log_path.write_text(
                '10.0.0.1 - - [18/Apr/2026:09:00:00 +0000] "GET /slow HTTP/1.1" 200 10 request_time=0.010 env=prod\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    'log_analyzer.py',
                    str(log_path),
                    '--facet-compare-field',
                    'env',
                    '--facet-compare-csv',
                    str(comparison_csv),
                ],
                cwd=Path(__file__).parent,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn('--facet-compare-csv requires --facet-compare-field and --facet-compare-values', completed.stderr)

    def test_cli_rejects_duplicate_facet_compare_values(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'access.log'
            log_path.write_text(
                '10.0.0.1 - - [18/Apr/2026:09:00:00 +0000] "GET /slow HTTP/1.1" 200 10 request_time=0.010 env=prod\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    'log_analyzer.py',
                    str(log_path),
                    '--facet-compare-field',
                    'env',
                    '--facet-compare-values',
                    'prod',
                    'prod',
                ],
                cwd=Path(__file__).parent,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn('--facet-compare-values must contain two distinct values', completed.stderr)

    def test_cli_time_window_accepts_naive_iso_as_utc(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'access.log'
            log_path.write_text(
                textwrap.dedent(
                    '''\
                    10.0.0.1 - - [18/Apr/2026:08:59:00 +0000] "GET /before HTTP/1.1" 200 10 request_time=0.040
                    10.0.0.2 - - [18/Apr/2026:09:00:00 +0000] "GET /inside HTTP/1.1" 200 11 request_time=0.080
                    '''
                ),
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    'log_analyzer.py',
                    str(log_path),
                    '--format',
                    'json',
                    '--window-start',
                    '2026-04-18T09:00:00',
                ],
                cwd=Path(__file__).parent,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload['total_requests'], 1)
            self.assertEqual(payload['time_window']['start'], '2026-04-18T09:00:00+00:00')

    def test_cli_csv_exports_include_upstream_latency_summary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'access.log'
            summary_csv = Path(tmpdir) / 'exports' / 'summary.csv'
            breakdown_csv = Path(tmpdir) / 'exports' / 'path-latency.csv'
            upstream_breakdown_csv = Path(tmpdir) / 'exports' / 'upstream-path-latency.csv'
            log_path.write_text(
                textwrap.dedent(
                    '''\
                    10.0.0.1 - - [18/Apr/2026:09:00:00 +0000] "GET /fast HTTP/1.1" 200 10 "-" "Mozilla/5.0" request_time=0.010 upstream_response_time=0.005
                    10.0.0.2 - - [18/Apr/2026:09:01:00 +0000] "GET /slow HTTP/1.1" 200 15 "https://example.com" "curl/8.0" request_time=0.450 upstream_response_time=0.300, 0.050
                    10.0.0.3 - - [18/Apr/2026:09:02:00 +0000] "GET /slow HTTP/1.1" 200 18 "https://example.com" "curl/8.0" request_time=0.500 upstream_response_time=0.320
                    '''
                ),
                encoding='utf-8',
            )
            subprocess.run(
                [
                    sys.executable,
                    'log_analyzer.py',
                    str(log_path),
                    '--format',
                    'json',
                    '--top',
                    '2',
                    '--latency-paths',
                    '1',
                    '--summary-csv',
                    str(summary_csv),
                    '--path-latency-csv',
                    str(breakdown_csv),
                    '--upstream-path-latency-csv',
                    str(upstream_breakdown_csv),
                ],
                cwd=Path(__file__).parent,
                check=True,
                capture_output=True,
                text=True,
            )

            with summary_csv.open(encoding='utf-8', newline='') as handle:
                rows = list(csv.DictReader(handle))
            self.assertTrue(any(row['section'] == 'summary' and row['metric'] == 'total_requests' and row['value'] == '3' for row in rows))
            self.assertTrue(any(row['section'] == 'top_paths' and row['key'] == '/slow' and row['count'] == '2' for row in rows))
            self.assertTrue(any(row['section'] == 'latency_summary' and row['metric'] == 'p95_ms' for row in rows))
            self.assertTrue(any(row['section'] == 'upstream_latency_summary' and row['metric'] == 'max_ms' and row['value'] == '350.0' for row in rows))

            with breakdown_csv.open(encoding='utf-8', newline='') as handle:
                latency_rows = list(csv.DictReader(handle))
            self.assertEqual(len(latency_rows), 1)
            self.assertEqual(latency_rows[0]['path'], '/slow')
            self.assertEqual(latency_rows[0]['count'], '2')
            self.assertEqual(latency_rows[0]['average_ms'], '475.0')
            self.assertEqual(latency_rows[0]['status_filter'], '')
            self.assertEqual(latency_rows[0]['method_filter'], '')
            self.assertEqual(latency_rows[0]['window_start'], '')
            self.assertEqual(latency_rows[0]['window_end'], '')

            with upstream_breakdown_csv.open(encoding='utf-8', newline='') as handle:
                upstream_rows = list(csv.DictReader(handle))
            self.assertEqual(len(upstream_rows), 1)
            self.assertEqual(upstream_rows[0]['path'], '/slow')
            self.assertEqual(upstream_rows[0]['count'], '2')
            self.assertEqual(upstream_rows[0]['average_ms'], '335.0')

    def test_cli_csv_exports_record_hotspot_filter_metadata(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'access.log'
            breakdown_csv = Path(tmpdir) / 'exports' / 'path-latency.csv'
            upstream_breakdown_csv = Path(tmpdir) / 'exports' / 'upstream-path-latency.csv'
            log_path.write_text(
                textwrap.dedent(
                    '''\
                    10.0.0.1 - - [18/Apr/2026:09:00:00 +0000] "POST /api/report HTTP/1.1" 500 15 request_time=0.450 upstream_response_time=0.300
                    10.0.0.2 - - [18/Apr/2026:09:01:00 +0000] "POST /api/report HTTP/1.1" 502 18 request_time=0.500 upstream_response_time=0.320
                    10.0.0.3 - - [18/Apr/2026:09:02:00 +0000] "GET /health HTTP/1.1" 200 10 request_time=0.010 upstream_response_time=0.005
                    '''
                ),
                encoding='utf-8',
            )
            subprocess.run(
                [
                    sys.executable,
                    'log_analyzer.py',
                    str(log_path),
                    '--format',
                    'json',
                    '--top',
                    '2',
                    '--hotspot-status',
                    '500',
                    '--hotspot-status',
                    '502',
                    '--hotspot-method',
                    'POST',
                    '--path-latency-csv',
                    str(breakdown_csv),
                    '--upstream-path-latency-csv',
                    str(upstream_breakdown_csv),
                ],
                cwd=Path(__file__).parent,
                check=True,
                capture_output=True,
                text=True,
            )

            with breakdown_csv.open(encoding='utf-8', newline='') as handle:
                latency_rows = list(csv.DictReader(handle))
            self.assertEqual(len(latency_rows), 1)
            self.assertEqual(latency_rows[0]['path'], '/api/report')
            self.assertEqual(latency_rows[0]['status_filter'], '500|502')
            self.assertEqual(latency_rows[0]['method_filter'], 'POST')

            with upstream_breakdown_csv.open(encoding='utf-8', newline='') as handle:
                upstream_rows = list(csv.DictReader(handle))
            self.assertEqual(len(upstream_rows), 1)
            self.assertEqual(upstream_rows[0]['path'], '/api/report')
            self.assertEqual(upstream_rows[0]['status_filter'], '500|502')
            self.assertEqual(upstream_rows[0]['method_filter'], 'POST')

    def test_cli_csv_exports_record_time_window_metadata(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'access.log'
            summary_csv = Path(tmpdir) / 'exports' / 'summary.csv'
            breakdown_csv = Path(tmpdir) / 'exports' / 'path-latency.csv'
            log_path.write_text(
                textwrap.dedent(
                    '''\
                    10.0.0.1 - - [18/Apr/2026:08:59:00 +0000] "GET /before HTTP/1.1" 200 10 request_time=0.040
                    10.0.0.2 - - [18/Apr/2026:09:00:00 +0000] "GET /inside HTTP/1.1" 200 11 request_time=0.080
                    10.0.0.3 - - [18/Apr/2026:09:04:00 +0000] "POST /inside HTTP/1.1" 500 12 request_time=0.500
                    '''
                ),
                encoding='utf-8',
            )
            subprocess.run(
                [
                    sys.executable,
                    'log_analyzer.py',
                    str(log_path),
                    '--format',
                    'json',
                    '--top',
                    '2',
                    '--window-start',
                    '2026-04-18T09:00:00Z',
                    '--window-end',
                    '2026-04-18T09:05:00Z',
                    '--summary-csv',
                    str(summary_csv),
                    '--path-latency-csv',
                    str(breakdown_csv),
                ],
                cwd=Path(__file__).parent,
                check=True,
                capture_output=True,
                text=True,
            )

            with summary_csv.open(encoding='utf-8', newline='') as handle:
                rows = list(csv.DictReader(handle))
            self.assertTrue(any(row['metric'] == 'time_window_start' and row['value'] == '2026-04-18T09:00:00+00:00' for row in rows))
            self.assertTrue(any(row['metric'] == 'time_window_end' and row['value'] == '2026-04-18T09:05:00+00:00' for row in rows))
            self.assertTrue(any(row['metric'] == 'time_window_excluded_requests' and row['value'] == '1' for row in rows))

            with breakdown_csv.open(encoding='utf-8', newline='') as handle:
                latency_rows = list(csv.DictReader(handle))
            self.assertEqual(latency_rows[0]['window_start'], '2026-04-18T09:00:00+00:00')
            self.assertEqual(latency_rows[0]['window_end'], '2026-04-18T09:05:00+00:00')

    def test_cli_time_bucket_csv_exports_record_bucket_and_window_metadata(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'access.log'
            summary_csv = Path(tmpdir) / 'exports' / 'summary.csv'
            bucket_csv = Path(tmpdir) / 'exports' / 'time-buckets.csv'
            log_path.write_text(
                textwrap.dedent(
                    '''\
                    10.0.0.1 - - [18/Apr/2026:08:59:00 +0000] "GET /before HTTP/1.1" 200 10 request_time=0.040
                    10.0.0.2 - - [18/Apr/2026:09:00:05 +0000] "GET /api/report HTTP/1.1" 200 11 request_time=0.080 upstream_response_time=0.050
                    10.0.0.3 - - [18/Apr/2026:09:00:40 +0000] "POST /api/report HTTP/1.1" 500 12 request_time=0.500 upstream_response_time=0.350
                    10.0.0.4 - - [18/Apr/2026:09:01:10 +0000] "GET /after HTTP/1.1" 200 13 request_time=0.060
                    '''
                ),
                encoding='utf-8',
            )
            subprocess.run(
                [
                    sys.executable,
                    'log_analyzer.py',
                    str(log_path),
                    '--format',
                    'json',
                    '--window-start',
                    '2026-04-18T09:00:00Z',
                    '--window-end',
                    '2026-04-18T09:00:59Z',
                    '--time-bucket',
                    'minute',
                    '--summary-csv',
                    str(summary_csv),
                    '--time-bucket-csv',
                    str(bucket_csv),
                ],
                cwd=Path(__file__).parent,
                check=True,
                capture_output=True,
                text=True,
            )

            with summary_csv.open(encoding='utf-8', newline='') as handle:
                summary_rows = list(csv.DictReader(handle))
            self.assertTrue(any(row['metric'] == 'time_bucket_granularity' and row['value'] == 'minute' for row in summary_rows))
            self.assertTrue(any(row['metric'] == 'time_bucket_count' and row['value'] == '1' for row in summary_rows))

            with bucket_csv.open(encoding='utf-8', newline='') as handle:
                bucket_rows = list(csv.DictReader(handle))
            self.assertEqual(len(bucket_rows), 1)
            self.assertEqual(bucket_rows[0]['granularity'], 'minute')
            self.assertEqual(bucket_rows[0]['bucket_start'], '2026-04-18T09:00:00+00:00')
            self.assertEqual(bucket_rows[0]['bucket_end'], '2026-04-18T09:01:00+00:00')
            self.assertEqual(bucket_rows[0]['request_count'], '2')
            self.assertEqual(bucket_rows[0]['error_count'], '1')
            self.assertEqual(bucket_rows[0]['error_rate_pct'], '50.0')
            self.assertEqual(bucket_rows[0]['top_path'], '/api/report')
            self.assertEqual(bucket_rows[0]['top_path_count'], '2')
            self.assertEqual(bucket_rows[0]['latency_sample_count'], '2')
            self.assertEqual(bucket_rows[0]['average_latency_ms'], '290.0')
            self.assertEqual(bucket_rows[0]['average_upstream_latency_ms'], '200.0')
            self.assertEqual(bucket_rows[0]['window_start'], '2026-04-18T09:00:00+00:00')
            self.assertEqual(bucket_rows[0]['window_end'], '2026-04-18T09:00:59+00:00')

    def test_cli_facet_csv_exports_include_named_field_metadata(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'access.log'
            summary_csv = Path(tmpdir) / 'exports' / 'summary.csv'
            path_facet_csv = Path(tmpdir) / 'exports' / 'path-latency-facets.csv'
            upstream_facet_csv = Path(tmpdir) / 'exports' / 'upstream-path-latency-facets.csv'
            bucket_facet_csv = Path(tmpdir) / 'exports' / 'time-bucket-facets.csv'
            log_path.write_text(
                textwrap.dedent(
                    '''\\
                    10.0.0.1 - - [18/Apr/2026:09:00:05 +0000] "POST /api/report HTTP/1.1" 500 10 request_time=0.450 upstream_response_time=0.300 env=prod region=us-east-1
                    10.0.0.2 - - [18/Apr/2026:09:00:40 +0000] "POST /api/report HTTP/1.1" 502 12 request_time=0.550 upstream_response_time=0.400 env=prod region=us-east-1
                    10.0.0.3 - - [18/Apr/2026:09:01:10 +0000] "POST /api/report HTTP/1.1" 500 13 request_time=0.250 upstream_response_time=0.100 env=staging
                    '''
                ),
                encoding='utf-8',
            )
            subprocess.run(
                [
                    sys.executable,
                    'log_analyzer.py',
                    str(log_path),
                    '--format',
                    'json',
                    '--summary-csv',
                    str(summary_csv),
                    '--path-latency-facet-csv',
                    str(path_facet_csv),
                    '--upstream-path-latency-facet-csv',
                    str(upstream_facet_csv),
                    '--time-bucket',
                    'minute',
                    '--time-bucket-facet-csv',
                    str(bucket_facet_csv),
                    '--hotspot-status',
                    '500',
                    '--hotspot-status',
                    '502',
                    '--hotspot-method',
                    'POST',
                    '--facet-field',
                    'env',
                    '--facet-field',
                    'region',
                ],
                cwd=Path(__file__).parent,
                check=True,
                capture_output=True,
                text=True,
            )

            with summary_csv.open(encoding='utf-8', newline='') as handle:
                summary_rows = list(csv.DictReader(handle))
            self.assertTrue(any(row['metric'] == 'facet_fields' and row['value'] == 'env|region' for row in summary_rows))
            self.assertTrue(any(row['metric'] == 'missing_facet_value' and row['value'] == '(missing)' for row in summary_rows))
            self.assertTrue(any(row['metric'] == 'path_latency_facet_row_count' and row['value'] == '2' for row in summary_rows))
            self.assertTrue(any(row['metric'] == 'time_bucket_facet_row_count' and row['value'] == '2' for row in summary_rows))

            with path_facet_csv.open(encoding='utf-8', newline='') as handle:
                path_rows = list(csv.DictReader(handle))
            self.assertEqual(len(path_rows), 2)
            self.assertEqual(path_rows[0]['path'], '/api/report')
            self.assertEqual(path_rows[0]['facet_label'], 'env=prod, region=us-east-1')
            self.assertEqual(path_rows[0]['facet_env'], 'prod')
            self.assertEqual(path_rows[0]['facet_region'], 'us-east-1')
            self.assertEqual(path_rows[0]['average_ms'], '500.0')
            self.assertEqual(path_rows[1]['facet_region'], '(missing)')
            self.assertEqual(path_rows[1]['status_filter'], '500|502')
            self.assertEqual(path_rows[1]['method_filter'], 'POST')

            with upstream_facet_csv.open(encoding='utf-8', newline='') as handle:
                upstream_rows = list(csv.DictReader(handle))
            self.assertEqual(len(upstream_rows), 2)
            self.assertEqual(upstream_rows[0]['facet_env'], 'prod')
            self.assertEqual(upstream_rows[0]['average_ms'], '350.0')
            self.assertEqual(upstream_rows[1]['facet_region'], '(missing)')

            with bucket_facet_csv.open(encoding='utf-8', newline='') as handle:
                bucket_rows = list(csv.DictReader(handle))
            self.assertEqual(len(bucket_rows), 2)
            self.assertEqual(bucket_rows[0]['granularity'], 'minute')
            self.assertEqual(bucket_rows[0]['bucket_start'], '2026-04-18T09:00:00+00:00')
            self.assertEqual(bucket_rows[0]['facet_env'], 'prod')
            self.assertEqual(bucket_rows[0]['facet_region'], 'us-east-1')
            self.assertEqual(bucket_rows[0]['request_count'], '2')
            self.assertEqual(bucket_rows[1]['facet_env'], 'staging')
            self.assertEqual(bucket_rows[1]['facet_region'], '(missing)')

    def test_cli_text_output_mentions_upstream_latency_summary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'access.log'
            log_path.write_text(
                '10.0.0.1 - - [18/Apr/2026:09:00:00 +0000] "GET /slow HTTP/1.1" 200 10 "https://example.com" "Mozilla/5.0" request_time=0.010 upstream_response_time=0.007\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [sys.executable, 'log_analyzer.py', str(log_path), '--format', 'text'],
                cwd=Path(__file__).parent,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn('Log Analysis Summary', completed.stdout)
            self.assertIn('Top referrers:', completed.stdout)
            self.assertIn('Latency summary (ms):', completed.stdout)
            self.assertIn('Upstream latency summary (ms):', completed.stdout)
            self.assertIn('Per-path latency hotspots (ms):', completed.stdout)
            self.assertIn('Per-path upstream latency hotspots (ms):', completed.stdout)

    def test_cli_time_bucket_card_exports_generate_svg_and_html(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'access.log'
            svg_path = Path(tmpdir) / 'exports' / 'trend-card.svg'
            html_path = Path(tmpdir) / 'exports' / 'trend-card.html'
            log_path.write_text(
                textwrap.dedent(
                    '''\
                    10.0.0.1 - - [18/Apr/2026:09:00:05 +0000] "GET /api/report HTTP/1.1" 200 10 request_time=0.050 upstream_response_time=0.030
                    10.0.0.2 - - [18/Apr/2026:09:00:40 +0000] "POST /api/report HTTP/1.1" 500 12 request_time=0.400 upstream_response_time=0.250
                    10.0.0.3 - - [18/Apr/2026:09:01:10 +0000] "POST /slow HTTP/1.1" 502 13 request_time=0.600 upstream_response_time=0.350
                    '''
                ),
                encoding='utf-8',
            )
            subprocess.run(
                [
                    sys.executable,
                    'log_analyzer.py',
                    str(log_path),
                    '--time-bucket',
                    'minute',
                    '--time-bucket-card-svg',
                    str(svg_path),
                    '--time-bucket-card-html',
                    str(html_path),
                ],
                cwd=Path(__file__).parent,
                check=True,
                capture_output=True,
                text=True,
            )
            svg_text = svg_path.read_text(encoding='utf-8')
            html_text = html_path.read_text(encoding='utf-8')
            self.assertIn('<svg', svg_text)
            self.assertIn('Observability trend snapshot', svg_text)
            self.assertIn('<!DOCTYPE html>', html_text)
            self.assertIn('Bucket summary table', html_text)
            self.assertIn('<code>/api/report</code>', html_text)

    def test_cli_time_bucket_card_exports_support_annotations(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'access.log'
            svg_path = Path(tmpdir) / 'exports' / 'trend-card.svg'
            html_path = Path(tmpdir) / 'exports' / 'trend-card.html'
            log_path.write_text(
                textwrap.dedent(
                    '''\
                    10.0.0.1 - - [18/Apr/2026:09:00:05 +0000] "GET /api/report HTTP/1.1" 200 10 request_time=0.050 upstream_response_time=0.030
                    10.0.0.2 - - [18/Apr/2026:09:00:40 +0000] "POST /api/report HTTP/1.1" 500 12 request_time=0.400 upstream_response_time=0.250
                    10.0.0.3 - - [18/Apr/2026:09:01:10 +0000] "POST /slow HTTP/1.1" 502 13 request_time=0.600 upstream_response_time=0.350
                    '''
                ),
                encoding='utf-8',
            )
            subprocess.run(
                [
                    sys.executable,
                    'log_analyzer.py',
                    str(log_path),
                    '--time-bucket',
                    'minute',
                    '--time-bucket-card-svg',
                    str(svg_path),
                    '--time-bucket-card-html',
                    str(html_path),
                    '--card-annotation',
                    '2026-04-18T09:00:20Z=deploy|Deploy started',
                    '--card-annotation',
                    '2026-04-18T09:01:10Z=rollback|Rollback triggered',
                ],
                cwd=Path(__file__).parent,
                check=True,
                capture_output=True,
                text=True,
            )
            svg_text = svg_path.read_text(encoding='utf-8')
            html_text = html_path.read_text(encoding='utf-8')
            self.assertIn('Annotations: 1. 09:00 Deploy started', svg_text)
            self.assertIn('>1</text>', svg_text)
            self.assertIn('Annotation markers', html_text)
            self.assertIn('Events: 09:00:20', html_text)
            self.assertIn('Rollback triggered', html_text)

    def test_cli_rejects_time_bucket_card_export_without_granularity(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'access.log'
            svg_path = Path(tmpdir) / 'exports' / 'trend-card.svg'
            log_path.write_text(
                '10.0.0.1 - - [18/Apr/2026:09:00:00 +0000] "GET /slow HTTP/1.1" 200 10 request_time=0.010\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    'log_analyzer.py',
                    str(log_path),
                    '--time-bucket-card-svg',
                    str(svg_path),
                ],
                cwd=Path(__file__).parent,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn('--time-bucket-card-svg requires --time-bucket', completed.stderr)

    def test_cli_facet_comparison_card_exports_generate_svg_and_html(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'access.log'
            svg_path = Path(tmpdir) / 'exports' / 'compare-card.svg'
            html_path = Path(tmpdir) / 'exports' / 'compare-card.html'
            log_path.write_text(
                textwrap.dedent(
                    '''\
                    10.0.0.1 - - [18/Apr/2026:09:00:05 +0000] "GET /api/report HTTP/1.1" 200 10 request_time=0.050 upstream_response_time=0.030 env=prod
                    10.0.0.2 - - [18/Apr/2026:09:00:40 +0000] "POST /api/report HTTP/1.1" 500 12 request_time=0.400 upstream_response_time=0.250 env=prod
                    10.0.0.3 - - [18/Apr/2026:09:01:10 +0000] "POST /api/report HTTP/1.1" 200 13 request_time=0.120 upstream_response_time=0.090 env=staging
                    10.0.0.4 - - [18/Apr/2026:09:01:45 +0000] "POST /api/report HTTP/1.1" 502 13 request_time=0.600 upstream_response_time=0.450 env=staging
                    '''
                ),
                encoding='utf-8',
            )
            subprocess.run(
                [
                    sys.executable,
                    'log_analyzer.py',
                    str(log_path),
                    '--time-bucket',
                    'minute',
                    '--facet-compare-field',
                    'env',
                    '--facet-compare-values',
                    'prod',
                    'staging',
                    '--facet-compare-card-svg',
                    str(svg_path),
                    '--facet-compare-card-html',
                    str(html_path),
                ],
                cwd=Path(__file__).parent,
                check=True,
                capture_output=True,
                text=True,
            )
            svg_text = svg_path.read_text(encoding='utf-8')
            html_text = html_path.read_text(encoding='utf-8')
            self.assertIn('<svg', svg_text)
            self.assertIn('Release comparison snapshot', svg_text)
            self.assertIn('<!DOCTYPE html>', html_text)
            self.assertIn('Summary delta table', html_text)
            self.assertIn('Aligned bucket rows', html_text)

    def test_cli_facet_comparison_card_exports_support_annotations(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'access.log'
            svg_path = Path(tmpdir) / 'exports' / 'compare-card.svg'
            html_path = Path(tmpdir) / 'exports' / 'compare-card.html'
            log_path.write_text(
                textwrap.dedent(
                    '''\
                    10.0.0.1 - - [18/Apr/2026:09:00:05 +0000] "GET /api/report HTTP/1.1" 200 10 request_time=0.050 upstream_response_time=0.030 env=prod
                    10.0.0.2 - - [18/Apr/2026:09:00:40 +0000] "POST /api/report HTTP/1.1" 500 12 request_time=0.400 upstream_response_time=0.250 env=prod
                    10.0.0.3 - - [18/Apr/2026:09:01:10 +0000] "POST /api/report HTTP/1.1" 200 13 request_time=0.120 upstream_response_time=0.090 env=staging
                    10.0.0.4 - - [18/Apr/2026:09:01:45 +0000] "POST /api/report HTTP/1.1" 502 13 request_time=0.600 upstream_response_time=0.450 env=staging
                    '''
                ),
                encoding='utf-8',
            )
            subprocess.run(
                [
                    sys.executable,
                    'log_analyzer.py',
                    str(log_path),
                    '--time-bucket',
                    'minute',
                    '--facet-compare-field',
                    'env',
                    '--facet-compare-values',
                    'prod',
                    'staging',
                    '--facet-compare-card-svg',
                    str(svg_path),
                    '--facet-compare-card-html',
                    str(html_path),
                    '--card-annotation',
                    '2026-04-18T09:00:20Z=deploy|Deploy started',
                    '--card-annotation',
                    '2026-04-18T09:01:40Z=rollback|Rollback triggered',
                ],
                cwd=Path(__file__).parent,
                check=True,
                capture_output=True,
                text=True,
            )
            svg_text = svg_path.read_text(encoding='utf-8')
            html_text = html_path.read_text(encoding='utf-8')
            self.assertIn('Annotations: 1. 09:00 Deploy started', svg_text)
            self.assertIn('[Deploy]', svg_text)
            self.assertIn('Annotation markers', html_text)
            self.assertIn('Deploy', html_text)
            self.assertIn('Rollback', html_text)
            self.assertIn('Events: 09:01:40', html_text)
            self.assertIn('Rollback triggered', html_text)

    def test_cli_rejects_facet_comparison_card_exports_without_compare_args(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'access.log'
            svg_path = Path(tmpdir) / 'exports' / 'compare-card.svg'
            log_path.write_text(
                '10.0.0.1 - - [18/Apr/2026:09:00:00 +0000] "GET /slow HTTP/1.1" 200 10 request_time=0.010 env=prod\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    'log_analyzer.py',
                    str(log_path),
                    '--facet-compare-card-svg',
                    str(svg_path),
                ],
                cwd=Path(__file__).parent,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn('comparison-card export flags require --facet-compare-field and --facet-compare-values', completed.stderr)

    def test_cli_rejects_card_annotation_without_card_export(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'access.log'
            log_path.write_text(
                '10.0.0.1 - - [18/Apr/2026:09:00:00 +0000] "GET /slow HTTP/1.1" 200 10 request_time=0.010\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    'log_analyzer.py',
                    str(log_path),
                    '--time-bucket',
                    'minute',
                    '--card-annotation',
                    '2026-04-18T09:00:00Z=Deploy started',
                ],
                cwd=Path(__file__).parent,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn('--card-annotation requires at least one card export flag', completed.stderr)

    def test_cli_rejects_card_annotation_outside_bucket_range(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'access.log'
            svg_path = Path(tmpdir) / 'exports' / 'trend-card.svg'
            log_path.write_text(
                '10.0.0.1 - - [18/Apr/2026:09:00:00 +0000] "GET /slow HTTP/1.1" 200 10 request_time=0.010\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    'log_analyzer.py',
                    str(log_path),
                    '--time-bucket',
                    'minute',
                    '--time-bucket-card-svg',
                    str(svg_path),
                    '--card-annotation',
                    '2026-04-18T09:05:00Z=Too late',
                ],
                cwd=Path(__file__).parent,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn('falls outside the current bucket coverage', completed.stderr)

    def test_cli_rejects_invalid_hotspot_status(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'access.log'
            log_path.write_text(
                '10.0.0.1 - - [18/Apr/2026:09:00:00 +0000] "GET /slow HTTP/1.1" 200 10 request_time=0.010\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    'log_analyzer.py',
                    str(log_path),
                    '--hotspot-status',
                    'oops',
                ],
                cwd=Path(__file__).parent,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn('--hotspot-status must be a 3-digit status code', completed.stderr)

    def test_cli_rejects_invalid_window_start(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'access.log'
            log_path.write_text(
                '10.0.0.1 - - [18/Apr/2026:09:00:00 +0000] "GET /slow HTTP/1.1" 200 10 request_time=0.010\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    'log_analyzer.py',
                    str(log_path),
                    '--window-start',
                    'not-a-time',
                ],
                cwd=Path(__file__).parent,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn('--window-start must be ISO-8601 or a common-log timestamp (naive ISO values are treated as UTC)', completed.stderr)

    def test_cli_rejects_inverted_time_window(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'access.log'
            log_path.write_text(
                '10.0.0.1 - - [18/Apr/2026:09:00:00 +0000] "GET /slow HTTP/1.1" 200 10 request_time=0.010\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    'log_analyzer.py',
                    str(log_path),
                    '--window-start',
                    '2026-04-18T09:05:00Z',
                    '--window-end',
                    '2026-04-18T09:00:00Z',
                ],
                cwd=Path(__file__).parent,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn('--window-start must be less than or equal to --window-end', completed.stderr)

    def test_cli_rejects_invalid_facet_field_name(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'access.log'
            log_path.write_text(
                '10.0.0.1 - - [18/Apr/2026:09:00:00 +0000] "GET /slow HTTP/1.1" 200 10 request_time=0.010 env=prod\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    'log_analyzer.py',
                    str(log_path),
                    '--facet-field',
                    'env-name',
                ],
                cwd=Path(__file__).parent,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn('--facet-field must look like a named log field', completed.stderr)

    def test_cli_rejects_facet_csv_without_facet_field(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'access.log'
            facet_csv = Path(tmpdir) / 'exports' / 'path-facets.csv'
            log_path.write_text(
                '10.0.0.1 - - [18/Apr/2026:09:00:00 +0000] "GET /slow HTTP/1.1" 200 10 request_time=0.010 env=prod\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    'log_analyzer.py',
                    str(log_path),
                    '--path-latency-facet-csv',
                    str(facet_csv),
                ],
                cwd=Path(__file__).parent,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn('facet-specific export flags require at least one --facet-field', completed.stderr)

    def test_cli_rejects_time_bucket_facet_csv_without_granularity(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'access.log'
            bucket_csv = Path(tmpdir) / 'exports' / 'time-bucket-facets.csv'
            log_path.write_text(
                '10.0.0.1 - - [18/Apr/2026:09:00:00 +0000] "GET /slow HTTP/1.1" 200 10 request_time=0.010 env=prod\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    'log_analyzer.py',
                    str(log_path),
                    '--facet-field',
                    'env',
                    '--time-bucket-facet-csv',
                    str(bucket_csv),
                ],
                cwd=Path(__file__).parent,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn('--time-bucket-facet-csv requires --time-bucket', completed.stderr)

    def test_cli_rejects_time_bucket_csv_without_granularity(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'access.log'
            bucket_csv = Path(tmpdir) / 'exports' / 'time-buckets.csv'
            log_path.write_text(
                '10.0.0.1 - - [18/Apr/2026:09:00:00 +0000] "GET /slow HTTP/1.1" 200 10 request_time=0.010\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    'log_analyzer.py',
                    str(log_path),
                    '--time-bucket-csv',
                    str(bucket_csv),
                ],
                cwd=Path(__file__).parent,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn('--time-bucket-csv requires --time-bucket', completed.stderr)


if __name__ == '__main__':
    unittest.main()
