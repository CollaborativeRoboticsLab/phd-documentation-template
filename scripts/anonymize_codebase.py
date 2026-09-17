from __future__ import annotations

import os
import re
import sys
from pathlib import Path


ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
ORG = "Collaborative" + "RoboticsLab"
ORG_LOWER = ORG.lower()
ANON_OWNER = "anonymous"
TEXT_SUFFIXES = {
    ".bib",
    ".cfg",
    ".cmake",
    ".cpp",
    ".css",
    ".env",
    ".example",
    ".h",
    ".hpp",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".launch",
    ".md",
    ".msg",
    ".py",
    ".repo",
    ".rst",
    ".rviz",
    ".setup_assistant",
    ".sh",
    ".srv",
    ".svg",
    ".tex",
    ".txt",
    ".urdf",
    ".xacro",
    ".xml",
    ".yaml",
    ".yml",
}
SKIP_DIRS = {".git", "build", "install", "log", "__pycache__"}


def iter_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name == "anonymize_codebase.py":
            continue
        if path.name in {"Dockerfile", ".setup_assistant"} or path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None


def write_if_changed(path: Path, original: str, updated: str) -> bool:
    if updated == original:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def detect_repo_roots() -> dict[str, list[Path]]:
    repo_roots: dict[str, list[Path]] = {}
    src1 = ROOT / "src_1"
    if src1.exists():
        for child in sorted(src1.iterdir()):
            if child.is_dir():
                repo_roots.setdefault(child.name, []).append(child)
    src2 = ROOT / "src_2"
    if src2.exists() and (src2 / "README.md").exists() and (src2 / "anygrasp_ros").exists():
        repo_roots.setdefault("anygrasp_ros", []).append(src2)
    return repo_roots


REPO_ROOTS = detect_repo_roots()


def local_group(path: Path) -> str | None:
    try:
        rel = path.resolve().relative_to(ROOT)
    except ValueError:
        return None
    if not rel.parts:
        return None
    if rel.parts[0] in {"src_1", "src_2"}:
        return rel.parts[0]
    return None


def choose_repo_root(repo_name: str, source_file: Path) -> Path | None:
    candidates = REPO_ROOTS.get(repo_name)
    if not candidates:
        return None
    group = local_group(source_file)
    if group:
        for candidate in candidates:
            if local_group(candidate) == group:
                return candidate
    return candidates[0]


def to_relative_link(source_file: Path, target: Path) -> str:
    relative = os.path.relpath(target, source_file.parent)
    return relative.replace(os.sep, "/")


def anonymize_url(url: str) -> str:
    url = url.replace(f"github.com/{ORG}/", f"github.com/{ANON_OWNER}/")
    url = url.replace(f"github.com/{ORG_LOWER}/", f"github.com/{ANON_OWNER}/")
    url = url.replace(f"open.vscode.dev/{ORG}/", f"open.vscode.dev/{ANON_OWNER}/")
    url = url.replace(f"open.vscode.dev/{ORG_LOWER}/", f"open.vscode.dev/{ANON_OWNER}/")
    return url


def rewrite_markdown_links(text: str, path: Path) -> str:
    blob_or_tree = re.compile(
        rf"\((https://github\.com/{ORG}/([^/]+)/((?:blob|tree))/[^/]+/([^\)]+))\)"
    )
    repo_root_link = re.compile(
        rf"\((https://github\.com/{ORG}/([^/)#]+?)(?:\.git)?/?(?:#[^)]*)?)\)"
    )
    open_vscode_link = re.compile(
        rf"\((https://open\.vscode\.dev/(?:{ORG}|{ORG_LOWER})/([^/)#]+?))\)"
    )

    def replace_blob_or_tree(match: re.Match[str]) -> str:
        url, repo_name, _, subpath = match.groups()
        repo_root = choose_repo_root(repo_name, path)
        if repo_root is not None:
            target = repo_root / subpath
            if target.exists():
                return f"({to_relative_link(path, target)})"
        return f"({anonymize_url(url)})"

    def replace_repo_root(match: re.Match[str]) -> str:
        url, repo_name = match.groups()
        repo_root = choose_repo_root(repo_name, path)
        if repo_root is not None:
            return f"({to_relative_link(path, repo_root)})"
        return f"({anonymize_url(url)})"

    def replace_open_vscode(match: re.Match[str]) -> str:
        url, repo_name = match.groups()
        repo_root = choose_repo_root(repo_name, path)
        if repo_root is not None:
            return f"({to_relative_link(path, repo_root)})"
        return f"({anonymize_url(url)})"

    text = blob_or_tree.sub(replace_blob_or_tree, text)
    text = open_vscode_link.sub(replace_open_vscode, text)
    text = repo_root_link.sub(replace_repo_root, text)
    return text


