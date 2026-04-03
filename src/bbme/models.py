from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class RepoStage(Enum):
    PENDING = "pending"
    CLONED = "cloned"
    BRANCHED = "branched"
    MODIFIED = "modified"
    COMMITTED = "committed"
    PUSHED = "pushed"
    PR_CREATED = "pr_created"
    FAILED = "failed"


@dataclass
class Config:
    workspace: str
    token: str
    username: str = ""
    base_url: str = "https://api.bitbucket.org/2.0"


@dataclass
class RepoInfo:
    workspace: str
    slug: str
    clone_url_https: str
    files_matched: list[str] = field(default_factory=list)


@dataclass
class RepoResult:
    repo: RepoInfo
    local_path: Path | None = None
    stage: RepoStage = RepoStage.PENDING
    main_branch: str = ""
    new_branch: str = ""
    files_changed: list[str] = field(default_factory=list)
    error: str | None = None
    pr_url: str | None = None
    pr_id: int | None = None


@dataclass
class PRResult:
    repo_slug: str
    pr_id: int
    url: str
    title: str


class BbmeError(Exception):
    pass


class ConfigError(BbmeError):
    pass


class BitbucketError(BbmeError):
    pass


class GitError(BbmeError):
    pass
