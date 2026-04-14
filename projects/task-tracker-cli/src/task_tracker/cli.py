from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .store import Task, TaskService, TaskStorage, TaskTrackerError, VALID_PRIORITIES, VALID_STATUSES


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Task Tracker CLI")
    parser.add_argument("--data-file", default="data/tasks.json", help="Path to the JSON task store.")
    parser.add_argument("--db", dest="data_file", help=argparse.SUPPRESS)
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
    done_parser.add_argument("id", nargs="?", type=int)
    done_parser.add_argument("task_id", nargs="?", type=int)

    reopen_parser = subparsers.add_parser("reopen", help="Mark a task as todo.")
    reopen_parser.add_argument("task_id", type=int)

    delete_parser = subparsers.add_parser("delete", help="Delete a task.")
    delete_parser.add_argument("id", nargs="?", type=int)
    delete_parser.add_argument("task_id", nargs="?", type=int)

    subparsers.add_parser("summary", help="Print task summary counts.")
    return parser


def format_task(task: Task) -> str:
    due = task.due_date or "-"
    return f"[{task.id}] {task.description} | status={task.status} | priority={task.priority} | due={due}"


def render_table(tasks: list[Task]) -> str:
    if not tasks:
        return "No tasks found."
    headers = ("ID", "Description", "Status", "Priority", "Due")
    rows = [headers] + [
        (str(task.id), task.description, task.status, task.priority, task.due_date or "-") for task in tasks
    ]
    widths = [max(len(row[index]) for row in rows) for index in range(len(headers))]
    lines = []
    for row_index, row in enumerate(rows):
        lines.append(" | ".join(cell.ljust(widths[index]) for index, cell in enumerate(row)))
        if row_index == 0:
            lines.append("-+-".join("-" * width for width in widths))
    return "\n".join(lines)


def _coalesce_task_id(args: argparse.Namespace) -> int:
    task_id = getattr(args, "id", None)
    alt_task_id = getattr(args, "task_id", None)
    return task_id if task_id is not None else alt_task_id


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
            print(render_table(tasks))
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
            task = service.set_status(_coalesce_task_id(args), "done")
            print(f"Completed task #{task.id}: {task.description}")
            return 0
        if args.command == "reopen":
            task = service.set_status(args.task_id, "todo")
            print(f"Reopened task #{task.id}: {task.description}")
            return 0
        if args.command == "delete":
            task = service.delete_task(_coalesce_task_id(args))
            print(f"Deleted task #{task.id}: {task.description}")
            return 0
        if args.command == "summary":
            print(json.dumps(service.summary(), indent=2))
            return 0
    except TaskTrackerError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    parser.print_help()
    return 1


main = run_cli


if __name__ == "__main__":
    raise SystemExit(run_cli())
