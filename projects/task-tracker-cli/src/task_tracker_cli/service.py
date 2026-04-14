from __future__ import annotations

from dataclasses import dataclass

from .models import Task
from .repository import TaskRepository


@dataclass(slots=True)
class TaskStats:
    total: int
    open: int
    completed: int


class TaskService:
    def __init__(self, repository: TaskRepository) -> None:
        self.repository = repository

    def add_task(self, title: str) -> Task:
        title = title.strip()
        if not title:
            raise ValueError("Task title cannot be empty.")

        tasks = self.repository.load()
        next_id = max((task.id for task in tasks), default=0) + 1
        task = Task(id=next_id, title=title)
        tasks.append(task)
        self.repository.save(tasks)
        return task

    def list_tasks(self, status: str = "all") -> list[Task]:
        tasks = self.repository.load()
        if status == "open":
            return [task for task in tasks if not task.completed]
        if status == "completed":
            return [task for task in tasks if task.completed]
        return tasks

    def mark_done(self, task_id: int) -> Task:
        tasks = self.repository.load()
        for task in tasks:
            if task.id == task_id:
                task.completed = True
                self.repository.save(tasks)
                return task
        raise ValueError(f"Task {task_id} not found.")

    def delete_task(self, task_id: int) -> Task:
        tasks = self.repository.load()
        for index, task in enumerate(tasks):
            if task.id == task_id:
                removed = tasks.pop(index)
                self.repository.save(tasks)
                return removed
        raise ValueError(f"Task {task_id} not found.")

    def stats(self) -> TaskStats:
        tasks = self.repository.load()
        completed = sum(1 for task in tasks if task.completed)
        total = len(tasks)
        return TaskStats(total=total, open=total - completed, completed=completed)
