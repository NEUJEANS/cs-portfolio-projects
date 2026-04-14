import os
import tempfile
import unittest

from mini_shell import run_command

os.environ["MINI_SHELL_NAME"] = "portfolio-shell"


class MiniShellTests(unittest.TestCase):
    def test_pwd_and_cd(self):
        cwd, out = run_command("pwd", "/tmp")
        self.assertEqual(out, "/tmp")
        with tempfile.TemporaryDirectory() as tmp:
            new_cwd, _ = run_command("cd .", tmp)
            self.assertEqual(os.path.abspath(tmp), new_cwd)

    def test_cd_rejects_missing_directory(self):
        with self.assertRaises(NotADirectoryError):
            run_command("cd missing-dir", "/tmp")

    def test_echo_builtin_expands_environment_variables(self):
        cwd, out = run_command("echo hello $MINI_SHELL_NAME", "/tmp")
        self.assertEqual(cwd, "/tmp")
        self.assertEqual(out, "hello portfolio-shell")

    def test_external_command_expands_environment_variables(self):
        cwd, out = run_command(
            "python3 -c 'import sys; print(sys.argv[1])' $MINI_SHELL_NAME",
            "/tmp",
        )
        self.assertEqual(cwd, "/tmp")
        self.assertEqual(out, "portfolio-shell")

    def test_pipeline_composes_external_commands(self):
        cwd, out = run_command(
            "python3 -c 'print(\"alpha beta\")' | python3 -c 'import sys; print(sys.stdin.read().upper().strip())'",
            "/tmp",
        )
        self.assertEqual(cwd, "/tmp")
        self.assertEqual(out, "ALPHA BETA")

    def test_rejects_builtin_inside_pipeline(self):
        with self.assertRaises(ValueError):
            run_command('echo hello | python3 -c "print(1)"', "/tmp")

    def test_quoted_pipe_character_does_not_split_pipeline(self):
        cwd, out = run_command(
            "python3 -c 'print(\"left|right\")'",
            "/tmp",
        )
        self.assertEqual(cwd, "/tmp")
        self.assertEqual(out, "left|right")

    def test_missing_command_has_friendly_error(self):
        with self.assertRaises(FileNotFoundError) as ctx:
            run_command("definitely-not-a-real-command", "/tmp")
        self.assertIn("command not found", str(ctx.exception))


if __name__ == "__main__":
    os.environ["MINI_SHELL_NAME"] = "portfolio-shell"
    unittest.main()
