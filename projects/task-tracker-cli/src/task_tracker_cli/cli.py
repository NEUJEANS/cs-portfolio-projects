from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from .store import Task, TaskStore, now_iso, validate_due_date, validate_priority, validate_status


DEFAULT_DB = Path(__file__).resolve().parents[2] / "data" / "tasks.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="task-tracker-cli", description="Track personal tasks from the command line.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="Path to the JSON database file")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add a new task")
    add_parser.add_argument("title")
    add_parser.add_argument("--priority", default="medium")
    add_parser.add_argument("--due")

    list_parser = subparsers.add_parser("list", help="List tasks")
    list_parser.add_argument("--status")
    list_parser.add_argument("--priority")
    list_parser.add_argument("--search")
    list_parser.add_argument("--due-before")
    list_parser.add_argument("--json", action="store_true")

    done_parser = subparsers.add_parser("done", help="Mark a task as done")
    done_parser.add_argument("task_id", type=int)

    delete_parser = subparsers.add_parser("delete", help="Delete a task")
    delete_parser.add_argument("task_id", type=int)

    summary_parser = subparsers.add_parser("summary", help="Show task counts")
    summary_parser.add_argument("--json", action="store_true")

    return parser


def format_task(task: Task) -> str:
    due = task.due_date or "-"
    return f"[{task.id}] {task.title} | status={task.status} priority={task.priority} due={due}"


def find_task(tasks: list[Task], task_id: int) -> Task | None:
    return next((task for task in tasks if task.id == task_id), None)


def filter_tasks(tasks: list[Task], *, status: str | None, priority: str | None, search: str | None, due_before: str | None) -> list[Task]:
    result = tasks
    if status:
        status = validate_status(status)
        result = [task for task in result if task.status == status]
    if priority:
        priority = validate_priority(priority)
        result = [task for task in result if task.priority == priority]
    if search:
        needle = search.lower()
        result = [task for task in result if needle in task.title.lower()]
    if due_before:
        limit = validate_due_date(due_before)
        result = [task for task in result if task.due_date is not None and task.due_date <= limit]
    return sorted(result, key=lambda task: (task.status, task.due_date or "9999-12-31", task.id))


def print_json(payload: object) -> None:
    print(json.dumps(payload, indent=2))


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    store = TaskStore(args.db)
    tasks = store.load()

    try:
        if args.command == "add":
            timestamp = now_iso()
            task = Task(
                id=store.next_id(tasks),
                title=args.title.strip(),
                status="todo",
                priority=validate_priority(args.priority),
                due_date=validate_due_date(args.due),
                created_at=timestamp,
                updated_at=timestamp,
            )
            if not task.title:
                raise ValueError("task title cannot be empty")
            tasks.append(task)
            store.save(tasks)
            print(f"Added task {task.id}: {task.title}")
            return 0

        if args.command == "list":
            filtered = filter_tasks(tasks, status=args.status, priority=args.priority, search=args.search, due_before=args.due_before)
            if args.json:
                print_json([asdict(task) for task in filtered])
            elif filtered:
                for task in filtered:
                    print(format_task(task))
            else:
                print("No tasks found.")
            return 0

        if args.command == "done":
            task = find_task(tasks, args.task_id)
            if task is None:
                raise ValueError(f"task {args.task_id} not found")
            task.status = "done"
            task.updated_at = now_iso()
            store.save(tasks)
            print(f"Completed task {task.id}: {task.title}")
            return 0

        if args.command == "delete":
            task = find_task(tasks, args.task_id)
            if task is None:
                raise ValueError(f"task {args.task_id} not found")
            tasks = [item for item in tasks if item.id != args.task_id]
            store.save(tasks)
            print(f"Deleted task {task.id}: {task.title}")
            return 0

        if args.command == "summary":
            completed = sum(task.status == "done" for task in tasks)
            payload = {
                "total": len(tasks),
                "todo": sum(task.status == "todo" for task in tasks),
                "done": completed,
                "completion_rate": round((completed / len(tasks)) * 100, 2) if tasks else 0.0,
                "overdue": sum(task.status != "done" and task.due_date is not None and task.due_date < now_iso()[:10] for task in tasks),
            }
            if args.json:
                print_json(payload)
            else:
                for key, value in payload.items():
                    print(f"{key}: {value}")
            return 0
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
