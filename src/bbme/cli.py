import shutil
import sys
from pathlib import Path

from rich.markup import escape
from rich.panel import Panel

from bbme.bitbucket import BitbucketClient
from bbme.config import load_config
from bbme.git_ops import (
    checkout_branch,
    clone_repo,
    commit,
    create_branch,
    push,
    stage_file,
)
from bbme.models import (
    BitbucketError,
    ConfigError,
    GitError,
    RepoResult,
    RepoStage,
)
from bbme.replacer import find_and_replace_in_repo
from bbme.ui import (
    console,
    display_branches,
    display_search_results,
    display_summary,
    prompt_confirm,
    prompt_select,
    prompt_text,
    select_repos,
    show_error,
    show_progress,
    show_success,
)

WORKSPACE_DIR = Path("workspace")


def _active(results: list[RepoResult]) -> list[RepoResult]:
    return [r for r in results if r.stage != RepoStage.FAILED]


def main() -> None:
    console.print(Panel("[bold]bbme — Bitbucket Mass Editor[/bold]\nMass find-and-replace across Bitbucket repos", border_style="blue"))

    # Step 1: Load config
    try:
        config = load_config()
    except ConfigError as e:
        show_error(str(e))
        sys.exit(1)

    client = BitbucketClient(config)

    try:
        _run_workflow(client, config)
    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted. Exiting.[/dim]")
        sys.exit(130)
    finally:
        client.close()


def _run_workflow(client: BitbucketClient, config) -> None:
    # Step 2: Prompt for search and replacement strings
    search_string = prompt_text("Search string (exact match):")
    replacement = prompt_text("Replacement string:")

    console.print(f"\nSearching for [cyan]'{escape(search_string)}'[/cyan] in workspace [cyan]{escape(config.workspace)}[/cyan]...")

    # Step 3: Search Bitbucket
    try:
        repos = client.search_code(search_string)
    except BitbucketError as e:
        show_error(f"Search failed: {e}")
        return

    if not repos:
        show_error("No repositories found matching the search string.")
        return

    # Step 4: Display results and select repos
    display_search_results(repos)
    repos = select_repos(repos)
    if not repos:
        show_error("No repos selected.")
        return
    console.print(f"\n[green]{len(repos)} repo(s) selected.[/green]")
    if not prompt_confirm("Proceed?"):
        return

    # Step 5: Prepare workspace
    if WORKSPACE_DIR.exists():
        if prompt_confirm("workspace/ already exists. Delete and recreate?"):
            shutil.rmtree(WORKSPACE_DIR)
        else:
            show_error("Cannot proceed with existing workspace. Exiting.")
            return
    WORKSPACE_DIR.mkdir(parents=True)

    # Initialize tracking
    results: list[RepoResult] = [RepoResult(repo=r) for r in repos]

    # Step 6: Clone repos
    console.print()
    with show_progress() as progress:
        task = progress.add_task("Cloning repos...", total=len(results))
        for r in results:
            try:
                target = WORKSPACE_DIR / r.repo.slug
                clone_repo(r.repo.clone_url_https, target)
                r.local_path = target
                r.stage = RepoStage.CLONED
            except GitError as e:
                r.stage = RepoStage.FAILED
                r.error = f"Clone failed: {e}"
                show_error(f"Failed to clone {r.repo.slug}: {e}")
            progress.advance(task)

    if not _active(results):
        show_error("All clones failed.")
        display_summary(results)
        return

    # Step 7: Checkout main branch
    main_branch = prompt_text("Main branch name:", default="main")
    for r in _active(results):
        try:
            checkout_branch(r.local_path, main_branch)
            r.main_branch = main_branch
        except GitError:
            console.print(f"[yellow]Branch '{main_branch}' not found in {r.repo.slug}[/yellow]")
            try:
                branches = client.list_branches(r.repo.slug)
                if not branches:
                    r.stage = RepoStage.FAILED
                    r.error = "No branches available"
                    continue
                display_branches(branches)
                chosen = prompt_select(f"Pick branch for {r.repo.slug}:", branches)
                checkout_branch(r.local_path, chosen)
                r.main_branch = chosen
            except (BitbucketError, GitError) as e:
                r.stage = RepoStage.FAILED
                r.error = f"Branch checkout failed: {e}"

    if not _active(results):
        show_error("All branch checkouts failed.")
        display_summary(results)
        return

    # Step 8: Create new branch
    new_branch = prompt_text("New branch name (e.g., fix/AA-3399-description):")
    for r in _active(results):
        try:
            create_branch(r.local_path, new_branch)
            r.new_branch = new_branch
            r.stage = RepoStage.BRANCHED
        except GitError as e:
            r.stage = RepoStage.FAILED
            r.error = f"Branch creation failed: {e}"

    if not _active(results):
        show_error("All branch creations failed.")
        display_summary(results)
        return

    # Step 9: Commit message
    commit_message = prompt_text("Commit message:")

    # Step 10: Find & Replace
    console.print(f"\nReplacing [cyan]'{escape(search_string)}'[/cyan] with [green]'{escape(replacement)}'[/green]...")
    for r in _active(results):
        changed = find_and_replace_in_repo(r.local_path, search_string, replacement)
        r.files_changed = changed
        if changed:
            r.stage = RepoStage.MODIFIED
            console.print(f"  [green]{r.repo.slug}[/green]: {len(changed)} file(s) changed")
        else:
            console.print(f"  [dim]{r.repo.slug}: no changes[/dim]")

    # Step 11: Commit per repo
    for r in _active(results):
        if not r.files_changed:
            continue
        try:
            for f in r.files_changed:
                stage_file(r.local_path, f)
            if commit(r.local_path, commit_message):
                r.stage = RepoStage.COMMITTED
        except GitError as e:
            r.stage = RepoStage.FAILED
            r.error = f"Commit failed: {e}"

    committed = [r for r in results if r.stage == RepoStage.COMMITTED]
    if not committed:
        show_error("No repos had changes to commit.")
        display_summary(results)
        return

    console.print(f"\n[green]{len(committed)} repo(s) committed successfully.[/green]")

    # Step 12-13: Push
    if not prompt_confirm(f"Push {len(committed)} repo(s) to remote?"):
        display_summary(results)
        return

    with show_progress() as progress:
        task = progress.add_task("Pushing...", total=len(committed))
        for r in committed:
            try:
                push(r.local_path, r.new_branch)
                r.stage = RepoStage.PUSHED
            except GitError as e:
                r.stage = RepoStage.FAILED
                r.error = f"Push failed: {e}"
            progress.advance(task)

    # Step 14-15: Create PRs
    pushed = [r for r in results if r.stage == RepoStage.PUSHED]
    if pushed:
        console.print()
        if prompt_confirm(f"Create PRs for {len(pushed)} repo(s)?"):
            for r in pushed:
                try:
                    pr = client.create_pull_request(
                        r.repo.slug, commit_message, r.new_branch, r.main_branch
                    )
                    r.pr_url = pr.url
                    r.pr_id = pr.pr_id
                    r.stage = RepoStage.PR_CREATED
                    console.print(f"  [green]PR created:[/green] {pr.url}")
                except BitbucketError as e:
                    r.stage = RepoStage.FAILED
                    r.error = f"PR creation failed: {e}"
                    show_error(f"PR failed for {r.repo.slug}: {e}")

    # Step 16: Summary
    console.print()
    display_summary(results)
    show_success("Done!")
