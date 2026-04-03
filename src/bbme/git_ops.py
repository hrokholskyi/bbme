import subprocess
from pathlib import Path

from bbme.models import GitError


def _run(args: list[str], cwd: Path | None = None) -> str:
    try:
        result = subprocess.run(
            args,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise GitError(e.stderr.strip() or e.stdout.strip() or str(e)) from e


def clone_repo(clone_url: str, target_dir: Path) -> None:
    _run(["git", "clone", clone_url, str(target_dir)])


def checkout_branch(repo_dir: Path, branch_name: str) -> None:
    _run(["git", "checkout", branch_name], cwd=repo_dir)


def create_branch(repo_dir: Path, branch_name: str) -> None:
    _run(["git", "checkout", "-b", branch_name], cwd=repo_dir)


def get_current_branch(repo_dir: Path) -> str:
    return _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_dir)


def stage_file(repo_dir: Path, file_path: str) -> None:
    _run(["git", "add", file_path], cwd=repo_dir)


def commit(repo_dir: Path, message: str) -> bool:
    try:
        _run(["git", "commit", "-m", message], cwd=repo_dir)
        return True
    except GitError as e:
        if "nothing to commit" in str(e):
            return False
        raise


def push(repo_dir: Path, branch_name: str) -> None:
    _run(["git", "push", "-u", "origin", branch_name], cwd=repo_dir)


def has_changes(repo_dir: Path) -> bool:
    output = _run(["git", "status", "--porcelain"], cwd=repo_dir)
    return bool(output)


def get_changed_files(repo_dir: Path) -> list[str]:
    output = _run(["git", "diff", "--name-only"], cwd=repo_dir)
    if not output:
        return []
    return output.splitlines()
