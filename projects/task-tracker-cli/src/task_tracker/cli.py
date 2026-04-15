from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .store import (
    Task,
    TaskService,
    TaskStorage,
    TaskTrackerError,
    VALID_PRIORITIES,
    VALID_RECURRENCE,
    VALID_STATUSES,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Task Tracker CLI")
    parser.add_argument("--data-file", default="data/tasks.json", help="Path to the JSON task store.")
    parser.add_argument("--db", dest="data_file", help=argparse.SUPPRESS)
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add a task.")
    add_parser.add_argument("description")
    add_parser.add_argument("--priority", default="medium", choices=VALID_PRIORITIES)
    add_parser.add_argument("--due")
    add_parser.add_argument("--tag", action="append", default=[], help="Attach a tag. Repeat or pass comma-separated values.")
    add_parser.add_argument("--repeat", choices=VALID_RECURRENCE, help="Schedule the task to recur when completed.")

    list_parser = subparsers.add_parser("list", help="List tasks.")
    add_list_arguments(list_parser)
    list_parser.add_argument("--json", action="store_true", help="Render tasks as JSON.")

    update_parser = subparsers.add_parser("update", help="Update task fields.")
    update_parser.add_argument("id", type=int)
    update_parser.add_argument("--description")
    update_parser.add_argument("--priority", choices=VALID_PRIORITIES)
    update_parser.add_argument("--due")
    update_parser.add_argument("--clear-due", action="store_true", help="Remove the due date from the task.")
    update_parser.add_argument("--status", choices=VALID_STATUSES)
    update_parser.add_argument("--tag", action="append", default=None, help="Replace tags. Repeat or pass comma-separated values.")
    update_parser.add_argument("--clear-tags", action="store_true", help="Remove all tags from the task.")
    update_parser.add_argument("--repeat", choices=VALID_RECURRENCE, help="Replace the task recurrence rule.")
    update_parser.add_argument("--clear-repeat", action="store_true", help="Remove the recurrence rule from the task.")

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

    archive_parser = subparsers.add_parser("archive", help="Archive completed tasks into dated snapshots.")
    archive_parser.add_argument("--output-dir", help="Archive destination directory. Defaults next to the data file.")
    archive_parser.add_argument("--keep", action="store_true", help="Keep completed tasks in the active store after archiving.")

    restore_parser = subparsers.add_parser("restore", help="Restore tasks from an archive JSON snapshot.")
    restore_parser.add_argument("source", help="Path to a JSON archive snapshot created by the archive command.")
    restore_parser.add_argument(
        "--status",
        choices=("original", *VALID_STATUSES),
        default="original",
        help="Override restored task status. Defaults to the archived status.",
    )

    summary_parser = subparsers.add_parser("summary", help="Print task summary counts.")
    summary_parser.add_argument("--json", action="store_true")

    export_parser = subparsers.add_parser("export", help="Export tasks as CSV or Markdown.")
    add_list_arguments(export_parser)
    export_parser.add_argument("--format", choices=("csv", "markdown"), default="csv")
    export_parser.add_argument("--output", help="Optional destination file path. Prints to stdout when omitted.")

    import_parser = subparsers.add_parser("import", help="Import tasks from CSV or JSON.")
    import_parser.add_argument("source", help="Source file to import.")
    import_parser.add_argument("--format", choices=("csv", "json"), required=True)
    return parser


def add_list_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--status", choices=VALID_STATUSES)
    parser.add_argument("--priority", choices=VALID_PRIORITIES)
    parser.add_argument("--sort-by", default="id", choices=("id", "created_at", "updated_at", "due_date", "priority"))
    parser.add_argument("--search", help="Filter by keyword in description, tags, or recurrence.")
    parser.add_argument("--tag", action="append", default=[], help="Require a tag. Repeat or pass comma-separated values.")


def format_task(task: Task) -> str:
    due = task.due_date or "-"
    tags = ",".join(task.tags) if task.tags else "-"
    repeat = task.recurrence or "-"
    return f"[{task.id}] {task.description} | status={task.status} | priority={task.priority} | due={due} | repeat={repeat} | tags={tags}"


def render_table(tasks: list[Task]) -> str:
    if not tasks:
        return "No tasks found."
    headers = ("ID", "Description", "Status", "Priority", "Due", "Repeat", "Tags")
    rows = [headers] + [
        (
            str(task.id),
            task.description,
            task.status,
            task.priority,
            task.due_date or "-",
            task.recurrence or "-",
            ", ".join(task.tags) or "-",
        )
        for task in tasks
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


def _select_tasks(service: TaskService, args: argparse.Namespace) -> list[Task]:
    return service.list_tasks(
        status=getattr(args, "status", None),
        priority=getattr(args, "priority", None),
        sort_by=getattr(args, "sort_by", "id"),
        search=getattr(args, "search", None),
        tags=getattr(args, "tag", None),
    )


def _render_summary(payload: dict[str, int], as_json: bool) -> str:
    if as_json:
        return json.dumps(payload, indent=2)
    ordered_keys = ["todo", "in-progress", "done", "total", "overdue", "tagged", "unique_tags", "recurring"]
    return " | ".join(f"{key}: {payload[key]}" for key in ordered_keys)


def run_cli(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    service = TaskService(TaskStorage(Path(args.data_file)))

    try:
        if args.command == "add":
            task = service.add_task(
                args.description,
                priority=args.priority,
                due_date=args.due,
                tags=args.tag,
                recurrence=args.repeat,
            )
            print(f"Added: {format_task(task)}")
            return 0
        if args.command == "list":
            tasks = _select_tasks(service, args)
            if args.json:
                print(json.dumps([task.to_dict() for task in tasks], indent=2))
            else:
                print(render_table(tasks))
            return 0
        if args.command == "update":
            if args.clear_tags and args.tag is not None:
                raise TaskTrackerError("Use either --tag or --clear-tags, not both.")
            if args.clear_due and args.due is not None:
                raise TaskTrackerError("Use either --due or --clear-due, not both.")
            if args.clear_repeat and args.repeat is not None:
                raise TaskTrackerError("Use either --repeat or --clear-repeat, not both.")
            if (
                all(value is None for value in [args.description, args.priority, args.due, args.status, args.repeat])
                and not args.clear_tags
                and args.tag is None
                and not args.clear_due
                and not args.clear_repeat
            ):
                raise TaskTrackerError("Provide at least one field to update.")
            task = service.update_task(
                args.id,
                description=args.description,
                priority=args.priority,
                due_date="" if args.clear_due else args.due,
                status=args.status,
                tags=[] if args.clear_tags else args.tag,
                recurrence="" if args.clear_repeat else args.repeat,
            )
            print(f"Updated: {format_task(task)}")
            return 0
        if args.command == "start":
            task, _ = service.set_status(args.id, "in-progress")
            print(f"Started: {format_task(task)}")
            return 0
        if args.command == "done":
            task, spawned_task = service.set_status(_coalesce_task_id(args), "done")
            print(f"Completed task #{task.id}: {task.description}")
            if spawned_task is not None:
                print(f"Spawned next recurring task: {format_task(spawned_task)}")
            return 0
        if args.command == "reopen":
            task, _ = service.set_status(args.task_id, "todo")
            print(f"Reopened task #{task.id}: {task.description}")
            return 0
        if args.command == "delete":
            task = service.delete_task(_coalesce_task_id(args))
            print(f"Deleted task #{task.id}: {task.description}")
            return 0
        if args.command == "archive":
            snapshot = service.archive_completed_tasks(
                Path(args.output_dir) if args.output_dir else None,
                keep=args.keep,
            )
            print(f"Archived {len(snapshot.archived_tasks)} completed task(s) at {snapshot.created_at}")
            print(f"JSON snapshot: {snapshot.json_path}")
            print(f"Markdown snapshot: {snapshot.markdown_path}")
            if args.keep:
                print("Completed tasks were kept in the active store.")
            else:
                print(f"Remaining active tasks: {len(snapshot.remaining_tasks)}")
            return 0
        if args.command == "restore":
            restored = service.restore_archive(Path(args.source), status=args.status)
            print(f"Restored {len(restored)} task(s) from {args.source}")
            if restored:
                print(f"Newest restored task: {format_task(restored[-1])}")
            return 0
        if args.command == "summary":
            print(_render_summary(service.summary(), args.json))
            return 0
        if args.command == "export":
            tasks = _select_tasks(service, args)
            exported = service.export_tasks(tasks, args.format)
            if args.output:
                destination = Path(args.output)
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(exported, encoding="utf-8", newline="")
                print(f"Exported {len(tasks)} task(s) to {destination}")
            else:
                print(exported, end="" if exported.endswith("\n") else "\n")
            return 0
        if args.command == "import":
            imported = service.import_tasks(Path(args.source), args.format)
            print(f"Imported {len(imported)} task(s) from {args.source}")
            if imported:
                print(f"Newest task: {format_task(imported[-1])}")
            return 0
    except TaskTrackerError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    parser.print_help()
    return 1


main = run_cli


if __name__ == "__main__":
    raise SystemExit(run_cli())
