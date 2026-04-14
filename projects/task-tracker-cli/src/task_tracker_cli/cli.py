from __future__ import annotations

import argparse
import os
from pathlib import Path

from .repository import TaskRepository
from .service import TaskService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Track tasks from the command line.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add a new task")
    add_parser.add_argument("title", help="Task title")

    list_parser = subparsers.add_parser("list", help="List tasks")
    list_parser.add_argument(
        "--status",
        choices=("all", "open", "completed"),
        default="all",
        help="Filter tasks by status",
    )

    done_parser = subparsers.add_parser("done", help="Mark a task as completed")
    done_parser.add_argument("task_id", type=int, help="Task id")

    delete_parser = subparsers.add_parser("delete", help="Delete a task")
    delete_parser.add_argument("task_id", type=int, help="Task id")

    subparsers.add_parser("stats", help="Show task statistics")
    return parser


def default_data_file() -> Path:
    override = os.environ.get("TASK_TRACKER_DATA_FILE")
    if override:
        return Path(override)
    return Path.cwd() / ".task-tracker" / "tasks.json"


def format_task(task) -> str:
    marker = "x" if task.completed else " "
    return f"[{marker}] {task.id}: {task.title}"


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    service = TaskService(TaskRepository(default_data_file()))

    try:
        if args.command == "add":
            task = service.add_task(args.title)
            print(f"Added task {task.id}: {task.title}")
            return 0

        if args.command == "list":
            tasks = service.list_tasks(status=args.status)
            if not tasks:
                print("No tasks found.")
                return 0
            for task in tasks:
                print(format_task(task))
            return 0

        if args.command == "done":
            task = service.mark_done(args.task_id)
            print(f"Completed task {task.id}: {task.title}")
            return 0

        if args.command == "delete":
            task = service.delete_task(args.task_id)
            print(f"Deleted task {task.id}: {task.title}")
            return 0

        if args.command == "stats":
            stats = service.stats()
            print(f"Total: {stats.total}")
            print(f"Open: {stats.open}")
            print(f"Completed: {stats.completed}")
            return 0
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1

    parser.error("Unknown command")
    return 2
