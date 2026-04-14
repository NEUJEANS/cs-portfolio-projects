from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Iterable

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
VALID_PRIORITIES = tuple(PRIORITY_ORDER.keys())
VALID_STATUSES = ("todo", "in-progress", "done")
ISO_DATE = "%Y-%m-%d"


class TaskTrackerError(Exception):
    """Domain-level exception for user-facing task tracker errors."""


@dataclass(slots=True)
class Task:
    id: int
    description: str
    status: str
    priority: str
    due_date: str | None
    created_at: str
    updated_at: str

    @classmethod
    def create(cls, task_id: int, description: str, priority: str = "medium", due_date: str | None = None) -> "Task":
        description = description.strip()
        if not description:
            raise TaskTrackerError("Description cannot be empty.")

        validate_priority(priority)
        normalized_due_date = normalize_due_date(due_date)
        timestamp = utc_now()
        return cls(
            id=task_id,
            description=description,
            status="todo",
            priority=priority,
            due_date=normalized_due_date,
            created_at=timestamp,
            updated_at=timestamp,
        )

    @classmethod
    def from_dict(cls, payload: dict) -> "Task":
        return cls(**payload)

    def to_dict(self) -> dict:
        return asdict(self)


class TaskStorage:
    def __init__(self, data_file: Path) -> None:
        self.data_file = data_file

    def load(self) -> list[Task]:
        if not self.data_file.exists():
            return []

        with self.data_file.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)

        return [Task.from_dict(item) for item in raw]

    def save(self, tasks: Iterable[Task]) -> None:
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        payload = [task.to_dict() for task in tasks]
        with self.data_file.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
            handle.write("\n")


class TaskService:
    def __init__(self, storage: TaskStorage) -> None:
        self.storage = storage

    def list_tasks(self, status: str | None = None, priority: str | None = None, sort_by: str = "id") -> list[Task]:
        tasks = self.storage.load()
        if status:
            validate_status(status)
            tasks = [task for task in tasks if task.status == status]
        if priority:
            validate_priority(priority)
            tasks = [task for task in tasks if task.priority == priority]
        return sorted(tasks, key=lambda task: sort_key(task, sort_by))

    def add_task(self, description: str, priority: str = "medium", due_date: str | None = None) -> Task:
        tasks = self.storage.load()
        next_id = max((task.id for task in tasks), default=0) + 1
        task = Task.create(next_id, description, priority=priority, due_date=due_date)
        tasks.append(task)
        self.storage.save(tasks)
        return task

    def update_task(
        self,
        task_id: int,
        description: str | None = None,
        priority: str | None = None,
        due_date: str | None = None,
        status: str | None = None,
    ) -> Task:
        tasks = self.storage.load()
        task = find_task(tasks, task_id)

        if description is not None:
            description = description.strip()
            if not description:
                raise TaskTrackerError("Description cannot be empty.")
            task.description = description
        if priority is not None:
            validate_priority(priority)
            task.priority = priority
        if due_date is not None:
            task.due_date = normalize_due_date(due_date)
        if status is not None:
            validate_status(status)
            task.status = status

        task.updated_at = utc_now()
        self.storage.save(tasks)
        return task

    def set_status(self, task_id: int, status: str) -> Task:
        validate_status(status)
        return self.update_task(task_id, status=status)

    def delete_task(self, task_id: int) -> Task:
        tasks = self.storage.load()
        task = find_task(tasks, task_id)
        remaining = [item for item in tasks if item.id != task_id]
        self.storage.save(remaining)
        return task

    def summary(self) -> dict[str, int]:
        counts = {status: 0 for status in VALID_STATUSES}
        for task in self.storage.load():
            counts[task.status] += 1
        counts["total"] = sum(counts.values())
        return counts


def find_task(tasks: list[Task], task_id: int) -> Task:
    for task in tasks:
        if task.id == task_id:
            return task
    raise TaskTrackerError(f"Task {task_id} was not found.")


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_due_date(value: str | None) -> str | None:
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(value).strftime(ISO_DATE)
    except ValueError as exc:
        raise TaskTrackerError("Due date must use YYYY-MM-DD format.") from exc


