from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .store import (
    ISO_DATE,
    Task,
    TaskService,
    TaskStorage,
    TaskTrackerError,
    VALID_PRIORITIES,
    VALID_RECURRENCE,
    VALID_STATUSES,
)

ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"
ANSI_DIM = "\033[2m"
ANSI_RED = "\033[31m"
ANSI_GREEN = "\033[32m"
ANSI_YELLOW = "\033[33m"
ANSI_BLUE = "\033[34m"
ANSI_MAGENTA = "\033[35m"
ANSI_CYAN = "\033[36m"

STATUS_STYLES = {
    "todo": ("○ todo", ANSI_BLUE),
    "in-progress": ("▶ in-progress", ANSI_YELLOW),
    "done": ("✓ done", ANSI_GREEN),
}
PRIORITY_STYLES = {
    "high": ("!!! high", ANSI_RED),
    "medium": ("!! medium", ANSI_YELLOW),
    "low": ("! low", ANSI_CYAN),
}


@dataclass(slots=True)
class ColorProfile:
    enabled: bool

    def apply(self, text: str, *codes: str) -> str:
        if not self.enabled or not codes:
            return text
        return f"{''.join(codes)}{text}{ANSI_RESET}"


@dataclass(slots=True)
class RenderContext:
    color: ColorProfile
    today: str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Task Tracker CLI")
    parser.add_argument("--data-file", default="data/tasks.json", help="Path to the JSON task store.")
    parser.add_argument("--db", dest="data_file", help=argparse.SUPPRESS)
    parser.add_argument(
        "--color",
        choices=("auto", "always", "never"),
        default="auto",
        help="Control ANSI color output for human-readable terminal views.",
    )
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


def _should_use_color(mode: str) -> bool:
    if mode == "always":
        return True
    if mode == "never":
        return False
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("TERM", "").lower() == "dumb":
        return False
    return sys.stdout.isatty()


def build_render_context(color_mode: str) -> RenderContext:
    return RenderContext(color=ColorProfile(_should_use_color(color_mode)), today=date.today().strftime(ISO_DATE))


def _format_due(task: Task, context: RenderContext) -> str:
    if not task.due_date:
        return context.color.apply("—", ANSI_DIM)
    if task.status != "done" and task.due_date < context.today:
        return context.color.apply(f"⚠ {task.due_date}", ANSI_RED, ANSI_BOLD)
    if task.status != "done" and task.due_date == context.today:
        return context.color.apply(f"★ {task.due_date}", ANSI_YELLOW, ANSI_BOLD)
    return task.due_date


def _format_status(status: str, context: RenderContext) -> str:
    label, color = STATUS_STYLES[status]
    return context.color.apply(label, color, ANSI_BOLD if status != "todo" else "")


def _format_priority(priority: str, context: RenderContext) -> str:
    label, color = PRIORITY_STYLES[priority]
    return context.color.apply(label, color, ANSI_BOLD if priority == "high" else "")


def format_task(task: Task, context: RenderContext | None = None) -> str:
    context = context or build_render_context("never")
    tags = ",".join(task.tags) if task.tags else context.color.apply("-", ANSI_DIM)
    repeat = task.recurrence or context.color.apply("-", ANSI_DIM)
    return (
        f"[{task.id}] {task.description} | status={_format_status(task.status, context)}"
        f" | priority={_format_priority(task.priority, context)} | due={_format_due(task, context)}"
        f" | repeat={repeat} | tags={tags}"
    )


def render_table(tasks: list[Task], context: RenderContext | None = None) -> str:
    context = context or build_render_context("never")
    if not tasks:
        return "No tasks found."
    headers = ("ID", "Description", "State", "Priority", "Due", "Repeat", "Tags")
    rows = [headers] + [
        (
            str(task.id),
            task.description,
            _format_status(task.status, context),
            _format_priority(task.priority, context),
            _format_due(task, context),
            task.recurrence or context.color.apply("—", ANSI_DIM),
            ", ".join(task.tags) or context.color.apply("—", ANSI_DIM),
        )
        for task in tasks
    ]
    widths = [max(_visible_length(row[index]) for row in rows) for index in range(len(headers))]
    lines = []
    for row_index, row in enumerate(rows):
        lines.append(" | ".join(_pad_visible(cell, widths[index]) for index, cell in enumerate(row)))
        if row_index == 0:
            lines.append("-+-".join("-" * width for width in widths))
    return "\n".join(lines)


def _visible_length(text: str) -> int:
    length = 0
    skip = False
    for char in text:
        if skip:
            if char == "m":
                skip = False
            continue
        if char == "\033":
            skip = True
            continue
        length += 1
    return length


def _pad_visible(text: str, width: int) -> str:
    return text + (" " * max(0, width - _visible_length(text)))


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


def _render_summary(payload: dict[str, int], as_json: bool, context: RenderContext) -> str:
    if as_json:
        return json.dumps(payload, indent=2)
    headline = [
        context.color.apply(f"todo {payload['todo']}", ANSI_BLUE, ANSI_BOLD),
        context.color.apply(f"in-progress {payload['in-progress']}", ANSI_YELLOW, ANSI_BOLD),
        context.color.apply(f"done {payload['done']}", ANSI_GREEN, ANSI_BOLD),
        context.color.apply(f"total {payload['total']}", ANSI_MAGENTA, ANSI_BOLD),
    ]
    detail = [
        f"overdue: {payload['overdue']}",
        f"tagged: {payload['tagged']}",
        f"unique_tags: {payload['unique_tags']}",
        f"recurring: {payload['recurring']}",
    ]
    return "Task summary\n" + "  ".join(headline) + "\n" + "  ".join(detail)


def run_cli(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    service = TaskService(TaskStorage(Path(args.data_file)))
    context = build_render_context(args.color)

    try:
        if args.command == "add":
            task = service.add_task(
                args.description,
                priority=args.priority,
                due_date=args.due,
                tags=args.tag,
                recurrence=args.repeat,
            )
            print(f"Added: {format_task(task, context)}")
            return 0
        if args.command == "list":
            tasks = _select_tasks(service, args)
            if args.json:
                print(json.dumps([task.to_dict() for task in tasks], indent=2))
            else:
                print(render_table(tasks, context))
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
            print(f"Updated: {format_task(task, context)}")
            return 0
        if args.command == "start":
            task, _ = service.set_status(args.id, "in-progress")
            print(f"Started: {format_task(task, context)}")
            return 0
        if args.command == "done":
            task, spawned_task = service.set_status(_coalesce_task_id(args), "done")
            print(f"Completed task #{task.id}: {task.description}")
            if spawned_task is not None:
                print(f"Spawned next recurring task: {format_task(spawned_task, context)}")
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
                print(f"Newest restored task: {format_task(restored[-1], context)}")
            return 0
        if args.command == "summary":
            print(_render_summary(service.summary(), args.json, context))
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
                print(f"Newest task: {format_task(imported[-1], context)}")
            return 0
    except TaskTrackerError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    parser.print_help()
    return 1


main = run_cli


if __name__ == "__main__":
    raise SystemExit(run_cli())
