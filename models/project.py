from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from utils.storage import DB

@dataclass
class Project:
    id: int
    title: str
    description: str | None
    due_date: str | None  # ISO date
    owner_id: Optional[int]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "due_date": self.due_date,
            "owner_id": self.owner_id,
        }

    @classmethod
    def from_dict(cls, rec: dict) -> "Project":
        return cls(
            id=rec["id"],
            title=rec["title"],
            description=rec.get("description"),
            due_date=rec.get("due_date"),
            owner_id=rec.get("owner_id"),
        )

    # CRUD helpers
    @classmethod
    def create(cls, db: DB, title: str, description: str | None, due_date: str | None, owner_id: Optional[int]) -> "Project":
        pid = db.next_project_id()
        proj = cls(id=pid, title=title, description=description, due_date=due_date, owner_id=owner_id)
        db.add_project(proj.to_dict())
        return proj

    @classmethod
    def all(cls, db: DB) -> list["Project"]:
        return [cls.from_dict(p) for p in db.data["projects"]]

    @classmethod
    def get(cls, db: DB, project_id: Optional[int]) -> Optional["Project"]:
        if project_id is None:
            return None
        for p in db.data["projects"]:
            if p["id"] == project_id:
                return cls.from_dict(p)
        return None

    @classmethod
    def find_by_title(cls, db: DB, title: str) -> "Project":
        for p in db.data["projects"]:
            if p["title"].lower() == title.lower():
                return cls.from_dict(p)
        raise SystemExit(f"Project not found: {title}")