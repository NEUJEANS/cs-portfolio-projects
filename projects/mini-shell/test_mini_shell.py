import os, tempfile, unittest
from mini_shell import run_command

class MiniShellTests(unittest.TestCase):
    def test_pwd_and_cd(self):
        cwd, out = run_command('pwd', '/tmp')
        self.assertEqual(out, '/tmp')
        with tempfile.TemporaryDirectory() as tmp:
            new_cwd, _ = run_command('cd .', tmp)
            self.assertEqual(os.path.abspath(tmp), new_cwd)

if __name__ == '__main__':
    unittest.main()
