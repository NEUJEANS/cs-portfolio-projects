import os
import tempfile
import unittest

from mini_shell import get_repl_history_limit, get_repl_history_path, load_history, run_command

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

    def test_history_builtin_lists_numbered_commands(self):
        history = []
        cwd, _ = run_command("pwd", "/tmp", history)
        self.assertEqual(cwd, "/tmp")
        cwd, _ = run_command("echo hello", cwd, history)
        cwd, out = run_command("history", cwd, history)
        self.assertEqual(cwd, "/tmp")
        self.assertEqual(
            out.splitlines(),
            [
                "   1  pwd",
                "   2  echo hello",
                "   3  history",
            ],
        )

    def test_double_bang_replays_last_command(self):
        history = []
        cwd, first = run_command("echo alpha", "/tmp", history)
        self.assertEqual(first, "alpha")
        cwd, second = run_command("!!", cwd, history)
        self.assertEqual(cwd, "/tmp")
        self.assertEqual(second, "alpha")
        self.assertEqual(history, ["echo alpha", "echo alpha"])

    def test_numbered_history_replays_specific_command(self):
        history = []
        cwd, _ = run_command("echo alpha", "/tmp", history)
        cwd, _ = run_command("echo beta", cwd, history)
        cwd, out = run_command("!1", cwd, history)
        self.assertEqual(cwd, "/tmp")
        self.assertEqual(out, "alpha")
        self.assertEqual(history[-1], "echo alpha")

    def test_history_reference_requires_existing_entry(self):
        with self.assertRaises(ValueError) as ctx:
            run_command("!!", "/tmp", [])
        self.assertIn("history is empty", str(ctx.exception))

    def test_numbered_history_reference_must_be_in_range(self):
        history = []
        run_command("echo alpha", "/tmp", history)
        with self.assertRaises(ValueError) as ctx:
            run_command("!3", "/tmp", history)
        self.assertIn("history entry not found: 3", str(ctx.exception))

    def test_history_builtin_can_be_redirected(self):
        history = []
        with tempfile.TemporaryDirectory() as tmp:
            output_path = os.path.join(tmp, "history.txt")
            run_command("echo alpha", tmp, history)
            cwd, out = run_command(f"history > {output_path}", tmp, history)
            self.assertEqual(cwd, tmp)
            self.assertEqual(out, "")
            with open(output_path, encoding="utf-8") as handle:
                self.assertEqual(
                    handle.read().splitlines(),
                    [
                        "   1  echo alpha",
                        f"   2  history > {output_path}",
                    ],
                )

    def test_load_history_returns_empty_for_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            history_path = os.path.join(tmp, "missing-history.txt")
            self.assertEqual(load_history(history_path), [])

    def test_repl_history_path_can_be_disabled_with_empty_env(self):
        original_value = os.environ.get("MINI_SHELL_HISTORY_FILE")
        os.environ["MINI_SHELL_HISTORY_FILE"] = ""
        try:
            self.assertIsNone(get_repl_history_path())
        finally:
            if original_value is None:
                os.environ.pop("MINI_SHELL_HISTORY_FILE", None)
            else:
                os.environ["MINI_SHELL_HISTORY_FILE"] = original_value

    def test_repl_history_limit_uses_env_override(self):
        original_value = os.environ.get("MINI_SHELL_HISTORY_LIMIT")
        os.environ["MINI_SHELL_HISTORY_LIMIT"] = "3"
        try:
            self.assertEqual(get_repl_history_limit(), 3)
        finally:
            if original_value is None:
                os.environ.pop("MINI_SHELL_HISTORY_LIMIT", None)
            else:
                os.environ["MINI_SHELL_HISTORY_LIMIT"] = original_value

    def test_repl_history_limit_rejects_negative_env_value(self):
        original_value = os.environ.get("MINI_SHELL_HISTORY_LIMIT")
        os.environ["MINI_SHELL_HISTORY_LIMIT"] = "-1"
        try:
            with self.assertRaises(ValueError) as ctx:
                get_repl_history_limit()
            self.assertIn("non-negative integer", str(ctx.exception))
        finally:
            if original_value is None:
                os.environ.pop("MINI_SHELL_HISTORY_LIMIT", None)
            else:
                os.environ["MINI_SHELL_HISTORY_LIMIT"] = original_value

    def test_repl_history_limit_rejects_non_numeric_env_value(self):
        original_value = os.environ.get("MINI_SHELL_HISTORY_LIMIT")
        os.environ["MINI_SHELL_HISTORY_LIMIT"] = "many"
        try:
            with self.assertRaises(ValueError) as ctx:
                get_repl_history_limit()
            self.assertIn("non-negative integer", str(ctx.exception))
        finally:
            if original_value is None:
                os.environ.pop("MINI_SHELL_HISTORY_LIMIT", None)
            else:
                os.environ["MINI_SHELL_HISTORY_LIMIT"] = original_value

    def test_load_history_ignores_blank_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            history_path = os.path.join(tmp, "mini-shell-history.txt")
            with open(history_path, "w", encoding="utf-8") as handle:
                handle.write("echo alpha\n\n history-like-gap\n")
            self.assertEqual(load_history(history_path), ["echo alpha", " history-like-gap"])

    def test_history_persists_across_sessions(self):
        with tempfile.TemporaryDirectory() as tmp:
            history_path = os.path.join(tmp, "mini-shell-history.txt")
            first_session_history = []

            cwd, out = run_command(
                "echo alpha",
                tmp,
                first_session_history,
                history_path=history_path,
            )
            self.assertEqual(cwd, tmp)
            self.assertEqual(out, "alpha")
            self.assertEqual(load_history(history_path), ["echo alpha"])

            second_session_history = load_history(history_path)
            cwd, out = run_command(
                "history",
                tmp,
                second_session_history,
                history_path=history_path,
            )
            self.assertEqual(cwd, tmp)
            self.assertEqual(
                out.splitlines(),
                [
                    "   1  echo alpha",
                    "   2  history",
                ],
            )
            self.assertEqual(load_history(history_path), ["echo alpha", "history"])

    def test_history_limit_trims_memory_and_history_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            history_path = os.path.join(tmp, "mini-shell-history.txt")
            history = []
            run_command("echo alpha", tmp, history, history_path=history_path, history_limit=2)
            run_command("echo beta", tmp, history, history_path=history_path, history_limit=2)
            run_command("echo gamma", tmp, history, history_path=history_path, history_limit=2)
            self.assertEqual(history, ["echo beta", "echo gamma"])
            self.assertEqual(load_history(history_path), ["echo beta", "echo gamma"])

    def test_load_history_can_trim_existing_file_to_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            history_path = os.path.join(tmp, "mini-shell-history.txt")
            with open(history_path, "w", encoding="utf-8") as handle:
                handle.write("echo alpha\necho beta\necho gamma\n")

            loaded_history = load_history(history_path, history_limit=2, trim_file=True)
            self.assertEqual(loaded_history, ["echo beta", "echo gamma"])
            self.assertEqual(load_history(history_path), ["echo beta", "echo gamma"])

    def test_zero_history_limit_disables_retention(self):
        with tempfile.TemporaryDirectory() as tmp:
            history_path = os.path.join(tmp, "mini-shell-history.txt")
            history = []

            cwd, out = run_command(
                "echo alpha",
                tmp,
                history,
                history_path=history_path,
                history_limit=0,
            )
            self.assertEqual(cwd, tmp)
            self.assertEqual(out, "alpha")
            self.assertEqual(history, [])
            self.assertEqual(load_history(history_path), [])

    def test_negative_history_limit_is_rejected_for_direct_calls(self):
        with self.assertRaises(ValueError) as ctx:
            run_command("echo alpha", "/tmp", [], history_limit=-1)
        self.assertIn("history limit must be a non-negative integer", str(ctx.exception))

    def test_history_clear_empties_memory_and_history_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            history_path = os.path.join(tmp, "mini-shell-history.txt")
            history = []
            run_command("echo alpha", tmp, history, history_path=history_path)
            run_command("echo beta", tmp, history, history_path=history_path)

            cwd, out = run_command("history -c", tmp, history, history_path=history_path)
            self.assertEqual(cwd, tmp)
            self.assertEqual(out, "")
            self.assertEqual(history, [])
            self.assertEqual(load_history(history_path), [])

    def test_history_rejects_unsupported_arguments(self):
        with tempfile.TemporaryDirectory() as tmp:
            history_path = os.path.join(tmp, "mini-shell-history.txt")
            with self.assertRaises(ValueError) as ctx:
                run_command("history -z", tmp, [], history_path=history_path)
            self.assertIn("history: unsupported arguments", str(ctx.exception))

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
