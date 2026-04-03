from pathlib import Path

BINARY_EXTENSIONS = frozenset({
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg",
    ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".exe", ".bin", ".so", ".dll", ".dylib",
    ".woff", ".woff2", ".ttf", ".eot",
    ".mp3", ".mp4", ".avi", ".mov", ".wav",
    ".pyc", ".class", ".o",
})


def find_and_replace_in_repo(
    repo_dir: Path, search_string: str, replacement: str
) -> list[str]:
    changed_files: list[str] = []

    for file_path in repo_dir.rglob("*"):
        if not file_path.is_file():
            continue

        # Skip .git directories (including submodules)
        if ".git" in file_path.relative_to(repo_dir).parts:
            continue

        # Skip binary extensions
        if file_path.suffix.lower() in BINARY_EXTENSIONS:
            continue

        # Try reading as text
        try:
            content = file_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue

        if search_string not in content:
            continue

        new_content = content.replace(search_string, replacement)
        file_path.write_text(new_content, encoding="utf-8")

        relative = str(file_path.relative_to(repo_dir))
        changed_files.append(relative)

    return changed_files
