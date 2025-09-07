from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from utils.storage import DB

@dataclass
class User:
    id: int
    name: str
    email: str

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "email": self.email}

    @classmethod
    def from_dict(cls, rec: dict) -> "User":
        return cls(id=rec["id"], name=rec["name"], email=rec["email"])

    # CRUD helpers
    @classmethod
    def create(cls, db: DB, name: str, email: str) -> "User":
        uid = db.next_user_id()
        user = cls(id=uid, name=name, email=email)
        db.add_user(user.to_dict())
        return user

    @classmethod
    def all(cls, db: DB) -> list["User"]:
        return [cls.from_dict(u) for u in db.data["users"]]

    @classmethod
    def get(cls, db: DB, user_id: Optional[int]) -> Optional["User"]:
        if user_id is None:
            return None
        for u in db.data["users"]:
            if u["id"] == user_id:
                return cls.from_dict(u)
        return None

    @classmethod
    def find_by_identity(cls, db: DB, identity: str) -> "User":
        # match by email first, then by name
        for u in db.data["users"]:
            if u["email"].lower() == identity.lower():
                return cls.from_dict(u)
        for u in db.data["users"]:
            if u["name"].lower() == identity.lower():
                return cls.from_dict(u)
        raise SystemExit(f"User not found: {identity}")