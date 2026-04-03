from __future__ import annotations

from typing import TYPE_CHECKING

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

if TYPE_CHECKING:
    from bbme.models import RepoInfo, RepoResult, RepoStage

console = Console()


def display_search_results(repos: list[RepoInfo]) -> None:
    table = Table(title="Repositories with matches")
    table.add_column("#", style="dim", width=4)
    table.add_column("Repository", style="cyan")
    table.add_column("Files matched", style="green", justify="right")

    for i, repo in enumerate(repos, 1):
        table.add_row(str(i), f"{repo.workspace}/{repo.slug}", str(len(repo.files_matched)))

    console.print(table)


def display_branches(branches: list[str]) -> None:
    branch_list = "\n".join(f"  - {b}" for b in branches)
    console.print(Panel(branch_list, title="Available branches", border_style="blue"))


def display_summary(results: list[RepoResult]) -> None:
    from bbme.models import RepoStage

    table = Table(title="Summary Report", show_lines=True)
    table.add_column("Repository", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Files changed")
    table.add_column("PR link")

    total_prs = 0
    total_failed = 0

    for r in results:
        if r.stage == RepoStage.FAILED:
            status = f"[red]FAILED: {r.error}[/red]"
            total_failed += 1
        elif r.stage == RepoStage.PR_CREATED:
            status = "[green]PR created[/green]"
            total_prs += 1
        elif r.stage == RepoStage.PUSHED:
            status = "[yellow]Pushed (no PR)[/yellow]"
        elif r.stage == RepoStage.COMMITTED:
            status = "[yellow]Committed (not pushed)[/yellow]"
        else:
            status = f"[dim]{r.stage.value}[/dim]"

        files = "\n".join(r.files_changed) if r.files_changed else "-"
        pr_link = r.pr_url or "-"
        table.add_row(r.repo.slug, status, files, pr_link)

    console.print(table)
    console.print(
        Panel(
            f"Total repos: {len(results)}  |  PRs created: {total_prs}  |  Failed: {total_failed}",
            border_style="green" if total_failed == 0 else "yellow",
        )
    )


def prompt_text(message: str, default: str = "") -> str:
    result = questionary.text(message, default=default).ask()
    if result is None:
        raise KeyboardInterrupt
    return result


def prompt_confirm(message: str, default: bool = True) -> bool:
    result = questionary.confirm(message, default=default).ask()
    if result is None:
        raise KeyboardInterrupt
    return result


def prompt_select(message: str, choices: list[str]) -> str:
    result = questionary.select(message, choices=choices).ask()
    if result is None:
        raise KeyboardInterrupt
    return result


def prompt_checkbox(message: str, choices: list[str]) -> list[str]:
    result = questionary.checkbox(message, choices=choices).ask()
    if result is None:
        raise KeyboardInterrupt
    return result


def select_repos(repos: list[RepoInfo]) -> list[RepoInfo]:
    all_label = f"(All {len(repos)} repos)"
    repo_labels = [f"{r.workspace}/{r.slug} ({len(r.files_matched)} files)" for r in repos]
    choices = [all_label] + repo_labels
    selected = prompt_checkbox(
        "Select repos to process (space to toggle, enter to confirm):",
        choices=choices,
    )
    if not selected:
        return []
    if all_label in selected:
        return list(repos)
    selected_set = set(selected)
    return [r for r, label in zip(repos, repo_labels) if label in selected_set]


def show_error(message: str) -> None:
    console.print(Panel(message, title="Error", border_style="red"))


def show_success(message: str) -> None:
    console.print(Panel(message, title="Success", border_style="green"))


def show_progress() -> Progress:
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        console=console,
    )
