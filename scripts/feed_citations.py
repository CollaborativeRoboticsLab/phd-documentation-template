#!/usr/bin/env python3
"""
Feed resolved citations from thesis/resolved_cite.txt into a target .bib file.

This stage removes successfully processed entries from the resolved file, so the
file acts as a queue between verification and bibliography ingestion.

USAGE:
    python feed_citations.py thesis/resolved_cite.txt --bib thesis/latex/Bibliography.bib
"""

import argparse
import builtins
import re
import sys
from collections import OrderedDict
from pathlib import Path


ROOT = Path(__file__).parent.parent
DEFAULT_RESOLVED = ROOT / "thesis/resolved_cite.txt"
DEFAULT_BIB = ROOT / "thesis/latex/Bibliography.bib"
REPO_BIB_PATTERNS = (
    "thesis/latex/Bibliography.bib",
    "papers/*/references.bib",
)


def spaced_print(*args, **kwargs):
    kwargs.setdefault("end", "\n\n")
    builtins.print(*args, **kwargs)


print = spaced_print


def normalize(text: str) -> str:
    text = re.sub(r"[^a-z0-9 ]", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def split_bib_entries(text: str) -> list[dict]:
    entries = []
    i = 0
    n = len(text)
    header_re = re.compile(r"@(\w+)\s*\{")
    while True:
        match = header_re.search(text, i)
        if not match:
            break
        brace_start = match.end() - 1
        depth = 0
        j = brace_start
        while j < n:
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        if j >= n:
            break
        raw = text[match.start():j + 1]
        key, fields = parse_entry_fields(raw)
        entries.append({"key": key, "fields": fields, "raw": raw})
        i = j + 1
    return entries


def parse_entry_fields(raw: str) -> tuple[str, dict]:
    inner = raw[raw.index("{") + 1: raw.rindex("}")]
    key, _, rest = inner.partition(",")
    key = key.strip()

    parts = []
    depth = 0
    buf = ""
    for ch in rest:
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(buf)
            buf = ""
        else:
            buf += ch
    if buf.strip():
        parts.append(buf)

    fields = {}
    for part in parts:
        if "=" not in part:
            continue
        fname, _, fval = part.partition("=")
        fname = fname.strip().lower()
        fval = fval.strip()
        if fval.startswith("{") and fval.endswith("}"):
            fval = fval[1:-1]
        elif fval.startswith('"') and fval.endswith('"'):
            fval = fval[1:-1]
        fields[fname] = fval.strip()
    return key, fields


def parse_resolved_sections(path: Path) -> OrderedDict[str, list[dict]]:
    if not path.exists():
        print(f"error: {path} does not exist")
        sys.exit(1)

    sections: OrderedDict[str, list[dict]] = OrderedDict()
    current_section = None
    current_entry = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("# "):
            continue
        if stripped.startswith("## "):
            current_section = stripped[3:].strip()
            sections.setdefault(current_section, [])
            current_entry = None
            continue
        if current_section is None:
            continue
        if line.startswith("    "):
            if current_entry is None or ":" not in stripped:
                continue
            field_name, _, field_value = stripped.partition(":")
            current_entry[field_name.strip()] = field_value.strip()
            continue

        current_entry = {"raw_ref": stripped}
        sections[current_section].append(current_entry)

    return sections


def format_resolved_sections(sections: OrderedDict[str, list[dict]]) -> str:
    lines = ["# Resolved Citations", ""]
    for section, refs in sections.items():
        lines.append(f"## {section}")
        for ref in refs:
            lines.append(ref["raw_ref"])
            for field in ("status", "title", "cite", "note"):
                if ref.get(field):
                    lines.append(f"    {field}: {ref[field]}")
            lines.append("")
        if not refs:
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def iter_repo_bib_entries() -> list[dict]:
    entries: list[dict] = []
    seen_paths: set[Path] = set()
    for pattern in REPO_BIB_PATTERNS:
        for bib_path in sorted(ROOT.glob(pattern)):
            if bib_path in seen_paths or not bib_path.exists():
                continue
            seen_paths.add(bib_path)
            for entry in split_bib_entries(bib_path.read_text(encoding="utf-8")):
                title = entry["fields"].get("title", "").strip()
                entries.append({
                    "path": bib_path,
                    "key": entry["key"],
                    "raw": entry["raw"],
                    "title": title,
                    "norm_title": normalize(title) if title else "",
                })
    return entries


def parse_cite_key(cite_text: str) -> str | None:
    match = re.fullmatch(r"\\cite\{([^}]+)\}", cite_text.strip())
    if not match:
        return None
    return match.group(1).strip()


def build_target_bib_indexes(bib_path: Path) -> tuple[set[str], set[str]]:
    existing_keys: set[str] = set()
    existing_titles: set[str] = set()
    if not bib_path.exists():
        return existing_keys, existing_titles
    for entry in split_bib_entries(bib_path.read_text(encoding="utf-8")):
        existing_keys.add(entry["key"])
        title = entry["fields"].get("title", "").strip()
        if title:
            existing_titles.add(normalize(title))
    return existing_keys, existing_titles


def find_repo_entry(cite_key: str, title: str, repo_entries: list[dict]) -> dict | None:
    for entry in repo_entries:
        if entry["key"] == cite_key:
            return entry

    normalized_title = normalize(title)
    matches = [entry for entry in repo_entries if entry["norm_title"] == normalized_title]
    if len(matches) == 1:
        return matches[0]
    return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("resolved", type=Path, nargs="?", default=DEFAULT_RESOLVED,
                        help=f"Resolved citation queue file (default: {DEFAULT_RESOLVED})")
    parser.add_argument("--bib", type=Path, default=DEFAULT_BIB,
                        help=f"Target bibliography to feed (default: {DEFAULT_BIB})")
    parser.add_argument("--dry-run", action="store_true",
                        help="Report what would change without writing files")
    return parser


def main():
    args = build_parser().parse_args()

    sections = parse_resolved_sections(args.resolved)
    repo_entries = iter_repo_bib_entries()
    existing_keys, existing_titles = build_target_bib_indexes(args.bib)

    remaining_sections: OrderedDict[str, list[dict]] = OrderedDict()
    appended_entries: list[str] = []
    processed_count = 0
    skipped_count = 0

    for section, refs in sections.items():
        remaining_sections[section] = []
        for ref in refs:
            cite_key = parse_cite_key(ref.get("cite", ""))
            title = ref.get("title", "")
            if not cite_key or not title:
                print(f"[{section}] keeping unresolved resolved-entry record for {ref.get('raw_ref', '(unknown)')}: missing cite/title metadata")
                remaining_sections[section].append(ref)
                continue

            repo_entry = find_repo_entry(cite_key, title, repo_entries)
            if repo_entry is None:
                print(f"[{section}] keeping {ref['raw_ref']}: could not find BibTeX for key {cite_key}")
                remaining_sections[section].append(ref)
                continue

            if cite_key in existing_keys or repo_entry["norm_title"] in existing_titles:
                print(f"[{section}] processed existing entry {cite_key}")
                processed_count += 1
                skipped_count += 1
                continue

            print(f"[{section}] append {cite_key} to {args.bib}")
            appended_entries.append(repo_entry["raw"])
            existing_keys.add(cite_key)
            if repo_entry["norm_title"]:
                existing_titles.add(repo_entry["norm_title"])
            processed_count += 1

    if args.dry_run:
        print(f"[dry-run] would append {len(appended_entries)} entries -> {args.bib}")
        print(f"[dry-run] would remove {processed_count} processed entries from {args.resolved}")
        print(f"[dry-run] {len([ref for refs in remaining_sections.values() for ref in refs])} entries would remain queued")
        return

    if appended_entries:
        existing_size = args.bib.stat().st_size if args.bib.exists() else 0
        with open(args.bib, "a", encoding="utf-8") as handle:
            if existing_size > 0:
                handle.write("\n\n")
            handle.write("\n\n".join(appended_entries))

    args.resolved.write_text(format_resolved_sections(remaining_sections), encoding="utf-8")

    print(f"Appended {len(appended_entries)} entries -> {args.bib}")
    print(f"Removed {processed_count} processed entries from {args.resolved}")
    print(f"{len([ref for refs in remaining_sections.values() for ref in refs])} entries remain queued")
    if skipped_count:
        print(f"{skipped_count} processed entries were already present in the target bibliography")


if __name__ == "__main__":
    main()