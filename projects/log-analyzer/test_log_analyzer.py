import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from log_analyzer import analyze_lines, format_text_report, parse_line


class LogAnalyzerTests(unittest.TestCase):
    def test_parse_line_supports_dash_bytes(self):
        parsed = parse_line('10.0.0.1 - - [x] "GET / HTTP/1.1" 304 -')
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.bytes_sent, 0)
        self.assertEqual(parsed.method, 'GET')

    def test_analyze_lines_counts_methods_paths_and_invalid_lines(self):
        lines = [
            '10.0.0.1 - - [x] "GET / HTTP/1.1" 200 10',
            '10.0.0.2 - - [x] "POST /login HTTP/1.1" 401 5',
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

    def test_format_text_report_handles_empty_results(self):
        report = format_text_report(analyze_lines([], top_n=3))
        self.assertIn('Total requests: 0', report)
        self.assertIn('Status counts:', report)
        self.assertIn('  (none)', report)

    def test_cli_json_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'access.log'
            log_path.write_text(
                textwrap.dedent(
                    '''\
                    10.0.0.1 - - [x] "GET / HTTP/1.1" 200 10
                    10.0.0.2 - - [x] "POST /login HTTP/1.1" 401 5
                    '''
                ),
                encoding='utf-8',
            )
            completed = subprocess.run(
                [sys.executable, 'log_analyzer.py', str(log_path), '--format', 'json', '--top', '1'],
                cwd=Path(__file__).parent,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload['total_requests'], 2)
            self.assertEqual(payload['top_paths'][0], ['/', 1])

    def test_cli_text_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'access.log'
            log_path.write_text('10.0.0.1 - - [x] "GET / HTTP/1.1" 200 10\n', encoding='utf-8')
            completed = subprocess.run(
                [sys.executable, 'log_analyzer.py', str(log_path), '--format', 'text'],
                cwd=Path(__file__).parent,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn('Log Analysis Summary', completed.stdout)
            self.assertIn('Top paths:', completed.stdout)


if __name__ == '__main__':
    unittest.main()
