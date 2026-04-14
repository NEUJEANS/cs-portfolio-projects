from __future__ import annotations

import csv
import json
from calendar import monthrange
from dataclasses import asdict, dataclass, field
from datetime import UTC, date, datetime, timedelta
from io import StringIO
from pathlib import Path
from typing import Iterable

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
VALID_PRIORITIES = tuple(PRIORITY_ORDER.keys())
VALID_STATUSES = ("todo", "in-progress", "done")
VALID_RECURRENCE = ("daily", "weekly", "monthly")
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
    tags: list[str] = field(default_factory=list)
    recurrence: str | None = None

    @classmethod
    def create(
        cls,
        task_id: int,
        description: str,
        priority: str = "medium",
        due_date: str | None = None,
        tags: list[str] | None = None,
        recurrence: str | None = None,
    ) -> "Task":
        description = description.strip()
        if not description:
            raise TaskTrackerError("Description cannot be empty.")

        validate_priority(priority)
        normalized_due_date = normalize_due_date(due_date)
        normalized_tags = normalize_tags(tags or [])
        normalized_recurrence = normalize_recurrence(recurrence)
        if normalized_recurrence and normalized_due_date is None:
            raise TaskTrackerError("Recurring tasks require a due date.")
        timestamp = utc_now()
        return cls(
            id=task_id,
            description=description,
            status="todo",
            priority=priority,
            due_date=normalized_due_date,
            created_at=timestamp,
            updated_at=timestamp,
            tags=normalized_tags,
            recurrence=normalized_recurrence,
        )

    @classmethod
    def from_dict(cls, payload: dict) -> "Task":
        data = dict(payload)
        data.setdefault("tags", [])
        data.setdefault("recurrence", None)
        return cls(**data)

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

    def list_tasks(
        self,
        status: str | None = None,
        priority: str | None = None,
        sort_by: str = "id",
        search: str | None = None,
        tags: list[str] | None = None,
    ) -> list[Task]:
        tasks = self.storage.load()
        if status:
            validate_status(status)
            tasks = [task for task in tasks if task.status == status]
        if priority:
            validate_priority(priority)
            tasks = [task for task in tasks if task.priority == priority]
        if search:
            needle = search.strip().lower()
            tasks = [
                task
                for task in tasks
                if needle in task.description.lower()
                or any(needle in tag.lower() for tag in task.tags)
                or (task.recurrence is not None and needle in task.recurrence)
            ]
        normalized_tags = normalize_tags(tags or []) if tags else []
        if normalized_tags:
            tasks = [task for task in tasks if all(tag in task.tags for tag in normalized_tags)]
        return sorted(tasks, key=lambda task: sort_key(task, sort_by))

    def add_task(
        self,
        description: str,
        priority: str = "medium",
        due_date: str | None = None,
        tags: list[str] | None = None,
        recurrence: str | None = None,
    ) -> Task:
        tasks = self.storage.load()
        task = Task.create(
            self._next_id(tasks),
            description,
            priority=priority,
            due_date=due_date,
            tags=tags,
            recurrence=recurrence,
        )
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
        tags: list[str] | None = None,
        recurrence: str | None = None,
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
        if tags is not None:
            task.tags = normalize_tags(tags)
        if recurrence is not None:
            task.recurrence = normalize_recurrence(recurrence)
        if task.recurrence and task.due_date is None:
            raise TaskTrackerError("Recurring tasks require a due date.")

        task.updated_at = utc_now()
        self.storage.save(tasks)
        return task

    def set_status(self, task_id: int, status: str) -> tuple[Task, Task | None]:
        validate_status(status)
        tasks = self.storage.load()
        task = find_task(tasks, task_id)
        task.status = status
        task.updated_at = utc_now()
        spawned_task: Task | None = None
        if status == "done" and task.recurrence and task.due_date:
            spawned_task = Task.create(
                self._next_id(tasks),
                task.description,
                priority=task.priority,
                due_date=advance_due_date(task.due_date, task.recurrence),
                tags=list(task.tags),
                recurrence=task.recurrence,
            )
            tasks.append(spawned_task)
        self.storage.save(tasks)
        return task, spawned_task

    def delete_task(self, task_id: int) -> Task:
        tasks = self.storage.load()
        task = find_task(tasks, task_id)
        remaining = [item for item in tasks if item.id != task_id]
        self.storage.save(remaining)
        return task

    def summary(self) -> dict[str, int]:
        counts = {status: 0 for status in VALID_STATUSES}
        overdue = 0
        tagged = 0
        recurring = 0
        unique_tags: set[str] = set()
        today = date.today().strftime(ISO_DATE)
        for task in self.storage.load():
            counts[task.status] += 1
            if task.status != "done" and task.due_date and task.due_date < today:
                overdue += 1
            if task.tags:
                tagged += 1
                unique_tags.update(task.tags)
            if task.recurrence:
                recurring += 1
        counts["total"] = sum(counts.values())
        counts["overdue"] = overdue
        counts["tagged"] = tagged
        counts["unique_tags"] = len(unique_tags)
        counts["recurring"] = recurring
        return counts

    def export_tasks(self, tasks: list[Task], output_format: str) -> str:
        if output_format == "csv":
            return render_csv(tasks)
        if output_format == "markdown":
            return render_markdown(tasks)
        raise TaskTrackerError("format must be one of: csv, markdown")

    @staticmethod
    def _next_id(tasks: list[Task]) -> int:
        return max((task.id for task in tasks), default=0) + 1


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


