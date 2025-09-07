from __future__ import annotations
import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
STORE = DATA_DIR / "store.json"

DEFAULT = {"users": [], "projects": [], "tasks": []}

class DB:
    def __init__(self):
        self.data: dict[str, list[dict[str, Any]]] = {"users": [], "projects": [], "tasks": []}
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not STORE.exists():
            STORE.write_text(json.dumps(DEFAULT, indent=2))

    def load(self) -> None:
        self.data = json.loads(STORE.read_text())

    def save(self) -> None:
        STORE.write_text(json.dumps(self.data, indent=2))

    @staticmethod
    def read_raw() -> dict[str, Any]:
        if STORE.exists():
            return json.loads(STORE.read_text())
        return DEFAULT

    # --- Users ---
    def next_user_id(self) -> int:
        ids = [u.get("id", 0) for u in self.data["users"]]
        return (max(ids) + 1) if ids else 1

    def add_user(self, rec: dict[str, Any]) -> None:
        self.data["users"].append(rec)

    # --- Projects ---
    def next_project_id(self) -> int:
        ids = [p.get("id", 0) for p in self.data["projects"]]
        return (max(ids) + 1) if ids else 1

    def add_project(self, rec: dict[str, Any]) -> None:
        self.data["projects"].append(rec)

    def update_project(self, proj: "Project") -> None:
        for i, p in enumerate(self.data["projects"]):
            if p["id"] == proj.id:
                self.data["projects"][i] = proj.to_dict()
                return

    # --- Tasks ---
    def next_task_id(self) -> int:
        ids = [t.get("id", 0) for t in self.data["tasks"]]
        return (max(ids) + 1) if ids else 1

    def add_task(self, rec: dict[str, Any]) -> None:
        self.data["tasks"].append(rec)

    def update_task(self, task: "Task") -> None:
        for i, t in enumerate(self.data["tasks"]):
            if t["id"] == task.id:
                self.data["tasks"][i] = task.to_dict()
                return