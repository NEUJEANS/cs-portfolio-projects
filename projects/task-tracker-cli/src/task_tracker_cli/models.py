from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(slots=True)
class Task:
    id: int
    title: str
    completed: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict) -> "Task":
        return cls(
            id=int(payload["id"]),
            title=str(payload["title"]),
            completed=bool(payload.get("completed", False)),
        )
