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

    def test_parse_line_supports_combined_logs_with_latency(self):
        parsed = parse_line(
            '10.0.0.1 - - [x] "GET /docs HTTP/1.1" 200 123 '
            '"https://example.com/start" "Mozilla/5.0" 0.245'
        )
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.referrer, 'https://example.com/start')
        self.assertEqual(parsed.user_agent, 'Mozilla/5.0')
        self.assertEqual(parsed.latency_ms, 245.0)

    def test_parse_line_supports_microsecond_latency(self):
        parsed = parse_line(
            '10.0.0.2 - - [x] "POST /ingest HTTP/1.1" 201 42 '
            '"-" "curl/8.0" 12345'
        )
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.latency_ms, 12.345)
        self.assertEqual(parsed.user_agent, 'curl/8.0')
        self.assertIsNone(parsed.referrer)

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
        self.assertEqual(result['path_latency_breakdown'][0]['path'], '/login')
        self.assertEqual(result['path_latency_breakdown'][0]['average_ms'], 350.0)

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

    def test_format_text_report_handles_empty_results(self):
        report = format_text_report(analyze_lines([], top_n=3))
        self.assertIn('Total requests: 0', report)
        self.assertIn('Status counts:', report)
        self.assertIn('Top referrers:', report)
        self.assertIn('Latency summary (ms):', report)
        self.assertIn('Per-path latency hotspots (ms):', report)
        self.assertIn('  (none)', report)

    def test_cli_json_output_includes_combined_and_latency_fields(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'access.log'
            log_path.write_text(
                textwrap.dedent(
                    '''\
                    10.0.0.1 - - [x] "GET / HTTP/1.1" 200 10 "https://example.com/start" "Mozilla/5.0" 0.125
                    10.0.0.2 - - [x] "POST /login HTTP/1.1" 401 5 "-" "curl/8.0" 2500
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
            self.assertEqual(payload['latency_summary']['max_ms'], 125.0)
            self.assertEqual(payload['path_latency_breakdown'][0]['path'], '/')

    def test_cli_csv_exports_write_summary_and_path_latency_breakdown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'access.log'
            summary_csv = Path(tmpdir) / 'exports' / 'summary.csv'
            breakdown_csv = Path(tmpdir) / 'exports' / 'path-latency.csv'
            log_path.write_text(
                textwrap.dedent(
                    '''\
                    10.0.0.1 - - [x] "GET /fast HTTP/1.1" 200 10 "-" "Mozilla/5.0" 0.010
                    10.0.0.2 - - [x] "GET /slow HTTP/1.1" 200 15 "https://example.com" "curl/8.0" 0.450
                    10.0.0.3 - - [x] "GET /slow HTTP/1.1" 200 18 "https://example.com" "curl/8.0" 0.500
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

            with breakdown_csv.open(encoding='utf-8', newline='') as handle:
                latency_rows = list(csv.DictReader(handle))
            self.assertEqual(len(latency_rows), 1)
            self.assertEqual(latency_rows[0]['path'], '/slow')
            self.assertEqual(latency_rows[0]['count'], '2')
            self.assertEqual(latency_rows[0]['average_ms'], '475.0')

    def test_cli_text_output_mentions_referrers_latency_and_hotspots(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'access.log'
            log_path.write_text(
                '10.0.0.1 - - [x] "GET /slow HTTP/1.1" 200 10 "https://example.com" "Mozilla/5.0" 0.010\n',
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
            self.assertIn('Per-path latency hotspots (ms):', completed.stdout)


if __name__ == '__main__':
    unittest.main()
