import contextlib
import os
import shlex
import subprocess
from dataclasses import dataclass
from typing import List, Optional, Tuple

BUILTINS = {"cd", "pwd", "exit", "echo"}
OPERATORS = {"|", "<", ">", ">>"}


@dataclass
class CommandSpec:
    parts: List[str]
    stdin_path: Optional[str] = None
    stdout_path: Optional[str] = None
    append_stdout: bool = False


def tokenize(command: str) -> List[str]:
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars="|<>")
        lexer.whitespace_split = True
        raw_tokens = list(lexer)
    except ValueError as exc:
        if "No closing quotation" in str(exc):
            raise ValueError("unterminated quote") from exc
        raise

    return [os.path.expandvars(token) if token not in OPERATORS else token for token in raw_tokens]


def parse_command(command: str) -> List[CommandSpec]:
    tokens = tokenize(command)
    specs: List[CommandSpec] = []
    current = CommandSpec(parts=[])
    pending_redirection: Optional[str] = None

    for token in tokens:
        if pending_redirection is not None:
            if token in OPERATORS:
                raise ValueError("redirection operator requires a path")
            if pending_redirection == "<":
                if current.stdin_path is not None:
                    raise ValueError("multiple input redirections are not supported")
                current.stdin_path = token
            else:
                if current.stdout_path is not None:
                    raise ValueError("multiple output redirections are not supported")
                current.stdout_path = token
                current.append_stdout = pending_redirection == ">>"
            pending_redirection = None
            continue

        if token == "|":
            if not current.parts:
                raise ValueError("invalid null command")
            specs.append(current)
            current = CommandSpec(parts=[])
            continue

        if token in {"<", ">", ">>"}:
            pending_redirection = token
            continue

        current.parts.append(token)

    if pending_redirection is not None:
        raise ValueError("redirection operator requires a path")
    if not current.parts:
        raise ValueError("invalid null command")

    specs.append(current)

    if len(specs) > 1:
        for index, spec in enumerate(specs):
            if spec.parts[0] in BUILTINS:
                raise ValueError("builtins are only supported as standalone commands")
            if index > 0 and spec.stdin_path is not None:
                raise ValueError("input redirection is only supported on the first pipeline command")
            if index < len(specs) - 1 and spec.stdout_path is not None:
                raise ValueError("output redirection is only supported on the last pipeline command")

    return specs


def resolve_path(path: str, cwd: str) -> str:
    expanded = os.path.expanduser(path)
    if os.path.isabs(expanded):
        return expanded
    return os.path.abspath(os.path.join(cwd, expanded))


def write_redirected_output(path: str, append: bool, output: str, cwd: str) -> None:
    file_mode = "a" if append else "w"
    with open(resolve_path(path, cwd), file_mode, encoding="utf-8") as handle:
        if output:
            handle.write(output)
            if not output.endswith("\n"):
                handle.write("\n")


def run_builtin(parts: List[str], cwd: Optional[str]) -> Tuple[str, str]:
    current_cwd = cwd or os.getcwd()
    name = parts[0]

    if name == "cd":
        target = parts[1] if len(parts) > 1 else os.path.expanduser("~")
        expanded_target = os.path.expanduser(target)
        if os.path.isabs(expanded_target):
            new_cwd = os.path.abspath(expanded_target)
        else:
            new_cwd = os.path.abspath(os.path.join(current_cwd, expanded_target))
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


