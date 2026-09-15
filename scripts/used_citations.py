#!/usr/bin/env python3
"""
This checks the .bib file for any entries that are not cited in the thesis
"""

import argparse
import re
from pathlib import Path

from deduplicate_bib import parse_bib

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BIB_PATH = ROOT / "thesis/latex/Bibliography.bib"


def source_globs_for_bib(bib_path: Path):
    resolved_bib = bib_path.resolve()

    if resolved_bib == DEFAULT_BIB_PATH.resolve():
        return ("thesis/latex/**/*.tex", "thesis/markdown/**/*.md")

    try:
        relative_bib = resolved_bib.relative_to(ROOT)
    except ValueError:
        return (str(bib_path.parent / "**/*.tex"), str(bib_path.parent / "**/*.md"))

    if relative_bib.name == "references.bib" and relative_bib.parts[:1] == ("papers",):
        paper_dir = Path(*relative_bib.parts[:-1])
        return (str(paper_dir / "**/*.tex"), str(paper_dir / "**/*.md"))

    bib_dir = relative_bib.parent
    return (str(bib_dir / "**/*.tex"), str(bib_dir / "**/*.md"))


def find_entry_line_numbers(bib_path):
    """Return a map of bib key -> 1-based line number where the entry starts."""
    line_numbers = {}
    # Matches lines like: @article{key, or @book{key,
    entry_re = re.compile(r"^\s*@\w+\s*\{\s*([^,\s]+)")

    with open(bib_path, encoding="utf-8") as f:
        for idx, line in enumerate(f, start=1):
            match = entry_re.match(line)
            if match:
                line_numbers[match.group(1)] = idx

    return line_numbers


def extract_entry_links(bib_path):
    """Return a map of bib key -> best paper link extracted from raw BibTeX text."""
    links = {}
    entry_start_re = re.compile(r"^\s*@\w+\s*\{\s*([^,\s]+)")

    with open(bib_path, encoding="utf-8") as f:
        lines = f.readlines()

    def normalize_link(link):
        # BibTeX values may be line-wrapped; remove internal whitespace for a valid URL.
        return "".join(link.split())

    def canonicalize_doi_url(url):
        doi_from_url = re.search(
            r"(?:dx\.)?doi\.org/(.+)$", url, flags=re.IGNORECASE)
        if doi_from_url:
            doi = doi_from_url.group(1).strip().rstrip("/")
            if doi.upper().endswith("/BIBTEX"):
                doi = doi[:-7].rstrip("/")
            return f"https://doi.org/{doi}"
        return url

    def parse_link_from_block(block_text):
        doi_match = re.search(
            r'doi\s*=\s*[\{"]([^\}\"]+)[\}"]',
            block_text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if doi_match:
            doi = normalize_link(doi_match.group(1).strip())
            if doi.upper().endswith("/BIBTEX"):
                doi = doi[:-7].rstrip("/")
            return f"https://doi.org/{doi}"

        wrapped_url = re.search(
            r"url\s*=\s*\{\s*\\url\{([^}]+)\}\s*\}",
            block_text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if wrapped_url:
            return canonicalize_doi_url(normalize_link(wrapped_url.group(1).strip()))

        plain_url = re.search(
            r'url\s*=\s*[\{"]([^\}\"]+)[\}"]',
            block_text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if plain_url:
            return canonicalize_doi_url(normalize_link(plain_url.group(1).strip()))

        return None

    current_key = None
    current_block = []
    for line in lines:
        start = entry_start_re.match(line)
        if start:
            if current_key and current_block:
                link = parse_link_from_block("".join(current_block))
                if link:
                    links[current_key] = link
            current_key = start.group(1)
            current_block = [line]
        elif current_key is not None:
            current_block.append(line)

    if current_key and current_block:
        link = parse_link_from_block("".join(current_block))
        if link:
            links[current_key] = link

    return links


def get_paper_link(entry, entry_links):
    """Return the best clickable paper link for a bib entry, if available."""
    raw_link = entry_links.get(entry["key"])
    if raw_link:
        return raw_link

    fields = entry.get("fields", {})

    doi = fields.get("doi", "").strip()
    if doi:
        doi = "".join(doi.split())
        if doi.upper().endswith("/BIBTEX"):
            doi = doi[:-7].rstrip("/")
        return f"https://doi.org/{doi}"

    url = fields.get("url", "").strip()
    if url:
        url = "".join(url.split())
        doi_from_url = re.search(
            r"(?:dx\.)?doi\.org/(.+)$", url, flags=re.IGNORECASE)
        if doi_from_url:
            doi = doi_from_url.group(1).strip().rstrip("/")
            if doi.upper().endswith("/BIBTEX"):
                doi = doi[:-7].rstrip("/")
            return f"https://doi.org/{doi}"
        return url

    return None


def extract_citation_keys(content):
    keys = set()

    for match in re.finditer(r"\\[A-Za-z]*cite[a-zA-Z*]*\s*\{([^}]+)\}", content):
        for key in match.group(1).split(","):
            cleaned = key.strip()
            if cleaned:
                keys.add(cleaned)

    for match in re.finditer(r"\[@([^\]]+)\]", content):
        for key in re.findall(r"@([A-Za-z0-9_:\-./]+)", match.group(1)):
            keys.add(key.strip())

    return keys


def collect_used_keys(entry_keys, source_globs):
    used_keys = set()
    scanned_files = []

    for pattern in source_globs:
        for source_file in sorted(ROOT.glob(pattern)):
            scanned_files.append(source_file)
            content = source_file.read_text(encoding="utf-8")
            used_keys.update(extract_citation_keys(content) & entry_keys)

    return used_keys, scanned_files


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "bib",
        nargs="?",
        type=Path,
        default=DEFAULT_BIB_PATH,
        help=f"Bib file to inspect (default: {DEFAULT_BIB_PATH})",
    )
    return parser


def main():
    args = build_parser().parse_args()
    bib_path = args.bib
    entries = parse_bib(bib_path)
    entry_line_numbers = find_entry_line_numbers(bib_path)
    entry_links = extract_entry_links(bib_path)
    source_globs = source_globs_for_bib(bib_path)

    used_keys, scanned_files = collect_used_keys(
        {entry["key"] for entry in entries}, source_globs
    )

    unused_entries = [e for e in entries if e["key"] not in used_keys]
    if unused_entries:
        print("Unused entries:")
        for e in unused_entries:
            line_no = entry_line_numbers.get(e["key"])
            paper_link = get_paper_link(e, entry_links)
            if line_no:
                # VS Code terminals auto-link file:line references.
                if paper_link:
                    print(
                        f"- {e['key']} ({bib_path}:{line_no}) | paper: {paper_link}")
                else:
                    print(f"- {e['key']} ({bib_path}:{line_no}) | paper: N/A")
            else:
                if paper_link:
                    print(f"- {e['key']} ({bib_path}) | paper: {paper_link}")
                else:
                    print(f"- {e['key']} ({bib_path}) | paper: N/A")
    else:
        print("All entries are used.")

    print("\nSummary:")
    print(f"- Parsed entries: {len(entries)}")
    print(f"- Scanned source files: {len(scanned_files)}")
    print(f"- Used entries: {len(used_keys)}")
    print(f"- Unused entries: {len(unused_entries)}")


if __name__ == "__main__":
    main()
