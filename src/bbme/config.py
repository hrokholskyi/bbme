import tomllib
from pathlib import Path

from bbme.models import Config, ConfigError

CONFIG_FILENAME = "bbme.toml"
XDG_CONFIG_PATH = Path.home() / ".config" / "bbme" / CONFIG_FILENAME


def _find_config_file() -> Path:
    local = Path(CONFIG_FILENAME)
    if local.exists():
        return local
    if XDG_CONFIG_PATH.exists():
        return XDG_CONFIG_PATH
    raise ConfigError(
        f"Config file not found. Create {CONFIG_FILENAME} in the current directory "
        f"or at {XDG_CONFIG_PATH}.\n"
        f"See bbme.toml.example for the required format."
    )


def load_config() -> Config:
    path = _find_config_file()
    with open(path, "rb") as f:
        data = tomllib.load(f)

    bb = data.get("bitbucket", {})
    workspace = bb.get("workspace", "").strip()
    token = bb.get("token", "").strip()

    if not workspace:
        raise ConfigError(f"Missing 'bitbucket.workspace' in {path}")
    if not token:
        raise ConfigError(f"Missing 'bitbucket.token' in {path}")

    return Config(
        workspace=workspace,
        token=token,
        username=bb.get("username", "").strip(),
        base_url=bb.get("base_url", "https://api.bitbucket.org/2.0").strip(),
    )