def run_pipeline(specs: List[CommandSpec], cwd: Optional[str]) -> str:
    current_cwd = cwd or os.getcwd()
    processes = []

    try:
        with contextlib.ExitStack() as stack:
            stdin_handle = None
            stdout_handle = None
            if specs[0].stdin_path is not None:
                stdin_handle = stack.enter_context(open(resolve_path(specs[0].stdin_path, current_cwd), encoding="utf-8"))
            if specs[-1].stdout_path is not None:
                stdout_handle = stack.enter_context(
                    open(
                        resolve_path(specs[-1].stdout_path, current_cwd),
                        "a" if specs[-1].append_stdout else "w",
                        encoding="utf-8",
                    )
                )

            previous_stdout = None
            for index, spec in enumerate(specs):
                process_stdin = stdin_handle if index == 0 and stdin_handle is not None else previous_stdout
                process_stdout = stdout_handle if index == len(specs) - 1 and stdout_handle is not None else subprocess.PIPE
                try:
                    process = subprocess.Popen(
                        spec.parts,
                        cwd=current_cwd,
                        stdin=process_stdin,
                        stdout=process_stdout,
                        stderr=subprocess.PIPE,
                        text=True,
                    )
                except FileNotFoundError as exc:
                    raise FileNotFoundError(f"command not found: {spec.parts[0]}") from exc

                if previous_stdout is not None:
                    previous_stdout.close()

                previous_stdout = process.stdout
                processes.append(process)

            stdout, stderr = processes[-1].communicate()

            stderr_texts = [stderr.strip()] if stderr.strip() else []
            for process in processes[:-1]:
                process.wait()
                if process.stderr is not None:
                    prior_stderr = process.stderr.read().strip()
                    if prior_stderr:
                        stderr_texts.append(prior_stderr)

            failing = [process.returncode for process in processes if process.returncode]
            if failing:
                error_text = "\n".join(stderr_texts) or f"pipeline failed with exit codes: {failing}"
                raise RuntimeError(error_text)

        if specs[-1].stdout_path is not None:
            return ""
        return (stdout or "").rstrip("\n")
    finally:
        for process in processes:
            if process.stdout is not None and not process.stdout.closed:
                process.stdout.close()
            if process.stderr is not None and not process.stderr.closed:
                process.stderr.close()


def run_external(spec: CommandSpec, cwd: Optional[str]) -> str:
    current_cwd = cwd or os.getcwd()

    try:
        with contextlib.ExitStack() as stack:
            stdin_handle = None
            stdout_handle = None
            if spec.stdin_path is not None:
                stdin_handle = stack.enter_context(open(resolve_path(spec.stdin_path, current_cwd), encoding="utf-8"))
            if spec.stdout_path is not None:
                stdout_handle = stack.enter_context(
                    open(
                        resolve_path(spec.stdout_path, current_cwd),
                        "a" if spec.append_stdout else "w",
                        encoding="utf-8",
                    )
                )

            result = subprocess.run(
                spec.parts,
                capture_output=stdout_handle is None,
                text=True,
                cwd=current_cwd,
                check=False,
                stdin=stdin_handle,
                stdout=stdout_handle,
            )
    except FileNotFoundError as exc:
        if exc.filename == spec.parts[0]:
            raise FileNotFoundError(f"command not found: {spec.parts[0]}") from exc
        raise

    if result.returncode != 0:
        error_text = result.stderr.strip() or f"command failed with exit code {result.returncode}"
        raise RuntimeError(error_text)

    if spec.stdout_path is not None:
        return ""
    return result.stdout.rstrip("\n")


def run_command(command: str, cwd: Optional[str] = None) -> Tuple[str, str]:
    current_cwd = cwd or os.getcwd()
    stripped = command.strip()
    if not stripped:
        return current_cwd, ""

    specs = parse_command(stripped)

    if len(specs) > 1:
        return current_cwd, run_pipeline(specs, current_cwd)

    spec = specs[0]
    if spec.parts[0] in BUILTINS:
        if spec.stdin_path is not None:
            raise ValueError("input redirection is not supported for builtins")
        new_cwd, output = run_builtin(spec.parts, current_cwd)
        if spec.stdout_path is not None:
            write_redirected_output(spec.stdout_path, spec.append_stdout, output, current_cwd)
            return new_cwd, ""
        return new_cwd, output

    return current_cwd, run_external(spec, current_cwd)


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
