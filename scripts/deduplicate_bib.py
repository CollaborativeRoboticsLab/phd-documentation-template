#!/usr/bin/env python3
"""
References accumulated across many separate AI-tool sessions tend to
duplicate: the same paper pulled in twice under two different citation
keys. This finds likely duplicates and merges them for the thesis
bibliography in this workspace.
"""

import argparse
import re
import difflib
from collections import defaultdict
from pathlib import Path

ENTRY_RE = re.compile(r"@(\w+)\{([^,]+),(.*?)\n\}", re.DOTALL)
FIELD_RE = re.compile(r"(\w+)\s*=\s*\{(.*?)\}\s*,?\s*$", re.MULTILINE)

TITLE_MATCH_THRESHOLD = 0.90  # entries above this are flagged as likely dupes
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BIB_PATH = ROOT / "thesis/latex/Bibliography.bib"


def normalize(text: str) -> str:
    text = re.sub(r"[^a-z0-9 ]", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def parse_bib(path: str | Path):
    with open(path, encoding="utf-8") as f:
        content = f.read()

    entries = []
    for m in ENTRY_RE.finditer(content):
        entry_type, key, body = m.groups()
        fields = {}
        for fm in FIELD_RE.finditer(body):
            fields[fm.group(1).lower()] = fm.group(2).strip()
        entries.append(
            {"type": entry_type, "key": key.strip(), "fields": fields})
    return entries


def build_duplicate_groups(entries):
    parents = {entry["key"]: entry["key"] for entry in entries}

    def find(key):
        while parents[key] != key:
            parents[key] = parents[parents[key]]
            key = parents[key]
        return key

    def union(left, right):
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parents[right_root] = left_root

    by_doi = defaultdict(list)
    for entry in entries:
        doi = entry["fields"].get("doi", "").strip().lower()
        if doi:
            by_doi[doi].append(entry)

    doi_dupes = {doi: group for doi, group in by_doi.items() if len(group) > 1}
    for group in doi_dupes.values():
        survivor = group[0]["key"]
        for entry in group[1:]:
            union(survivor, entry["key"])

    seen = []
    title_dupes = []
    for entry in entries:
        title = entry["fields"].get("title", "")
        if not title:
            continue
        norm = normalize(title)
        for other_key, other_norm in seen:
            score = difflib.SequenceMatcher(None, norm, other_norm).ratio()
            if score >= TITLE_MATCH_THRESHOLD:
                title_dupes.append((entry["key"], other_key, score))
                union(entry["key"], other_key)
        seen.append((entry["key"], norm))

    grouped_entries = defaultdict(list)
    for entry in entries:
        grouped_entries[find(entry["key"])].append(entry)

    duplicate_groups = [group for group in grouped_entries.values() if len(group) > 1]
    return doi_dupes, title_dupes, duplicate_groups


def merge_entries(entries):
    merged = {"type": entries[0]["type"]}
    unique_keys = sorted({entry["key"] for entry in entries})
    merged["key"] = "-".join(unique_keys)
    merged_fields = {}
    for entry in entries:
        for field_name, value in entry["fields"].items():
            if field_name not in merged_fields:
                merged_fields[field_name] = value
            elif merged_fields[field_name] != value:
                merged_fields[field_name] += " | " + value
    merged["fields"] = merged_fields
    return merged


def write_deduped_bib(entries, duplicate_groups, output_path: Path):
    duplicate_keys = {entry["key"] for group in duplicate_groups for entry in group}
    deduped_entries = [merge_entries(group) for group in duplicate_groups]
    deduped_entries.extend(entry for entry in entries if entry["key"] not in duplicate_keys)

    with open(output_path, "w", encoding="utf-8") as f:
        for entry in deduped_entries:
            f.write(f"@{entry['type']}{{{entry['key']},\n")
            for field_name, value in entry["fields"].items():
                f.write(f"  {field_name} = {{{value}}},\n")
            f.write("}\n\n")


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "bib",
        nargs="?",
        type=Path,
        default=DEFAULT_BIB_PATH,
        help=f"Bib file to deduplicate (default: {DEFAULT_BIB_PATH})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output path for the merged bibliography preview",
    )
    return parser


def main():
    args = build_parser().parse_args()
    entries = parse_bib(args.bib)
    print(f"Parsed {len(entries)} entries.\n")
    doi_dupes, title_dupes, duplicate_groups = build_duplicate_groups(entries)

    if doi_dupes:
        print("=== Same DOI, different keys ===")
        for doi, group in doi_dupes.items():
            keys = ", ".join(entry["key"] for entry in group)
            print(f"  DOI {doi}: {keys}")
        print()

    if title_dupes:
        print("=== Near-identical titles, different keys ===")
        for k1, k2, score in title_dupes:
            print(f"  {k1}  <->  {k2}   (title similarity {score:.2f})")
        print()

    if not doi_dupes and not title_dupes:
        print("No likely duplicates found.")
    else:
        total_citations = len(entries)
        print(f"Total citations: {total_citations}")
        print(
            f"Found {len(doi_dupes)} DOI collisions and {len(title_dupes)} title collisions.")
        unique_count = total_citations - sum(len(group) - 1 for group in duplicate_groups)
        print(f"After deduplication, you would have {unique_count} unique citations.")

        print("For each duplicate group: keep one key, then in thesis/latex/**/*.tex")
        print("and thesis/markdown/**/*.md")
        print("replace the losing key with the surviving one, and delete the")
        print(f"losing @entry from {args.bib.name}.")

        output_path = args.output or args.bib.with_name(
            f"{args.bib.stem}_deduped{args.bib.suffix}"
        )
        write_deduped_bib(entries, duplicate_groups, output_path)
        print(f"Wrote merged preview bibliography to {output_path}")


if __name__ == "__main__":
    main()