def normalize_recurrence(value: str | None) -> str | None:
    if value in (None, "", "none"):
        return None
    if value not in VALID_RECURRENCE:
        raise TaskTrackerError(f"Recurrence must be one of: {', '.join(VALID_RECURRENCE)}")
    return value


def advance_due_date(due_date: str, recurrence: str) -> str:
    current = date.fromisoformat(due_date)
    if recurrence == "daily":
        return (current + timedelta(days=1)).strftime(ISO_DATE)
    if recurrence == "weekly":
        return (current + timedelta(days=7)).strftime(ISO_DATE)
    if recurrence == "monthly":
        year = current.year + (1 if current.month == 12 else 0)
        month = 1 if current.month == 12 else current.month + 1
        day = min(current.day, monthrange(year, month)[1])
        return date(year, month, day).strftime(ISO_DATE)
    raise TaskTrackerError(f"Recurrence must be one of: {', '.join(VALID_RECURRENCE)}")


def normalize_tags(tags: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for raw_tag in tags:
        for part in raw_tag.split(','):
            tag = part.strip().lower().replace(' ', '-')
            if not tag:
                continue
            if not all(ch.isalnum() or ch in {'-', '_'} for ch in tag):
                raise TaskTrackerError(
                    "Tags may only contain letters, numbers, hyphens, and underscores."
                )
            if tag not in seen:
                seen.add(tag)
                normalized.append(tag)
    return normalized


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


def render_csv(tasks: list[Task]) -> str:
    buffer = StringIO(newline="")
    writer = csv.DictWriter(
        buffer,
        fieldnames=["id", "description", "status", "priority", "due_date", "recurrence", "tags", "created_at", "updated_at"],
    )
    writer.writeheader()
    for task in tasks:
        writer.writerow(
            {
                "id": task.id,
                "description": task.description,
                "status": task.status,
                "priority": task.priority,
                "due_date": task.due_date or "",
                "recurrence": task.recurrence or "",
                "tags": ",".join(task.tags),
                "created_at": task.created_at,
                "updated_at": task.updated_at,
            }
        )
    return buffer.getvalue()


def render_markdown(tasks: list[Task]) -> str:
    lines = ["# Task Export", "", f"Total tasks: {len(tasks)}", ""]
    if not tasks:
        lines.append("No tasks found.")
        return "\n".join(lines) + "\n"

    lines.extend(
        [
            "| ID | Description | Status | Priority | Due | Repeat | Tags |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for task in tasks:
        description = task.description.replace("|", "\\|")
        tags = ", ".join(task.tags) if task.tags else "-"
        lines.append(
            f"| {task.id} | {description} | {task.status} | {task.priority} | {task.due_date or '-'} | {task.recurrence or '-'} | {tags} |"
        )
    return "\n".join(lines) + "\n"
