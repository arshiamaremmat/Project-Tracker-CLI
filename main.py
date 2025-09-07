#!/usr/bin/env python3
import argparse
import sys
from rich.console import Console
from rich.table import Table
from dateutil import parser as dateparser

from utils.storage import DB
from utils.validation import ensure_email
from models.user import User
from models.project import Project
from models.task import Task

console = Console()

def _fmt_date(dt: str | None) -> str:
    return dt or "-"

def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="project-tracker",
        description="Project Tracker CLI: manage users, projects, and tasks",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # add-user
    p_add_user = sub.add_parser("add-user", help="Create a new user")
    p_add_user.add_argument("--name", required=True)
    p_add_user.add_argument("--email", required=True)

    # list-users
    sub.add_parser("list-users", help="List users")

    # add-project
    p_add_proj = sub.add_parser("add-project", help="Create a project for a user")
    p_add_proj.add_argument("--user", help="User name or email", required=True)
    p_add_proj.add_argument("--title", required=True)
    p_add_proj.add_argument("--description", default="")
    p_add_proj.add_argument("--due", help="Due date (e.g., 2025-09-30 or 'Oct 2')", default=None)

    # list-projects
    p_list_proj = sub.add_parser("list-projects", help="List projects (optionally by user)")
    p_list_proj.add_argument("--user", help="User name or email", default=None)
    p_list_proj.add_argument("--search", help="Search in title/description", default=None)

    # add-task
    p_add_task = sub.add_parser("add-task", help="Add a task to a project")
    p_add_task.add_argument("--project", help="Project title", required=True)
    p_add_task.add_argument("--title", required=True)
    p_add_task.add_argument("--assigned-to", help="User name or email", default=None)

    # list-tasks
    p_list_tasks = sub.add_parser("list-tasks", help="List tasks (optionally filtered)")
    p_list_tasks.add_argument("--project", default=None)
    p_list_tasks.add_argument("--status", choices=["todo", "doing", "done"], default=None)

    # complete-task
    p_complete = sub.add_parser("complete-task", help="Mark a task done")
    p_complete.add_argument("--task-id", type=int, required=True)

    # assign-task
    p_assign = sub.add_parser("assign-task", help="Assign/Change task owner")
    p_assign.add_argument("--task-id", type=int, required=True)
    p_assign.add_argument("--user", required=True)

    # add-contributor
    p_contrib = sub.add_parser("add-contributor", help="Add a contributor (many-to-many)")
    p_contrib.add_argument("--task-id", type=int, required=True)
    p_contrib.add_argument("--user", required=True)

    # edit-project
    p_edit_proj = sub.add_parser("edit-project", help="Edit project fields")
    p_edit_proj.add_argument("--project-id", type=int, required=True)
    p_edit_proj.add_argument("--title")
    p_edit_proj.add_argument("--description")
    p_edit_proj.add_argument("--due")

    # dump-data
    sub.add_parser("dump-data", help="Print raw JSON store for debugging")

    args = parser.parse_args(argv)

    db = DB()
    db.load()

    if args.cmd == "add-user":
        ensure_email(args.email)
        user = User.create(db, name=args.name, email=args.email)
        db.save()
        console.print(f"[green]Created user[/green] #{user.id}: {user.name} <{user.email}>")
        return 0

    if args.cmd == "list-users":
        table = Table("ID", "Name", "Email")
        for u in User.all(db):
            table.add_row(str(u.id), u.name, u.email)
        console.print(table)
        return 0

    if args.cmd == "add-project":
        user = User.find_by_identity(db, args.user)
        due = None
        if args.due:
            due = dateparser.parse(args.due).date().isoformat()
        proj = Project.create(db, title=args.title, description=args.description, due_date=due, owner_id=user.id)
        db.save()
        console.print(f"[green]Created project[/green] #{proj.id} for {user.name}: {proj.title} (due {_fmt_date(proj.due_date)})")
        return 0

    if args.cmd == "list-projects":
        owner = User.find_by_identity(db, args.user) if args.user else None
        rows = Project.all(db)
        if owner:
            rows = [p for p in rows if p.owner_id == owner.id]
        if args.search:
            q = args.search.lower()
            rows = [p for p in rows if q in p.title.lower() or q in (p.description or "").lower()]
        table = Table("ID", "Title", "Owner", "Due", "#Tasks")
        for p in rows:
            owner_name = User.get(db, p.owner_id).name if p.owner_id else "-"
            tcount = len(Task.for_project(db, p.id))
            table.add_row(str(p.id), p.title, owner_name, _fmt_date(p.due_date), str(tcount))
        console.print(table)
        return 0

    if args.cmd == "add-task":
        proj = Project.find_by_title(db, args.project)
        assigned_to_id = None
        if args.assigned_to:
            assigned_to_id = User.find_by_identity(db, args.assigned_to).id
        task = Task.create(db, title=args.title, project_id=proj.id, assigned_to=assigned_to_id)
        db.save()
        console.print(f"[green]Created task[/green] #{task.id} in project '{proj.title}'")
        return 0

    if args.cmd == "list-tasks":
        tasks = Task.all(db)
        if args.project:
            proj = Project.find_by_title(db, args.project)
            tasks = [t for t in tasks if t.project_id == proj.id]
        if args.status:
            tasks = [t for t in tasks if t.status == args.status]
        table = Table("ID", "Title", "Project", "Status", "Assigned", "Contributors")
        for t in tasks:
            proj = Project.get(db, t.project_id)
            assigned = User.get(db, t.assigned_to).name if t.assigned_to else "-"
            contribs = ", ".join(User.get(db, uid).name for uid in t.contributors) if t.contributors else "-"
            table.add_row(str(t.id), t.title, proj.title if proj else "-", t.status, assigned, contribs)
        console.print(table)
        return 0

    if args.cmd == "complete-task":
        task = Task.get(db, args.task_id)
        if not task:
            console.print(f"[red]Task {args.task_id} not found")
            return 1
        task.status = "done"
        db.update_task(task)
        db.save()
        console.print(f"[green]Completed task[/green] #{task.id}: {task.title}")
        return 0

    if args.cmd == "assign-task":
        task = Task.get(db, args.task_id)
        if not task:
            console.print(f"[red]Task {args.task_id} not found")
            return 1
        user = User.find_by_identity(db, args.user)
        task.assigned_to = user.id
        db.update_task(task)
        db.save()
        console.print(f"[green]Assigned task[/green] #{task.id} to {user.name}")
        return 0

    if args.cmd == "add-contributor":
        task = Task.get(db, args.task_id)
        if not task:
            console.print(f"[red]Task {args.task_id} not found")
            return 1
        user = User.find_by_identity(db, args.user)
        if user.id not in task.contributors:
            task.contributors.append(user.id)
        db.update_task(task)
        db.save()
        console.print(f"[green]Added contributor[/green] {user.name} to task #{task.id}")
        return 0

    if args.cmd == "edit-project":
        proj = Project.get(db, args.project_id)
        if not proj:
            console.print(f"[red]Project {args.project_id} not found")
            return 1
        if args.title:
            proj.title = args.title
        if args.description is not None:
            proj.description = args.description
        if args.due is not None:
            proj.due_date = dateparser.parse(args.due).date().isoformat() if args.due else None
        db.update_project(proj)
        db.save()
        console.print(f"[green]Updated project[/green] #{proj.id}")
        return 0

    if args.cmd == "dump-data":
        console.print_json(DB.read_raw())
        return 0

    return 0

if __name__ == "__main__":
    raise SystemExit(run())