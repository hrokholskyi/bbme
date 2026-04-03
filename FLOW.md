# FLOW.md — Interactive Workflow

This document walks through each step of a bbme session with sample TUI output.

---

## Step 1: Launch

```
╭───────────────────────────────────────────────╮
│       bbme — Bitbucket Mass Editor            │
│  Mass find-and-replace across Bitbucket repos │
╰───────────────────────────────────────────────╯
```

Config is loaded from `bbme.toml` (local directory or `~/.config/bbme/bbme.toml`).
If the file is missing or incomplete, an error panel is shown and the tool exits.

---

## Step 2: Enter search and replacement strings

```
? Search string (exact match): cdn.old-domain.com
? Replacement string: cdn.new-domain.com

Searching for 'cdn.old-domain.com' in workspace example_workspace...
```

These are exact string matches — not regex. Every text file in each repo is checked.

---

## Step 3: Review search results

bbme queries the Bitbucket code search API and displays matching repos:

```
                Repositories with matches
┏━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ #  ┃ Repository                            ┃ Files matched ┃
┡━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│  1 │ example_workspace/web-frontend        │             8 │
│  2 │ example_workspace/api-gateway         │             3 │
│  3 │ example_workspace/mobile-app          │             5 │
│  4 │ example_workspace/docs-site           │             2 │
└────┴──────────────────────────────────────┴───────────────┘
```

---

## Step 4: Select repositories

Use space to toggle, enter to confirm:

```
? Select repos to process (space to toggle, enter to confirm):
 ❯ ◉ (All 4 repos)
   ◉ example_workspace/web-frontend (8 files)
   ◉ example_workspace/api-gateway (3 files)
   ◯ example_workspace/mobile-app (5 files)
   ◉ example_workspace/docs-site (2 files)
```

```
3 repo(s) selected.
? Proceed? (Y/n): Y
```

---

## Step 5: Prepare workspace

If a `workspace/` directory already exists from a previous run:

```
? workspace/ already exists. Delete and recreate? (Y/n): Y
```

A fresh `workspace/` directory is created for cloning.

---

## Step 6: Clone repositories

```
⠸ Cloning repos...  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 3/3  0:00:12
```

Each repo is cloned into `workspace/<slug>/`. If a clone fails, that repo is marked as failed and the rest continue.

---

## Step 7: Checkout main branch

```
? Main branch name: (main) main
```

If a repo doesn't have the specified branch, bbme fetches the branch list and lets you pick:

```
Branch 'main' not found in api-gateway
╭──────── Available branches ────────╮
│   - master                         │
│   - develop                        │
│   - release/v2                     │
╰────────────────────────────────────╯
? Pick branch for api-gateway:
 ❯ master
   develop
   release/v2
```

---

## Step 8: Create a new branch

```
? New branch name (e.g., fix/PROJ-1234-description): fix/PROJ-1234-update-cdn-domain
```

A new branch is created from the base branch in every active repo.

---

## Step 9: Enter commit message

```
? Commit message: fix: update CDN domain to cdn.new-domain.com
```

---

## Step 10: Find and replace

```
Replacing 'cdn.old-domain.com' with 'cdn.new-domain.com'...
  web-frontend: 8 file(s) changed
  api-gateway: 3 file(s) changed
  docs-site: 2 file(s) changed
```

Files are modified in-place within the cloned repos. Binary files and `.git` directories are skipped.

---

## Step 11: Commit changes

Changes are staged and committed per-repo using the commit message from step 9.

```
3 repo(s) committed successfully.
```

---

## Step 12: Push

```
? Push 3 repo(s) to remote? (Y/n): Y

⠼ Pushing...  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 3/3  0:00:06
```

Each repo is pushed to `origin/<new-branch>`.

---

## Step 13: Create pull requests

```
? Create PRs for 3 repo(s)? (Y/n): Y
  PR created: https://bitbucket.org/example_workspace/web-frontend/pull-requests/142
  PR created: https://bitbucket.org/example_workspace/api-gateway/pull-requests/87
  PR created: https://bitbucket.org/example_workspace/docs-site/pull-requests/31
```

PRs are created via the Bitbucket API with the commit message as the title, targeting the base branch.

---

## Step 14: Summary

```
                                    Summary Report
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Repository      ┃ Status     ┃ Files changed      ┃ PR link                                                     ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ web-frontend    │ PR created │ src/config.ts      │ .../example_workspace/web-frontend/pull-requests/142        │
│                 │            │ src/utils/cdn.ts   │                                                             │
│                 │            │ public/index.html  │                                                             │
│                 │            │ ...5 more          │                                                             │
├────────────────┼────────────┼────────────────────┼─────────────────────────────────────────────────────────────┤
│ api-gateway     │ PR created │ config/default.yml │ .../example_workspace/api-gateway/pull-requests/87          │
│                 │            │ src/middleware.go   │                                                             │
│                 │            │ README.md          │                                                             │
├────────────────┼────────────┼────────────────────┼─────────────────────────────────────────────────────────────┤
│ docs-site       │ PR created │ docs/setup.md      │ .../example_workspace/docs-site/pull-requests/31            │
│                 │            │ mkdocs.yml         │                                                             │
└────────────────┴────────────┴────────────────────┴─────────────────────────────────────────────────────────────┘
╭─────────────────────────────────────────────────────╮
│ Total repos: 3  |  PRs created: 3  |  Failed: 0    │
╰─────────────────────────────────────────────────────╯
╭──────── Success ────────╮
│ Done!                   │
╰─────────────────────────╯
```

---

## Error handling

If any repo fails at any step, it's marked as `FAILED` and excluded from subsequent steps. The summary table shows what went wrong:

```
│ mobile-app  │ FAILED: Clone failed: repository access denied │ -  │ -  │
```

The workflow continues with the remaining repos. You can Ctrl+C at any prompt to abort.
