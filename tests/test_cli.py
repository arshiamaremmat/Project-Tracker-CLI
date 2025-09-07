import json
from utils.storage import DB, STORE
from main import run


def setup_function(_):
    if STORE.exists():
        STORE.unlink()


def _run(argv: list[str]) -> int:
    return run(argv)


def test_cli_end_to_end(capsys):
    assert _run(["add-user", "--name", "Alex", "--email", "alex@example.com"]) == 0
    assert _run(["add-project", "--user", "Alex", "--title", "CLI Tool"]) == 0
    assert _run(["add-task", "--project", "CLI Tool", "--title", "Implement add-task", "--assigned-to", "alex@example.com"]) == 0
    assert _run(["list-projects"]) == 0
    out = capsys.readouterr().out
    assert "CLI Tool" in out

    # complete task
    assert _run(["complete-task", "--task-id", "1"]) == 0
    assert _run(["list-tasks"]) == 0
    out2 = capsys.readouterr().out
    assert "done" in out2