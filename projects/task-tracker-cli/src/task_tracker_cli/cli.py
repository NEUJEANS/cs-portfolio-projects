from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

VALID_STATUSES = ("todo", "in-progress", "done")
DEFAULT_DB_FILENAME = ".task-tracker.json"


@dataclass(slots=True)
class Task:
    id: int
    title: str
    status: str
    created_at: str
    updated_at: str
    completed_at: str | None = None


class TaskStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> list[Task]:
        if not self.path.exists():
            return []
        payload = json.loads(self.path.read_text())
        return [Task(**item) for item in payload]

    def save(self, tasks: Iterable[Task]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        serializable = [asdict(task) for task in tasks]
        self.path.write_text(json.dumps(serializable, indent=2) + "\n")


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def next_id(tasks: list[Task]) -> int:
    return max((task.id for task in tasks), default=0) + 1


def find_task(tasks: list[Task], task_id: int) -> Task:
    for task in tasks:
        if task.id == task_id:
            return task
    raise ValueError(f"Task {task_id} does not exist")


def normalize_title(title: str) -> str:
    normalized = title.strip()
    if not normalized:
        raise ValueError("Task title cannot be blank")
    return normalized


def add_task(tasks: list[Task], title: str) -> Task:
    timestamp = now_iso()
    task = Task(
        id=next_id(tasks),
        title=normalize_title(title),
        status="todo",
        created_at=timestamp,
        updated_at=timestamp,
    )
    tasks.append(task)
    return task


def update_task_title(task: Task, title: str) -> None:
    task.title = normalize_title(title)
    task.updated_at = now_iso()


def set_task_status(task: Task, status: str) -> None:
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {status}")
    task.status = status
    task.updated_at = now_iso()
    task.completed_at = task.updated_at if status == "done" else None


def delete_task(tasks: list[Task], task_id: int) -> None:
    task = find_task(tasks, task_id)
    tasks.remove(task)


def format_task(task: Task) -> str:
    completed_suffix = f" | completed {task.completed_at}" if task.completed_at else ""
    return f"[{task.id}] {task.title} ({task.status}) | updated {task.updated_at}{completed_suffix}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Track personal tasks from the command line.")
    parser.add_argument(
        "--db",
        default=DEFAULT_DB_FILENAME,
        help="Path to the JSON task database file (default: .task-tracker.json)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add a new task")
    add_parser.add_argument("title", help="Task title")

    update_parser = subparsers.add_parser("update", help="Rename a task")
    update_parser.add_argument("id", type=int, help="Task id")
    update_parser.add_argument("title", help="New title")

    delete_parser = subparsers.add_parser("delete", help="Delete a task")
    delete_parser.add_argument("id", type=int, help="Task id")

    mark_parser = subparsers.add_parser("mark", help="Change task status")
    mark_parser.add_argument("id", type=int, help="Task id")
    mark_parser.add_argument("status", choices=VALID_STATUSES, help="New task status")

    list_parser = subparsers.add_parser("list", help="List tasks")
    list_parser.add_argument("--status", choices=VALID_STATUSES, help="Filter by status")

    subparsers.add_parser("summary", help="Show task counts by status")
    return parser


def run_command(args: argparse.Namespace) -> str:
    store = TaskStore(Path(args.db))
    tasks = store.load()

    match args.command:
        case "add":
            task = add_task(tasks, args.title)
            store.save(tasks)
            return f"Added task {task.id}: {task.title}"
        case "update":
            task = find_task(tasks, args.id)
            update_task_title(task, args.title)
            store.save(tasks)
            return f"Updated task {task.id}: {task.title}"
        case "delete":
            delete_task(tasks, args.id)
            store.save(tasks)
            return f"Deleted task {args.id}"
        case "mark":
            task = find_task(tasks, args.id)
            set_task_status(task, args.status)
            store.save(tasks)
            return f"Task {task.id} marked as {task.status}"
        case "list":
            filtered = [task for task in tasks if not args.status or task.status == args.status]
            if not filtered:
                return "No tasks found"
            return "\n".join(format_task(task) for task in filtered)
        case "summary":
            counts = {status: 0 for status in VALID_STATUSES}
            for task in tasks:
                counts[task.status] += 1
            return " | ".join(f"{status}: {counts[status]}" for status in VALID_STATUSES)
        case _:
            raise ValueError(f"Unknown command: {args.command}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        print(run_command(args))
        return 0
    except ValueError as exc:
        parser.exit(status=1, message=f"Error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
