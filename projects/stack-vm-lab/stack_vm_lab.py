import argparse
import json
import shlex
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Instruction:
    opcode: str
    args: list[str] = field(default_factory=list)
    line: int = 0


@dataclass
class Frame:
    name: str
    return_ip: int | None
    locals: dict[str, Any] = field(default_factory=dict)


class VMError(RuntimeError):
    pass


class StackVM:
    def __init__(self, program: dict[str, list[Instruction]], entry: str = "main") -> None:
        if entry not in program:
            raise VMError(f"missing entry function: {entry}")
        self.program = program
        self.stack: list[Any] = []
        self.output: list[Any] = []
        self.trace: list[dict[str, Any]] = []
        self.frames: list[Frame] = [Frame(entry, None, {})]
        self.current_function = entry
        self.ip = 0
        self.halted = False

    @property
    def frame(self) -> Frame:
        return self.frames[-1]

    def pop(self) -> Any:
        if not self.stack:
            raise VMError("stack underflow")
        return self.stack.pop()

    def resolve_value(self, token: str) -> Any:
        if token.lower() == "true":
            return True
        if token.lower() == "false":
            return False
        if token.startswith('"') and token.endswith('"'):
            return token[1:-1]
        try:
            return int(token)
        except ValueError:
            return token

    def step(self) -> None:
        instructions = self.program[self.current_function]
        if self.ip < 0 or self.ip >= len(instructions):
            raise VMError(f"instruction pointer out of range in {self.current_function}: {self.ip}")
        instruction = instructions[self.ip]
        before_stack = list(self.stack)
        next_ip = self.ip + 1
        op = instruction.opcode
        args = instruction.args

        if op == "PUSH":
            self.stack.append(self.resolve_value(args[0]))
        elif op == "POP":
            self.pop()
        elif op == "DUP":
            value = self.pop()
            self.stack.extend([value, value])
        elif op == "SWAP":
            right = self.pop()
            left = self.pop()
            self.stack.extend([right, left])
        elif op == "LOAD":
            name = args[0]
            if name not in self.frame.locals:
                raise VMError(f"unknown local: {name}")
            self.stack.append(self.frame.locals[name])
        elif op == "STORE":
            self.frame.locals[args[0]] = self.pop()
        elif op in {"ADD", "SUB", "MUL", "DIV", "MOD", "EQ", "LT", "GT"}:
            right = self.pop()
            left = self.pop()
            if op == "ADD":
                self.stack.append(left + right)
            elif op == "SUB":
                self.stack.append(left - right)
            elif op == "MUL":
                self.stack.append(left * right)
            elif op == "DIV":
                self.stack.append(left // right)
            elif op == "MOD":
                self.stack.append(left % right)
            elif op == "EQ":
                self.stack.append(left == right)
            elif op == "LT":
                self.stack.append(left < right)
            elif op == "GT":
                self.stack.append(left > right)
        elif op == "JMP":
            next_ip = int(args[0])
        elif op == "JIF":
            condition = self.pop()
            if not condition:
                next_ip = int(args[0])
        elif op == "CALL":
            function_name = args[0]
            arg_count = int(args[1]) if len(args) > 1 else 0
            if function_name not in self.program:
                raise VMError(f"unknown function: {function_name}")
            values = [self.pop() for _ in range(arg_count)][::-1]
            self.frames.append(
                Frame(
                    function_name,
                    return_ip=self.ip + 1,
                    locals={f"arg{index}": value for index, value in enumerate(values)},
                )
            )
            self.current_function = function_name
            next_ip = 0
        elif op == "RET":
            return_value = self.pop() if self.stack else None
            finished = self.frames.pop()
            if not self.frames:
                if return_value is not None:
                    self.stack.append(return_value)
                self.halted = True
                self.trace.append(
                    {
                        "function": finished.name,
                        "ip": self.ip,
                        "instruction": render_instruction(instruction),
                        "stack_before": before_stack,
                        "stack_after": list(self.stack),
                    }
                )
                return
            caller = self.frames[-1]
            self.current_function = caller.name
            next_ip = finished.return_ip if finished.return_ip is not None else 0
            if return_value is not None:
                self.stack.append(return_value)
        elif op == "PRINT":
            value = self.pop()
            self.output.append(value)
        elif op == "HALT":
            self.halted = True
        else:
            raise VMError(f"unsupported opcode: {op}")

        self.trace.append(
            {
                "function": self.current_function,
                "ip": self.ip,
                "instruction": render_instruction(instruction),
                "stack_before": before_stack,
                "stack_after": list(self.stack),
                "locals": dict(self.frame.locals),
            }
        )
        self.ip = next_ip

    def run(self, max_steps: int = 10_000) -> dict[str, Any]:
        steps = 0
        while not self.halted:
            self.step()
            steps += 1
            if steps > max_steps:
                raise VMError("program exceeded step limit")
        return {
            "entry": self.frames[0].name if self.frames else self.current_function,
            "stack": list(self.stack),
            "output": list(self.output),
            "steps": steps,
            "trace": self.trace,
        }


def render_instruction(instruction: Instruction) -> str:
    if instruction.args:
        return f"{instruction.opcode} {' '.join(instruction.args)}"
    return instruction.opcode


def parse_program(text: str) -> dict[str, list[Instruction]]:
    program: dict[str, list[Instruction]] = {}
    current: list[Instruction] | None = None
    current_name: str | None = None
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith("func "):
            current_name = line.split()[1].rstrip(":")
            if current_name in program:
                raise VMError(f"duplicate function: {current_name}")
            current = []
            program[current_name] = current
            continue
        if current is None or current_name is None:
            raise VMError(f"instruction outside of function on line {line_number}")
        parts = shlex.split(line)
        current.append(Instruction(parts[0].upper(), parts[1:], line_number))
    if not program:
        raise VMError("program is empty")
    return program


def load_program(path: Path) -> dict[str, list[Instruction]]:
    return parse_program(path.read_text())


SAMPLES = {
    "factorial": """
func main:
  PUSH 5
  STORE n
  PUSH 1
  STORE acc
  LOAD n
  PUSH 1
  GT
  JIF 17
  LOAD acc
  LOAD n
  MUL
  STORE acc
  LOAD n
  PUSH 1
  SUB
  STORE n
  JMP 4
  LOAD acc
  PRINT
  HALT
""".strip(),
    "max2": """
func main:
  PUSH 9
  PUSH 14
  CALL max 2
  PRINT
  HALT

func max:
  LOAD arg0
  LOAD arg1
  GT
  JIF 6
  LOAD arg0
  RET
  LOAD arg1
  RET
""".strip(),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a tiny stack-based VM lab")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="run a program file")
    run_parser.add_argument("path")
    run_parser.add_argument("--entry", default="main")
    run_parser.add_argument("--trace-limit", type=int, default=20)

    sample_parser = subparsers.add_parser("sample", help="run a bundled sample")
    sample_parser.add_argument("name", choices=sorted(SAMPLES))
    sample_parser.add_argument("--trace-limit", type=int, default=20)

    dis_parser = subparsers.add_parser("disassemble", help="print parsed instructions")
    dis_parser.add_argument("path")
    return parser


def summarize(program: dict[str, list[Instruction]]) -> dict[str, list[str]]:
    return {name: [render_instruction(instruction) for instruction in instructions] for name, instructions in program.items()}


def command_run(program: dict[str, list[Instruction]], entry: str, trace_limit: int) -> dict[str, Any]:
    vm = StackVM(program, entry=entry)
    result = vm.run()
    result["trace"] = result["trace"][:trace_limit]
    result["functions"] = summarize(program)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        program = load_program(Path(args.path))
        result = command_run(program, entry=args.entry, trace_limit=args.trace_limit)
    elif args.command == "sample":
        program = parse_program(SAMPLES[args.name])
        result = command_run(program, entry="main", trace_limit=args.trace_limit)
        result["sample"] = args.name
    else:
        program = load_program(Path(args.path))
        result = {"functions": summarize(program)}

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
