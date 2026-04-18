import csv
import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from log_analyzer import analyze_lines, format_text_report, parse_line


class LogAnalyzerTests(unittest.TestCase):
    def test_parse_line_supports_dash_bytes(self):
        parsed = parse_line('10.0.0.1 - - [x] "GET / HTTP/1.1" 304 -')
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.bytes_sent, 0)
        self.assertEqual(parsed.method, 'GET')
        self.assertIsNone(parsed.referrer)
        self.assertIsNone(parsed.latency_ms)
        self.assertIsNone(parsed.upstream_response_time_ms)

    def test_parse_line_supports_combined_logs_with_latency(self):
        parsed = parse_line(
            '10.0.0.1 - - [x] "GET /docs HTTP/1.1" 200 123 '
            '"https://example.com/start" "Mozilla/5.0" 0.245'
        )
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.referrer, 'https://example.com/start')
        self.assertEqual(parsed.user_agent, 'Mozilla/5.0')
        self.assertEqual(parsed.latency_ms, 245.0)
        self.assertIsNone(parsed.request_time_ms)

    def test_parse_line_supports_microsecond_latency(self):
        parsed = parse_line(
            '10.0.0.2 - - [x] "POST /ingest HTTP/1.1" 201 42 '
            '"-" "curl/8.0" 12345'
        )
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.latency_ms, 12.345)
        self.assertEqual(parsed.user_agent, 'curl/8.0')
        self.assertIsNone(parsed.referrer)

    def test_parse_line_supports_named_nginx_timing_fields(self):
        parsed = parse_line(
            '10.0.0.3 - - [x] "GET /api/report HTTP/1.1" 200 321 '
            '"https://example.com" "Mozilla/5.0" '
            'request_time=0.245 upstream_response_time=0.201 upstream_connect_time=0.010'
        )
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.latency_ms, 245.0)
        self.assertEqual(parsed.request_time_ms, 245.0)
        self.assertEqual(parsed.upstream_response_time_ms, 201.0)

    def test_parse_line_sums_multi_attempt_upstream_response_times(self):
        parsed = parse_line(
            '10.0.0.4 - - [x] "GET /retry HTTP/1.1" 200 64 '
            'request_time=0.400 upstream_response_time=0.050, 0.125:0.075'
        )
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.request_time_ms, 400.0)
        self.assertEqual(parsed.upstream_response_time_ms, 250.0)
        self.assertEqual(parsed.latency_ms, 400.0)

    def test_parse_line_ignores_invalid_named_timing_values(self):
        parsed = parse_line(
            '10.0.0.5 - - [x] "GET /broken HTTP/1.1" 200 32 '
            'request_time=oops upstream_response_time=0.010'
        )
        self.assertIsNotNone(parsed)
        self.assertIsNone(parsed.request_time_ms)
        self.assertIsNone(parsed.latency_ms)
        self.assertEqual(parsed.upstream_response_time_ms, 10.0)

    def test_analyze_lines_counts_combined_fields_and_latency(self):
        lines = [
            '10.0.0.1 - - [x] "GET / HTTP/1.1" 200 10 "https://example.com/start" "Mozilla/5.0" 0.100',
            '10.0.0.2 - - [x] "POST /login HTTP/1.1" 401 5 "https://example.com/start" "curl/8.0" 0.350',
            '10.0.0.1 - - [x] "GET / HTTP/1.1" 200 15',
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

    def test_analyze_lines_reports_upstream_latency_summary_from_named_fields(self):
        lines = [
            '10.0.0.1 - - [x] "GET /api/report HTTP/1.1" 200 100 "-" "agent-a" request_time=0.120 upstream_response_time=0.080',
            '10.0.0.2 - - [x] "GET /api/report HTTP/1.1" 200 120 "-" "agent-a" request_time=0.180 upstream_response_time=0.050, 0.070',
            '10.0.0.3 - - [x] "GET /status HTTP/1.1" 200 90 request_time=0.040 upstream_response_time=-',
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
            '10.0.0.1 - - [x] "GET /fast HTTP/1.1" 200 10 "-" "agent-a" 0.010',
            '10.0.0.2 - - [x] "GET /fast HTTP/1.1" 200 11 "-" "agent-a" 0.015',
            '10.0.0.3 - - [x] "GET /steady HTTP/1.1" 200 12 "-" "agent-b" 0.200',
            '10.0.0.4 - - [x] "GET /steady HTTP/1.1" 200 13 "-" "agent-b" 0.220',
            '10.0.0.5 - - [x] "GET /hot HTTP/1.1" 200 14 "-" "agent-c" 0.450',
        ]
        result = analyze_lines(lines, top_n=2, latency_top_n=2)
        self.assertEqual([row['path'] for row in result['path_latency_breakdown']], ['/hot', '/steady'])
        self.assertEqual(result['path_latency_breakdown'][1]['count'], 2)
        self.assertEqual(result['path_latency_breakdown'][1]['p95_ms'], 219.0)

    def test_analyze_lines_limits_and_sorts_upstream_path_latency_breakdown(self):
        lines = [
            '10.0.0.1 - - [x] "GET /fast HTTP/1.1" 200 10 request_time=0.050 upstream_response_time=0.010',
            '10.0.0.2 - - [x] "GET /retry HTTP/1.1" 200 11 request_time=0.300 upstream_response_time=0.080, 0.070',
            '10.0.0.3 - - [x] "GET /retry HTTP/1.1" 200 12 request_time=0.320 upstream_response_time=0.090',
            '10.0.0.4 - - [x] "GET /db HTTP/1.1" 200 13 request_time=0.280 upstream_response_time=0.200',
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
            '10.0.0.1 - - [x] "GET /health HTTP/1.1" 200 10 request_time=0.005 upstream_response_time=0.001',
            '10.0.0.2 - - [x] "POST /api/report HTTP/1.1" 500 12 request_time=0.600 upstream_response_time=0.500',
            '10.0.0.3 - - [x] "POST /api/report HTTP/1.1" 502 13 request_time=0.700 upstream_response_time=0.650',
            '10.0.0.4 - - [x] "GET /api/report HTTP/1.1" 500 14 request_time=0.450 upstream_response_time=0.300',
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
                    '10.0.0.1 - - [x] "POST /api/report HTTP/1.1" 500 12 request_time=0.600 upstream_response_time=0.500',
                ],
                top_n=1,
                hotspot_statuses=['500'],
                hotspot_methods=['POST'],
            )
        )
        self.assertIn('Per-path latency hotspots (ms): (filters: status=500; method=POST)', report)
        self.assertIn('Per-path upstream latency hotspots (ms): (filters: status=500; method=POST)', report)

    def test_cli_json_output_includes_named_timing_summaries(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'access.log'
            log_path.write_text(
                textwrap.dedent(
                    '''\
                    10.0.0.1 - - [x] "GET / HTTP/1.1" 200 10 "https://example.com/start" "Mozilla/5.0" request_time=0.125 upstream_response_time=0.080
                    10.0.0.2 - - [x] "POST /login HTTP/1.1" 401 5 "-" "curl/8.0" request_time=0.250 upstream_response_time=0.120
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

    def test_cli_json_output_supports_hotspot_filters(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'access.log'
            log_path.write_text(
                textwrap.dedent(
                    '''\
                    10.0.0.1 - - [x] "GET /health HTTP/1.1" 200 10 request_time=0.005 upstream_response_time=0.001
                    10.0.0.2 - - [x] "POST /api/report HTTP/1.1" 500 12 request_time=0.600 upstream_response_time=0.500
                    10.0.0.3 - - [x] "POST /api/report HTTP/1.1" 502 13 request_time=0.700 upstream_response_time=0.650
                    10.0.0.4 - - [x] "GET /api/report HTTP/1.1" 500 14 request_time=0.450 upstream_response_time=0.300
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

    def test_cli_csv_exports_include_upstream_latency_summary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'access.log'
            summary_csv = Path(tmpdir) / 'exports' / 'summary.csv'
            breakdown_csv = Path(tmpdir) / 'exports' / 'path-latency.csv'
            upstream_breakdown_csv = Path(tmpdir) / 'exports' / 'upstream-path-latency.csv'
            log_path.write_text(
                textwrap.dedent(
                    '''\
                    10.0.0.1 - - [x] "GET /fast HTTP/1.1" 200 10 "-" "Mozilla/5.0" request_time=0.010 upstream_response_time=0.005
                    10.0.0.2 - - [x] "GET /slow HTTP/1.1" 200 15 "https://example.com" "curl/8.0" request_time=0.450 upstream_response_time=0.300, 0.050
                    10.0.0.3 - - [x] "GET /slow HTTP/1.1" 200 18 "https://example.com" "curl/8.0" request_time=0.500 upstream_response_time=0.320
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
                    10.0.0.1 - - [x] "POST /api/report HTTP/1.1" 500 15 request_time=0.450 upstream_response_time=0.300
                    10.0.0.2 - - [x] "POST /api/report HTTP/1.1" 502 18 request_time=0.500 upstream_response_time=0.320
                    10.0.0.3 - - [x] "GET /health HTTP/1.1" 200 10 request_time=0.010 upstream_response_time=0.005
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

    def test_cli_text_output_mentions_upstream_latency_summary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'access.log'
            log_path.write_text(
                '10.0.0.1 - - [x] "GET /slow HTTP/1.1" 200 10 "https://example.com" "Mozilla/5.0" request_time=0.010 upstream_response_time=0.007\n',
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

    def test_cli_rejects_invalid_hotspot_status(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'access.log'
            log_path.write_text(
                '10.0.0.1 - - [x] "GET /slow HTTP/1.1" 200 10 request_time=0.010\n',
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


if __name__ == '__main__':
    unittest.main()
