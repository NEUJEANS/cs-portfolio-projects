import tempfile, unittest
from pathlib import Path
from integrity_monitor import snapshot_dir, diff_snapshots

class IntegrityMonitorTests(unittest.TestCase):
    def test_detect_changed_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / 'a.txt').write_text('hello')
            old = snapshot_dir(p)
            (p / 'a.txt').write_text('bye')
            new = snapshot_dir(p)
            diff = diff_snapshots(old, new)
            self.assertEqual(diff['changed'], ['a.txt'])

if __name__ == '__main__':
    unittest.main()
