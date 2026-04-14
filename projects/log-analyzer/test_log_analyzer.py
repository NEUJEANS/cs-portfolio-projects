import unittest
from log_analyzer import analyze_lines

class LogAnalyzerTests(unittest.TestCase):
    def test_counts(self):
        lines = [
            '10.0.0.1 - - [x] "GET / HTTP/1.1" 200 1',
            '10.0.0.2 - - [x] "GET /404 HTTP/1.1" 404 1',
            '10.0.0.1 - - [x] "GET / HTTP/1.1" 200 1',
        ]
        result = analyze_lines(lines)
        self.assertEqual(result['status_counts']['200'], 2)
        self.assertEqual(result['top_ips'][0], ('10.0.0.1', 2))

if __name__ == '__main__':
    unittest.main()
