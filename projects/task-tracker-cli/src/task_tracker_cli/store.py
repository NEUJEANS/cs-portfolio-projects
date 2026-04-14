from __future__ import annotations

import json
import tempfile
from dataclasses import asdict, dataclass
from datetime import date, datetime, UTC
from pathlib import Path

VALID_STATUSES = {"todo", "done"}
VALID_PRIORITIES = {"low", "medium", "high"}


@dataclass(slots=True)
class Task:
    id: int
    title: str
    status: str
    priority: str
    due_date: str | None
    created_at: str
    updated_at: str

    @classmethod
    def from_dict(cls, payload: dict) -> "Task":
        return cls(**payload)


class TaskStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def load(self) -> list[Task]:
        if not self.db_path.exists():
            return []
        data = json.loads(self.db_path.read_text(encoding="utf-8"))
        return [Task.from_dict(item) for item in data]

    def save(self, tasks: list[Task]) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_path = tempfile.mkstemp(dir=str(self.db_path.parent), prefix=".tasks-", suffix=".json")
        try:
            with open(fd, "w", encoding="utf-8") as handle:
                json.dump([asdict(task) for task in tasks], handle, indent=2)
                handle.write("\n")
            Path(temp_path).replace(self.db_path)
        except Exception:
            Path(temp_path).unlink(missing_ok=True)
            raise

    def next_id(self, tasks: list[Task]) -> int:
        return max((task.id for task in tasks), default=0) + 1


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def validate_priority(value: str) -> str:
    normalized = value.lower()
    if normalized not in VALID_PRIORITIES:
        raise ValueError(f"invalid priority: {value}")
    return normalized


def validate_status(value: str) -> str:
    normalized = value.lower()
    if normalized not in VALID_STATUSES:
        raise ValueError(f"invalid status: {value}")
    return normalized


def validate_due_date(value: str | None) -> str | None:
    if value is None:
        return None
    date.fromisoformat(value)
    return value
