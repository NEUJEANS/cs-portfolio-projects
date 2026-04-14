import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from stack_vm_lab import SAMPLES, StackVM, VMError, parse_program

PROJECT_DIR = Path(__file__).resolve().parent
SCRIPT = PROJECT_DIR / "stack_vm_lab.py"


def run_cli(*args: str) -> dict:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(completed.stdout)


class StackVMLabTests(unittest.TestCase):
    def test_factorial_sample_outputs_120(self) -> None:
        result = StackVM(parse_program(SAMPLES["factorial"])).run()
        self.assertEqual(result["output"], [120])
        self.assertEqual(result["stack"], [])

    def test_call_and_return_flow(self) -> None:
        result = StackVM(parse_program(SAMPLES["max2"])).run()
        self.assertEqual(result["output"], [14])

    def test_custom_program_with_locals_and_branch(self) -> None:
        program = parse_program(
            """
func main:
  PUSH 10
  PUSH 3
  MOD
  PUSH 1
  EQ
  JIF 8
  PUSH 99
  PRINT
  HALT
  PUSH 0
  PRINT
  HALT
""".strip()
        )
        result = StackVM(program).run()
        self.assertEqual(result["output"], [99])

    def test_disassemble_cli_lists_functions(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".svm", delete=False) as handle:
            handle.write(SAMPLES["max2"])
            path = handle.name
        output = run_cli("disassemble", path)
        self.assertIn("main", output["functions"])
        self.assertIn("CALL max 2", output["functions"]["main"])

    def test_sample_cli_limits_trace(self) -> None:
        output = run_cli("sample", "factorial", "--trace-limit", "3")
        self.assertEqual(output["output"], [120])
        self.assertEqual(len(output["trace"]), 3)

    def test_quoted_string_with_spaces_round_trips(self) -> None:
        program = parse_program(
            """
func main:
  PUSH "hello vm"
  PRINT
  HALT
""".strip()
        )
        result = StackVM(program).run()
        self.assertEqual(result["output"], ["hello vm"])

    def test_unknown_local_raises_error(self) -> None:
        program = parse_program(
            """
func main:
  LOAD missing
  HALT
""".strip()
        )
        with self.assertRaisesRegex(VMError, "unknown local"):
            StackVM(program).run()

    def test_duplicate_function_rejected(self) -> None:
        with self.assertRaisesRegex(VMError, "duplicate function"):
            parse_program(
                """
func main:
  HALT
func main:
  HALT
""".strip()
            )


if __name__ == "__main__":
    unittest.main()
