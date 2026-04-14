import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.task_tracker.cli import build_parser, render_table, run_cli
from src.task_tracker.store import Task, TaskService, TaskStorage


@pytest.fixture()
def data_file(tmp_path: Path) -> Path:
    return tmp_path / "tasks.json"


def run_args(data_file: Path, *argv: str) -> int:
    return run_cli(["--data-file", str(data_file), *argv])


def test_cli_add_list_summary_and_json(data_file: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert run_args(data_file, "add", "Write docs", "--priority", "high", "--due", "2026-04-20", "--tag", "docs") == 0
    assert run_args(data_file, "add", "Ship CLI", "--tag", "portfolio,demo") == 0

    assert run_args(data_file, "list", "--sort-by", "priority") == 0
    listing = capsys.readouterr().out
    assert "Write docs" in listing
    assert "priority" in listing

    assert run_args(data_file, "list", "--json", "--tag", "demo") == 0
    payload = json.loads(capsys.readouterr().out)
    assert [task["description"] for task in payload] == ["Ship CLI"]

    assert run_args(data_file, "summary") == 0
    summary = capsys.readouterr().out
    assert "todo: 2" in summary
    assert "unique_tags: 3" in summary


def test_cli_update_clear_due_and_export(data_file: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert run_args(data_file, "add", "Prepare demo", "--due", "2026-04-18", "--tag", "demo") == 0
    capsys.readouterr()

    assert run_args(data_file, "update", "1", "--priority", "low", "--clear-due", "--tag", "talk") == 0
    updated = capsys.readouterr().out
    assert "priority=low" in updated
    assert "due=-" in updated
    assert "tags=talk" in updated

    export_path = tmp_path / "tasks.md"
    assert run_args(data_file, "export", "--format", "markdown", "--output", str(export_path)) == 0
    capsys.readouterr()
    assert export_path.exists()
    assert "# Task Export" in export_path.read_text(encoding="utf-8")


def test_cli_rejects_conflicting_update_flags(data_file: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert run_args(data_file, "add", "Prepare lab") == 0
    capsys.readouterr()

    assert run_args(data_file, "update", "1", "--due", "2026-04-20", "--clear-due") == 1
    assert "Use either --due or --clear-due, not both." in capsys.readouterr().err


def test_render_table_empty() -> None:
    assert render_table([]) == "No tasks found."


def test_build_parser_supports_clear_due() -> None:
    args = build_parser().parse_args(["update", "1", "--clear-due"])
    assert args.clear_due is True


def test_packaged_entry_point_smoke(data_file: Path) -> None:
    project_dir = Path(__file__).resolve().parents[1]
    command = [sys.executable, "-m", "task_tracker", "--data-file", str(data_file), "add", "Prepare demo"]
    result = subprocess.run(command, cwd=project_dir, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Added:" in result.stdout


def test_compatibility_namespace_for_legacy_entry_point(data_file: Path) -> None:
    service = TaskService(TaskStorage(data_file))
    task = service.add_task("Legacy import path check")
    legacy_task = __import__("task_tracker_cli.store", fromlist=["Task"]).Task
    assert isinstance(task, Task)
    assert legacy_task is Task
