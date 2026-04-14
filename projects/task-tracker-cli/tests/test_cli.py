from pathlib import Path

import pytest

from task_tracker_cli.cli import run_command, build_parser


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "tasks.json"


def parse_args(db_path: Path, *argv: str):
    return build_parser().parse_args(["--db", str(db_path), *argv])


def test_add_list_and_summary(db_path: Path):
    assert run_command(parse_args(db_path, "add", "Write docs")) == "Added task 1: Write docs"
    assert run_command(parse_args(db_path, "add", "Ship CLI")) == "Added task 2: Ship CLI"

    listing = run_command(parse_args(db_path, "list"))
    assert "[1] Write docs (todo)" in listing
    assert "[2] Ship CLI (todo)" in listing
    assert run_command(parse_args(db_path, "summary")) == "todo: 2 | in-progress: 0 | done: 0"


def test_mark_update_delete_flow(db_path: Path):
    run_command(parse_args(db_path, "add", "Draft README"))
    assert run_command(parse_args(db_path, "mark", "1", "in-progress")) == "Task 1 marked as in-progress"
    assert run_command(parse_args(db_path, "update", "1", "Draft polished README")) == "Updated task 1: Draft polished README"
    assert "Draft polished README (in-progress)" in run_command(parse_args(db_path, "list", "--status", "in-progress"))
    assert run_command(parse_args(db_path, "mark", "1", "done")) == "Task 1 marked as done"
    done_listing = run_command(parse_args(db_path, "list", "--status", "done"))
    assert "completed" in done_listing
    assert run_command(parse_args(db_path, "delete", "1")) == "Deleted task 1"
    assert run_command(parse_args(db_path, "list")) == "No tasks found"


def test_missing_task_raises_value_error(db_path: Path):
    with pytest.raises(ValueError, match="Task 99 does not exist"):
        run_command(parse_args(db_path, "delete", "99"))


def test_blank_title_is_rejected(db_path: Path):
    with pytest.raises(ValueError, match="Task title cannot be blank"):
        run_command(parse_args(db_path, "add", "   "))