def remove_citation_sections(text: str) -> str:
    pattern = re.compile(
        r"\n#{2,} Citation\s*\n.*?(?=\n#{2,}\s|\Z)",
        flags=re.DOTALL,
    )
    return pattern.sub("\n", text)


def collect_project_names() -> set[str]:
    names: set[str] = set()
    name_line = re.compile(r"^[A-Z][A-Za-z.'-]+(?: [A-Z][A-Za-z.'-]+)+$")
    for authors_path in ROOT.rglob("AUTHORS"):
        if "external" in authors_path.parts:
            continue
        content = read_text(authors_path)
        if content is None:
            continue
        for line in content.splitlines():
            candidate = line.strip()
            if name_line.fullmatch(candidate):
                names.add(candidate)

    for package_xml in ROOT.rglob("package.xml"):
        content = read_text(package_xml)
        if content is None:
            continue
        for match in re.finditer(r"<(?:author|maintainer)(?:\s+[^>]*)?>(.*?)</(?:author|maintainer)>", content):
            candidate = re.sub(r"\s+", " ", match.group(1)).strip()
            if candidate:
                names.add(candidate)

    for assistant_path in ROOT.rglob(".setup_assistant"):
        content = read_text(assistant_path)
        if content is None:
            continue
        for match in re.finditer(r"^\s*author_name:\s*(.+?)\s*$", content, flags=re.MULTILINE):
            candidate = match.group(1).strip()
            if candidate:
                names.add(candidate)

    return names


def sanitize_package_xml(text: str) -> str:
    text = re.sub(r"\n\s*<author(?:\s+[^>]*)?>.*?</author>", "", text, flags=re.DOTALL)
    text = re.sub(r"\n\s*<maintainer(?:\s+[^>]*)?>.*?</maintainer>", "", text, flags=re.DOTALL)
    return text


def sanitize_setup_assistant(text: str) -> str:
    return re.sub(r"^(\s*author_name:\s*).*$", r"\1Anonymous", text, flags=re.MULTILINE)


def sanitize_text_file(path: Path, names: set[str]) -> bool:
    original = read_text(path)
    if original is None:
        return False

    updated = original
    if path.suffix.lower() == ".md" or path.name.endswith(".md"):
        updated = rewrite_markdown_links(updated, path)
        updated = remove_citation_sections(updated)

    if path.name == "package.xml":
        updated = sanitize_package_xml(updated)

    if path.name == ".setup_assistant":
        updated = sanitize_setup_assistant(updated)

    updated = updated.replace(f"https://github.com/{ORG}/", f"https://github.com/{ANON_OWNER}/")
    updated = updated.replace(f"https://github.com/{ORG_LOWER}/", f"https://github.com/{ANON_OWNER}/")
    updated = updated.replace(f"https://open.vscode.dev/{ORG}/", f"https://open.vscode.dev/{ANON_OWNER}/")
    updated = updated.replace(f"https://open.vscode.dev/{ORG_LOWER}/", f"https://open.vscode.dev/{ANON_OWNER}/")
    updated = updated.replace(f"{ORG}/", "")
    updated = updated.replace(f"{ORG_LOWER}/", "")
    updated = updated.replace(ORG, "")
    updated = updated.replace(ORG_LOWER, "")

    for name in sorted(names, key=len, reverse=True):
        updated = re.sub(re.escape(name), "Anonymous", updated)

    return write_if_changed(path, original, updated)


def remove_authors_files() -> int:
    removed = 0
    for authors_path in ROOT.rglob("AUTHORS"):
        authors_path.unlink()
        removed += 1
    return removed


def main() -> None:
    names = collect_project_names()
    changed_files = 0
    for path in iter_files(ROOT):
        if sanitize_text_file(path, names):
            changed_files += 1
    removed_authors = remove_authors_files()
    print(f"updated_files={changed_files}")
    print(f"removed_authors={removed_authors}")
    print(f"tracked_names={len(names)}")


if __name__ == "__main__":
    main()