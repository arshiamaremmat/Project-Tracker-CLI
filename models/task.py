
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from utils.storage import DB

VALID_STATUSES = {"todo", "doing", "done"}

@dataclass
class Task:
    id: int
    title: str
    project_id: int
    _status: str = field(default="todo", repr=False)
    assigned_to: Optional[int] = None
    contributors: list[int] = field(default_factory=list)

    # Encapsulation via property
    @property
    def status(self) -> str:
        return self._status

    @status.setter
    def status(self, value: str) -> None:
        if value not in VALID_STATUSES:
            raise ValueError(f"Invalid status: {value}")
        self._status = value

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "project_id": self.project_id,
            "status": self._status,
            "assigned_to": self.assigned_to,
            "contributors": self.contributors,
        }

    @classmethod
    def from_dict(cls, rec: dict) -> "Task":
        t = cls(
            id=rec["id"],
            title=rec["title"],
            project_id=rec["project_id"],
            assigned_to=rec.get("assigned_to"),
            contributors=list(rec.get("contributors", [])),
        )
        t.status = rec.get("status", "todo")
        return t

    # CRUD helpers
    @classmethod
    def create(cls, db: DB, title: str, project_id: int, assigned_to: Optional[int] = None) -> "Task":
        tid = db.next_task_id()
        task = cls(id=tid, title=title, project_id=project_id, assigned_to=assigned_to)
        db.add_task(task.to_dict())
        return task

    @classmethod
    def all(cls, db: DB) -> list["Task"]:
        return [cls.from_dict(t) for t in db.data["tasks"]]

    @classmethod
    def get(cls, db: DB, task_id: Optional[int]) -> Optional["Task"]:
        if task_id is None:
            return None
        for t in db.data["tasks"]:
            if t["id"] == task_id:
                return cls.from_dict(t)
        return None

    @classmethod
    def for_project(cls, db: DB, project_id: int) -> list["Task"]:
        return [cls.from_dict(t) for t in db.data["tasks"] if t["project_id"] == project_id]