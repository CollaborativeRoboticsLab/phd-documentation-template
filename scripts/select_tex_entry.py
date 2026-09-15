#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Resolve a LaTeX entry file from a document directory."
    )
    parser.add_argument("--directory", required=True, help="Directory containing candidate .tex files")
    parser.add_argument("--entry", default="", help="Optional explicit entry filename")
    return parser.parse_args()


def list_tex_files(directory: Path) -> list[Path]:
    return sorted(path for path in directory.glob("*.tex") if path.is_file())


def has_documentclass(path: Path) -> bool:
    try:
        return "\\documentclass" in path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False


def candidate_entries(directory: Path) -> list[Path]:
    tex_files = list_tex_files(directory)
    root_docs = [path for path in tex_files if has_documentclass(path)]
    return root_docs or tex_files


def fail(message: str) -> "NoReturn":
    print(message, file=sys.stderr)
    raise SystemExit(1)


def prompt_select(options: list[Path]) -> Path:
    if not sys.stdin.isatty():
        names = ", ".join(path.name for path in options)
        fail(
            "multiple .tex entry files found; rerun with ENTRY=<filename>. "
            f"Available entries: {names}"
        )

    print("Select the LaTeX entry file by index:", file=sys.stderr)
    for index, path in enumerate(options, start=1):
        print(f"  {index}. {path.name}", file=sys.stderr)

    while True:
        choice = input("Enter selection index: ").strip()
        if not choice.isdigit():
            print("Please enter a numeric index.", file=sys.stderr)
            continue
        selected = int(choice)
        if 1 <= selected <= len(options):
            return options[selected - 1]
        print("Index out of range.", file=sys.stderr)


def confirm_single(option: Path) -> Path:
    if not sys.stdin.isatty():
        fail(
            f"single .tex entry found ({option.name}); rerun with ENTRY={option.name} to confirm the build target"
        )

    while True:
        answer = input(f"Build {option.name}? [y/n]: ").strip().lower()
        if answer in {"y", "yes"}:
            return option
        if answer in {"n", "no"}:
            fail("build cancelled")
        print("Please answer y or n.", file=sys.stderr)


def resolve_entry(directory: Path, entry: str) -> Path:
    if not directory.is_dir():
        fail(f"directory does not exist: {directory}")

    options = candidate_entries(directory)
    if not options:
        fail(f"no .tex files found in {directory}")

    if entry:
        explicit = directory / entry
        if explicit in options:
            return explicit
        names = ", ".join(path.name for path in options)
        fail(f"ENTRY {entry} is not a valid choice. Available entries: {names}")

    if len(options) == 1:
        return confirm_single(options[0])

    return prompt_select(options)


def main() -> None:
    args = parse_args()
    directory = Path(args.directory)
    selected = resolve_entry(directory, args.entry)
    print(selected.as_posix())


if __name__ == "__main__":
    main()