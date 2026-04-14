import os
import shlex
import subprocess
from typing import List, Optional, Tuple

BUILTINS = {"cd", "pwd", "exit", "echo"}


def split_pipeline(command: str) -> List[str]:
    segments = []
    current = []
    quote_char = None
    escaped = False

    for char in command:
        if escaped:
            current.append(char)
            escaped = False
            continue

        if char == "\\":
            current.append(char)
            escaped = True
            continue

        if char in {"'", '"'}:
            if quote_char == char:
                quote_char = None
            elif quote_char is None:
                quote_char = char
            current.append(char)
            continue

        if char == "|" and quote_char is None:
            segments.append("".join(current).strip())
            current = []
            continue

        current.append(char)

    if quote_char is not None:
        raise ValueError("unterminated quote")

    segments.append("".join(current).strip())
    return segments


def tokenize(command: str) -> List[str]:
    return [os.path.expandvars(part) for part in shlex.split(command)]


def run_builtin(parts: List[str], cwd: Optional[str]) -> Tuple[str, str]:
    current_cwd = cwd or os.getcwd()
    name = parts[0]

    if name == "cd":
        target = parts[1] if len(parts) > 1 else os.path.expanduser("~")
        new_cwd = os.path.abspath(os.path.join(current_cwd, target))
        if not os.path.isdir(new_cwd):
            raise NotADirectoryError(f"cd: no such directory: {target}")
        return new_cwd, ""

    if name == "pwd":
        return current_cwd, current_cwd

    if name == "echo":
        return current_cwd, " ".join(parts[1:])

    if name == "exit":
        raise SystemExit(0)

    raise ValueError(f"unsupported builtin: {name}")


def run_pipeline(segments: List[str], cwd: Optional[str]) -> str:
    processes = []
    previous_stdout = None

    try:
        for segment in segments:
            parts = tokenize(segment)
            if not parts:
                raise ValueError("invalid null command in pipeline")
            if parts[0] in BUILTINS:
                raise ValueError("builtins are only supported as standalone commands")

            process = subprocess.Popen(
                parts,
                cwd=cwd,
                stdin=previous_stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            if previous_stdout is not None:
                previous_stdout.close()

            previous_stdout = process.stdout
            processes.append(process)

        stdout, stderr = processes[-1].communicate()

        for process in processes[:-1]:
            process.wait()

        failing = [process.returncode for process in processes if process.returncode]
        if failing:
            error_text = stderr.strip() or f"pipeline failed with exit codes: {failing}"
            raise RuntimeError(error_text)

        return stdout.strip()
    finally:
        for process in processes:
            if process.stdout is not None and not process.stdout.closed:
                process.stdout.close()
            if process.stderr is not None and not process.stderr.closed:
                process.stderr.close()


def run_external(parts: List[str], cwd: Optional[str]) -> str:
    try:
        result = subprocess.run(parts, capture_output=True, text=True, cwd=cwd, check=False)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"command not found: {parts[0]}") from exc

    if result.returncode != 0:
        error_text = result.stderr.strip() or f"command failed with exit code {result.returncode}"
        raise RuntimeError(error_text)

    return result.stdout.strip()


def run_command(command: str, cwd: Optional[str] = None) -> Tuple[str, str]:
    current_cwd = cwd or os.getcwd()
    stripped = command.strip()
    if not stripped:
        return current_cwd, ""

    segments = split_pipeline(stripped)
    if any(not segment for segment in segments):
        raise ValueError("invalid null command")

    if len(segments) > 1:
        return current_cwd, run_pipeline(segments, current_cwd)

    parts = tokenize(stripped)
    if not parts:
        return current_cwd, ""

    if parts[0] in BUILTINS:
        return run_builtin(parts, current_cwd)

    return current_cwd, run_external(parts, current_cwd)


def repl():
    cwd = os.getcwd()
    while True:
        try:
            command = input(f"{cwd}$ ")
            cwd, output = run_command(command, cwd)
            if output:
                print(output)
        except (FileNotFoundError, NotADirectoryError, RuntimeError, ValueError) as exc:
            print(exc)
        except SystemExit:
            break


if __name__ == "__main__":
    repl()
