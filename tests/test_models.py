import os
import json
from utils.storage import DB, STORE
from models.user import User
from models.project import Project
from models.task import Task

def setup_function(_):
    # reset store for isolated tests
    if STORE.exists():
        STORE.unlink()


def test_user_project_task_relationships():
    db = DB(); db.load()
    alice = User.create(db, name="Alice", email="alice@example.com")
    proj = Project.create(db, title="CLI Tool", description="Build CLI", due_date=None, owner_id=alice.id)
    task = Task.create(db, title="Implement add-task", project_id=proj.id, assigned_to=alice.id)
    db.save()

    # reload and assert
    db2 = DB(); db2.load()
    users = User.all(db2)
    projects = Project.all(db2)
    tasks = Task.all(db2)

    assert users[0].name == "Alice"
    assert projects[0].owner_id == users[0].id
    assert tasks[0].project_id == projects[0].id
    assert tasks[0].assigned_to == users[0].id


def test_task_status_property_guard():
    db = DB(); db.load()
    proj = Project.create(db, title="P", description=None, due_date=None, owner_id=None)
    t = Task.create(db, title="T", project_id=proj.id)
    t.status = "doing"
    db.update_task(t)
    db.save()

    db2 = DB(); db2.load()
    t2 = Task.get(db2, t.id)
    assert t2.status == "doing"

    try:
        t2.status = "invalid"
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid status should raise")