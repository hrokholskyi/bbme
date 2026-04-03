# bbme — Bitbucket Mass Editor

A CLI tool for find-and-replace across multiple Bitbucket Cloud repositories. Search for a string across your workspace, pick which repos to update, and bbme will clone them, make the changes, push new branches, and open PRs — all in one interactive session.

## Installation

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

Optionally, install `bbme` as a global command so you can run it from anywhere:

```bash
uv tool install .
```

## Configuration

Copy the example config and fill in your Bitbucket credentials:

```bash
cp bbme.toml.example bbme.toml
```

**`bbme.toml`**

```toml
[bitbucket]
workspace = "your-workspace"

# App password (most common) — set both username and token
username = "your-bitbucket-username"
token = "your-app-password"

# OAuth / workspace access token — set only token, remove username
# token = "your-oauth-or-workspace-token"
```

You can also place this file at `~/.config/bbme/bbme.toml` to keep it out of your project directory.

> **Note:** Git clone and push use HTTPS, so make sure your git credential helper is configured for Bitbucket (or that your app password is stored in your system keychain).

## Usage

```bash
uv run bbme
```

The tool walks you through each step interactively:

1. Enter a search string and its replacement
2. bbme searches the Bitbucket code search API across your workspace
3. Select which repositories to update
4. Choose the base branch and a new branch name
5. Write a commit message
6. Review changes, push, and optionally create pull requests

All cloned repos are placed in a local `workspace/` directory.

For a detailed walkthrough with sample TUI output for every step, see [FLOW.md](FLOW.md).

## How it works

```
Search Bitbucket API → Select repos → Clone → Branch → Find & replace → Commit → Push → Create PRs
```

- Exact string matching (not regex) across all text files in each repo
- Binary files are automatically skipped
- Each repo is tracked independently — if one fails, the rest continue
- A summary table is printed at the end showing the status of every repo

## Creating an app password

1. Go to **Bitbucket → Personal settings → App passwords**
2. Click **Create app password**
3. Grant these permissions:
   - **Repositories**: Read, Write
   - **Pull requests**: Read, Write
4. Copy the generated password into `bbme.toml`