def validate_priority(priority: str) -> None:
    if priority not in VALID_PRIORITIES:
        raise TaskTrackerError(f"Priority must be one of: {', '.join(VALID_PRIORITIES)}")


def validate_status(status: str) -> None:
    if status not in VALID_STATUSES:
        raise TaskTrackerError(f"Status must be one of: {', '.join(VALID_STATUSES)}")


def sort_key(task: Task, sort_by: str):
    if sort_by == "priority":
        return PRIORITY_ORDER[task.priority], task.id
    if sort_by == "due_date":
        return task.due_date is None, task.due_date or "9999-12-31", task.id
    if sort_by in {"id", "created_at", "updated_at"}:
        return getattr(task, sort_by)
    raise TaskTrackerError("sort-by must be one of: id, created_at, updated_at, due_date, priority")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Task Tracker CLI")
    parser.add_argument("--data-file", default="data/tasks.json", help="Path to the JSON task store.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add a task.")
    add_parser.add_argument("description")
    add_parser.add_argument("--priority", default="medium", choices=VALID_PRIORITIES)
    add_parser.add_argument("--due")

    list_parser = subparsers.add_parser("list", help="List tasks.")
    list_parser.add_argument("--status", choices=VALID_STATUSES)
    list_parser.add_argument("--priority", choices=VALID_PRIORITIES)
    list_parser.add_argument("--sort-by", default="id", choices=("id", "created_at", "updated_at", "due_date", "priority"))

    update_parser = subparsers.add_parser("update", help="Update task fields.")
    update_parser.add_argument("id", type=int)
    update_parser.add_argument("--description")
    update_parser.add_argument("--priority", choices=VALID_PRIORITIES)
    update_parser.add_argument("--due")
    update_parser.add_argument("--status", choices=VALID_STATUSES)

    start_parser = subparsers.add_parser("start", help="Mark a task as in-progress.")
    start_parser.add_argument("id", type=int)

    done_parser = subparsers.add_parser("done", help="Mark a task as done.")
    done_parser.add_argument("id", type=int)

    delete_parser = subparsers.add_parser("delete", help="Delete a task.")
    delete_parser.add_argument("id", type=int)

    subparsers.add_parser("summary", help="Print task summary counts.")
    return parser


def format_task(task: Task) -> str:
    due = task.due_date or "-"
    return f"[{task.id}] {task.description} | status={task.status} | priority={task.priority} | due={due}"


def run_cli(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    service = TaskService(TaskStorage(Path(args.data_file)))

    try:
        if args.command == "add":
            task = service.add_task(args.description, priority=args.priority, due_date=args.due)
            print(f"Added: {format_task(task)}")
            return 0
        if args.command == "list":
            tasks = service.list_tasks(status=args.status, priority=args.priority, sort_by=args.sort_by)
            if not tasks:
                print("No tasks found.")
                return 0
            for task in tasks:
                print(format_task(task))
            return 0
        if args.command == "update":
            if all(value is None for value in [args.description, args.priority, args.due, args.status]):
                raise TaskTrackerError("Provide at least one field to update.")
            task = service.update_task(args.id, description=args.description, priority=args.priority, due_date=args.due, status=args.status)
            print(f"Updated: {format_task(task)}")
            return 0
        if args.command == "start":
            task = service.set_status(args.id, "in-progress")
            print(f"Started: {format_task(task)}")
            return 0
        if args.command == "done":
            task = service.set_status(args.id, "done")
            print(f"Completed: {format_task(task)}")
            return 0
        if args.command == "delete":
            task = service.delete_task(args.id)
            print(f"Deleted task {task.id}: {task.description}")
            return 0
        if args.command == "summary":
            summary = service.summary()
            print(json.dumps(summary, indent=2))
            return 0
    except TaskTrackerError as exc:
        print(f"Error: {exc}")
        return 1

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(run_cli())
