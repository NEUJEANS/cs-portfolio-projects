from __future__ import annotations

import json
from pathlib import Path
from tempfile import NamedTemporaryFile

from .models import Task


class TaskRepository:
    def __init__(self, data_file: Path) -> None:
        self.data_file = Path(data_file)

    def load(self) -> list[Task]:
        if not self.data_file.exists():
            return []

        raw = self.data_file.read_text(encoding="utf-8").strip()
        if not raw:
            return []

        payload = json.loads(raw)
        return [Task.from_dict(item) for item in payload]

    def save(self, tasks: list[Task]) -> None:
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        serialized = json.dumps([task.to_dict() for task in tasks], indent=2) + "\n"

        with NamedTemporaryFile("w", delete=False, encoding="utf-8", dir=self.data_file.parent) as tmp:
            tmp.write(serialized)
            temp_path = Path(tmp.name)

        temp_path.replace(self.data_file)
