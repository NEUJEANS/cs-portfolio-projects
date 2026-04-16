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

    def test_cd_expands_tilde(self):
        home = os.path.expanduser("~")
        cwd, out = run_command("cd ~", "/tmp")
        self.assertEqual(cwd, home)
        self.assertEqual(out, "")

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

    def test_builtin_output_redirection_writes_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_path = os.path.join(tmp, "cwd.txt")
            cwd, out = run_command(f"pwd > {output_path}", tmp)
            self.assertEqual(cwd, tmp)
            self.assertEqual(out, "")
            with open(output_path, encoding="utf-8") as handle:
                self.assertEqual(handle.read(), f"{tmp}\n")

    def test_append_redirection_supports_compact_operator(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_path = os.path.join(tmp, "echo.txt")
            run_command(f"echo alpha > {output_path}", tmp)
            run_command(f"echo beta>>{output_path}", tmp)
            with open(output_path, encoding="utf-8") as handle:
                self.assertEqual(handle.read().splitlines(), ["alpha", "beta"])

    def test_external_input_redirection_feeds_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_path = os.path.join(tmp, "input.txt")
            with open(input_path, "w", encoding="utf-8") as handle:
                handle.write("alpha beta")

            cwd, out = run_command(
                f"python3 -c 'import sys; print(sys.stdin.read().upper())' < {input_path}",
                tmp,
            )
            self.assertEqual(cwd, tmp)
            self.assertEqual(out, "ALPHA BETA")

    def test_pipeline_allows_edge_redirection(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_path = os.path.join(tmp, "input.txt")
            output_path = os.path.join(tmp, "output.txt")
            with open(input_path, "w", encoding="utf-8") as handle:
                handle.write("alpha beta")

            cwd, out = run_command(
                "python3 -c 'import sys; print(sys.stdin.read().upper())' "
                f"< {input_path} | "
                "python3 -c 'import sys; print(sys.stdin.read().strip().replace(\" \", \"-\"))' "
                f"> {output_path}",
                tmp,
            )
            self.assertEqual(cwd, tmp)
            self.assertEqual(out, "")
            with open(output_path, encoding="utf-8") as handle:
                self.assertEqual(handle.read(), "ALPHA-BETA\n")

    def test_pipeline_preserves_earlier_stage_stderr(self):
        with self.assertRaises(RuntimeError) as ctx:
            run_command(
                "python3 -c 'import sys; sys.stderr.write(\"boom\\n\"); sys.exit(2)' "
                "| python3 -c 'import sys; sys.stdout.write(sys.stdin.read())'",
                "/tmp",
            )
        self.assertIn("boom", str(ctx.exception))

    def test_rejects_builtin_inside_pipeline(self):
        with self.assertRaises(ValueError):
            run_command('echo hello | python3 -c "print(1)"', "/tmp")

    def test_rejects_mid_pipeline_output_redirection(self):
        with self.assertRaises(ValueError):
            run_command(
                "python3 -c 'print(1)' > out.txt | python3 -c 'print(2)'",
                "/tmp",
            )

    def test_rejects_dangling_redirection_operator(self):
        with self.assertRaises(ValueError) as ctx:
            run_command("echo hello >", "/tmp")
        self.assertIn("requires a path", str(ctx.exception))

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
