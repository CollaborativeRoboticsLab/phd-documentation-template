#!/usr/bin/env python3
"""
Three modes:

  from-list   Turns a pile of messy, AI-tool-generated reference strings into
              clean, verified bibtex entries appended to a .bib file — and
              flags anything that doesn't resolve, which is usually either a
              fabricated/hallucinated citation or a preprint/source not
              indexed anywhere searchable.

  check-bib   Verifies the entries already in a .bib file against Crossref
              (and arXiv as a fallback) — fills in any fields missing from
              entries that verify with confidence, and flags entries that
              can't be confidently verified so you can eyeball them by hand.

    sync-unresolved-markdown
                            Resolves entries from thesis/unresolved_cite.txt into
                            thesis/resolved_cite.txt and removes those resolved entries from
                            thesis/unresolved_cite.txt. With --prepare-only it stops there;
                            without it, it also performs the older bibliography and markdown
                            sync behavior.

USAGE:
    python verify_citations.py from-list refs_raw.txt [--bib thesis/latex/Bibliography.bib] [--flagged thesis/unresolved_cite.txt]
    python verify_citations.py check-bib [thesis/latex/Bibliography.bib] [--flagged thesis/unresolved_cite.txt]
    python verify_citations.py sync-unresolved-markdown [thesis/unresolved_cite.txt] [--bib thesis/latex/Bibliography.bib] [--flagged thesis/unresolved_cite.txt]
"""

import argparse
import builtins
import html
import os
import sys
import re
import time
import requests
from pathlib import Path
from collections import OrderedDict
from rapidfuzz import fuzz

ROOT = Path(__file__).parent.parent
BIB_FILE = ROOT / "thesis/latex/Bibliography.bib"
FLAGGED_FILE = ROOT / "thesis/unresolved_cite.txt"
RESOLVED_FILE = ROOT / "thesis/resolved_cite.txt"

MARKDOWN_SECTION_DIRS = {
    "Contribution 1": ROOT / "thesis/markdown/contribution_1",
    "Contribution 2": ROOT / "thesis/markdown/contribution_2",
}

REPO_BIB_PATTERNS = (
    "thesis/latex/Bibliography.bib",
    "papers/*/references.bib",
)

GENERIC_PLACEHOLDER_WORDS = {"paper", "reference", "references", "source"}

CROSSREF_API = "https://api.crossref.org/works"
ARXIV_API = "http://export.arxiv.org/api/query"
DOI_RESOLVER = "https://doi.org/{doi}"

# Set this to your real email — Crossref's "polite pool" gives faster,
# more reliable service to requests that identify a contact. Override with
# --email on the command line instead of editing this if you'd rather not
# hardcode it here.
CONTACT_EMAIL = "your_email@example.com"

TITLE_MATCH_THRESHOLD = 0.72  # similarity below this => flagged, not accepted
RESOLUTION_CONFIDENCE_THRESHOLD = 0.75
REQUEST_DELAY = 0.3           # seconds between API calls, be polite

HEADERS = {"User-Agent": f"bib-verifier/1.0 (mailto:{CONTACT_EMAIL})"}


def spaced_print(*args, **kwargs):
    kwargs.setdefault("end", "\n\n")
    builtins.print(*args, **kwargs)


print = spaced_print


def normalize(text: str) -> str:
    text = re.sub(r"[^a-z0-9 ]", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def title_similarity(a: str, b: str) -> float:
    """Similarity in [0, 1]. Uses rapidfuzz's token_set_ratio rather than
    difflib.SequenceMatcher: token_set_ratio compares the set of words each
    string shares against the words unique to each side, so a string that
    is a superset of the other's words (e.g. "title + authors + year" vs.
    "title" alone) does NOT get penalised the way a length-sensitive ratio
    does. See the PATCH NOTE at the top of this file for why this changed."""
    return fuzz.token_set_ratio(normalize(a), normalize(b)) / 100.0


def clean_abstract_text(text: str | None) -> str | None:
    if not text:
        return None

    cleaned = html.unescape(text)
    cleaned = re.sub(r"</?jats:[^>]+>", " ", cleaned)
    cleaned = re.sub(r"</?[^>]+>", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned or None


def crossref_lookup(raw_ref: str, score_against: str | None = None):
    """Query Crossref's bibliographic fuzzy-match endpoint with `raw_ref`
    (a richer query -- e.g. title+author+year -- helps Crossref's own
    relevance ranking find the right candidate). Score candidates against
    `score_against` if given (pass the bare title when you have one --
    see run_check_bib), otherwise fall back to scoring against `raw_ref`
    itself (used by run_from_list, where no separate title is available)."""
    scoring_text = score_against if score_against is not None else raw_ref
    try:
        resp = requests.get(
            CROSSREF_API,
            params={"query.bibliographic": raw_ref, "rows": 3},
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        items = resp.json().get("message", {}).get("items", [])
    except requests.RequestException as e:
        print(f"    [crossref error] {e}")
        return None

    best = None
    best_score = 0.0
    for item in items:
        titles = item.get("title", [])
        if not titles:
            continue
        score = title_similarity(scoring_text, titles[0])
        if score > best_score:
            best_score = score
            best = item

    if best is None:
        return None
    return {
        "doi": best.get("DOI"),
        "title": best.get("title", [""])[0],
        "score": best_score,
        "abstract": clean_abstract_text(best.get("abstract")),
    }


def fetch_crossref_metadata(doi: str) -> dict | None:
    try:
        resp = requests.get(
            f"{CROSSREF_API}/{doi}",
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        item = resp.json().get("message", {})
    except requests.RequestException as e:
        print(f"    [crossref metadata error] {e}")
        return None

    return {
        "title": (item.get("title") or [""])[0],
        "abstract": clean_abstract_text(item.get("abstract")),
    }


def arxiv_lookup(raw_ref: str, score_against: str | None = None):
    """Fallback for preprints not in Crossref. See crossref_lookup() for
    what `score_against` does and why."""
    scoring_text = score_against if score_against is not None else raw_ref
    try:
        resp = requests.get(
            ARXIV_API,
            params={"search_query": f"all:{raw_ref}", "max_results": 3},
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"    [arxiv error] {e}")
        return None

    # crude XML title extraction, avoids adding an XML-parsing dependency
    titles = re.findall(r"<title>(.*?)</title>", resp.text, re.DOTALL)
    ids = re.findall(r"<id>(http://arxiv\.org/abs/[^<]+)</id>", resp.text)
    summaries = re.findall(r"<summary>(.*?)</summary>", resp.text, re.DOTALL)
    titles = [t.strip() for t in titles[1:]]  # skip feed's own title
    summaries = [clean_abstract_text(s) for s in summaries]
    if not titles or not ids:
        return None

    best_idx, best_score = None, 0.0
    for i, t in enumerate(titles):
        score = title_similarity(scoring_text, t)
        if score > best_score:
            best_score, best_idx = score, i
    if best_idx is None:
        return None
    return {
        "arxiv_id": ids[best_idx].rsplit("/", 1)[-1],
        "title": titles[best_idx],
        "score": best_score,
        "abstract": summaries[best_idx] if best_idx < len(summaries) else None,
    }


def fetch_bibtex_for_doi(doi: str) -> str | None:
    try:
        resp = requests.get(
            DOI_RESOLVER.format(doi=doi),
            headers={**HEADERS, "Accept": "application/x-bibtex"},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.text.strip()
    except requests.RequestException as e:
        print(f"    [doi fetch error] {e}")
        return None


def arxiv_bibtex(arxiv_id: str, title: str) -> str:
    # arXiv has no native BibTeX endpoint; build a minimal, valid entry.
    key = "arxiv" + re.sub(r"[^0-9]", "", arxiv_id)[:10]
    return (
        f"@misc{{{key},\n"
        f"  title = {{{title}}},\n"
        f"  eprint = {{{arxiv_id}}},\n"
        f"  archivePrefix = {{arXiv}},\n"
        f"  url = {{https://arxiv.org/abs/{arxiv_id}}}\n"
        f"}}"
    )


def merge_missing_metadata(fields: dict, abstract: str | None) -> dict:
    merged = dict(fields)
    if abstract and not merged.get("abstract", "").strip():
        merged["abstract"] = abstract
    return merged


def parse_unresolved_sections(path: Path) -> OrderedDict[str, list[str]]:
    sections: OrderedDict[str, list[str]] = OrderedDict()
    current_section = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("# "):
            continue
        if line.startswith("## "):
            current_section = line[3:].strip()
            sections.setdefault(current_section, [])
            continue
        if current_section is None:
            continue
        sections[current_section].append(line)

    return sections


def format_unresolved_sections(sections: OrderedDict[str, list[str]]) -> str:
    lines = ["# Unresolved Citations", ""]
    for section, refs in sections.items():
        lines.append(f"## {section}")
        lines.extend(refs)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def format_resolved_sections(sections: OrderedDict[str, list[dict]]) -> str:
    lines = ["# Resolved Citations", ""]
    for section, refs in sections.items():
        lines.append(f"## {section}")
        for ref in refs:
            lines.append(ref["raw_ref"])
            lines.append(f"    status: {ref['status']}")
            lines.append(f"    title: {ref['title']}")
            lines.append(f"    cite: \\cite{{{ref['key']}}}")
            lines.append(f"    note: {ref['note']}")
            if ref.get("bibtex"):
                lines.append("    bibtex: <<<")
                for bibtex_line in ref["bibtex"].splitlines():
                    lines.append(f"        {bibtex_line}")
                lines.append("    >>>")
            lines.append("")
        if not refs:
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_existing_bib_indexes(bib_path: Path) -> tuple[set[str], dict[str, str], dict[str, str]]:
    existing_dois: set[str] = set()
    doi_to_key: dict[str, str] = {}
    title_to_key: dict[str, str] = {}

    if not bib_path.exists():
        return existing_dois, doi_to_key, title_to_key

    entries = split_bib_entries(bib_path.read_text(encoding="utf-8"))
    for entry in entries:
        key = entry["key"]
        fields = entry["fields"]
        doi = fields.get("doi", "").strip().lower()
        if doi:
            existing_dois.add(doi)
            doi_to_key[doi] = key
        title = fields.get("title", "").strip()
        if title:
            title_to_key[normalize(title)] = key

    return existing_dois, doi_to_key, title_to_key


def find_repo_entry_by_key(repo_entries: list[dict], cite_key: str) -> dict | None:
    for entry in repo_entries:
        if entry["key"] == cite_key:
            return entry
    return None


def resolve_reference_to_bib(raw_ref: str, doi_to_key: dict[str, str], title_to_key: dict[str, str], repo_entries: list[dict]):
    local_entry = find_local_bib_candidate(raw_ref, repo_entries)
    if local_entry is not None:
        local_title_key = title_to_key.get(local_entry["norm_title"])
        if local_title_key:
            return {
                "status": "existing",
                "key": local_title_key,
                "title": local_entry["title"],
                "bibtex": local_entry["raw"],
                "score": 1.0,
                "note": f"matched existing local title from {local_entry['path'].relative_to(ROOT)}",
            }

        doi_norm = local_entry["fields"].get("doi", "").strip().lower()
        if doi_norm and doi_norm in doi_to_key:
            return {
                "status": "existing",
                "key": doi_to_key[doi_norm],
                "title": local_entry["title"],
                "bibtex": local_entry["raw"],
                "score": 1.0,
                "note": f"matched existing local DOI from {local_entry['path'].relative_to(ROOT)}",
            }

        if doi_norm:
            doi_to_key[doi_norm] = local_entry["key"]
        if local_entry["norm_title"]:
            title_to_key[local_entry["norm_title"]] = local_entry["key"]
        return {
            "status": "new",
            "key": local_entry["key"],
            "title": local_entry["title"],
            "bibtex": local_entry["raw"],
            "score": 1.0,
            "note": f"copied verified local entry from {local_entry['path'].relative_to(ROOT)}",
        }

    if is_generic_placeholder_label(raw_ref):
        return {
            "status": "unresolved",
            "score": 0.0,
            "note": "generic placeholder label needs an exact title or a unique local bibliography match",
        }

    cr = crossref_lookup(raw_ref)
    time.sleep(REQUEST_DELAY)

    if cr and cr["score"] >= RESOLUTION_CONFIDENCE_THRESHOLD:
        doi_norm = (cr["doi"] or "").strip().lower()
        if doi_norm and doi_norm in doi_to_key:
            existing_entry = find_repo_entry_by_key(repo_entries, doi_to_key[doi_norm])
            return {
                "status": "existing",
                "key": doi_to_key[doi_norm],
                "title": cr["title"],
                "bibtex": existing_entry["raw"] if existing_entry else None,
                "score": cr["score"],
                "note": f"matched existing DOI {doi_norm}",
            }

        bibtex = fetch_bibtex_for_doi(cr["doi"])
        time.sleep(REQUEST_DELAY)
        if bibtex:
            key, parsed_fields = parse_entry_fields(bibtex)
            parsed_fields = merge_missing_metadata(parsed_fields, cr.get("abstract"))
            bibtex = add_missing_fields(
                bibtex,
                {"abstract": parsed_fields["abstract"]} if parsed_fields.get("abstract") else {},
            )
            if doi_norm:
                doi_to_key[doi_norm] = key
            if parsed_fields.get("title"):
                title_to_key[normalize(parsed_fields["title"])] = key
            return {
                "status": "new",
                "key": key,
                "title": cr["title"],
                "bibtex": bibtex,
                "score": cr["score"],
                "note": f"verified via Crossref score {cr['score']:.2f}",
            }

    ax = arxiv_lookup(raw_ref)
    time.sleep(REQUEST_DELAY)
    if ax and ax["score"] >= RESOLUTION_CONFIDENCE_THRESHOLD:
        normalized_title = normalize(ax["title"])
        if normalized_title in title_to_key:
            existing_entry = find_repo_entry_by_key(repo_entries, title_to_key[normalized_title])
            return {
                "status": "existing",
                "key": title_to_key[normalized_title],
                "title": ax["title"],
                "bibtex": existing_entry["raw"] if existing_entry else None,
                "score": ax["score"],
                "note": "matched existing arXiv title",
            }

        bibtex = arxiv_bibtex(ax["arxiv_id"], ax["title"])
        if ax.get("abstract"):
            bibtex = add_missing_fields(bibtex, {"abstract": ax["abstract"]})
        key, parsed_fields = parse_entry_fields(bibtex)
        if parsed_fields.get("title"):
            title_to_key[normalize(parsed_fields["title"])] = key
        return {
            "status": "new",
            "key": key,
            "title": ax["title"],
            "bibtex": bibtex,
            "score": ax["score"],
            "note": f"verified via arXiv score {ax['score']:.2f}",
        }

    if cr:
        if cr["score"] >= TITLE_MATCH_THRESHOLD:
            note = f"closest Crossref match below resolution confidence ({cr['score']:.2f} < {RESOLUTION_CONFIDENCE_THRESHOLD:.2f}): {cr['title']}"
        else:
            note = f"closest Crossref match ({cr['score']:.2f}): {cr['title']}"
    elif ax:
        if ax["score"] >= TITLE_MATCH_THRESHOLD:
            note = f"closest arXiv match below resolution confidence ({ax['score']:.2f} < {RESOLUTION_CONFIDENCE_THRESHOLD:.2f}): {ax['title']}"
        else:
            note = f"closest arXiv match ({ax['score']:.2f}): {ax['title']}"
    else:
        note = "no candidate match found at all"

    return {"status": "unresolved", "score": 0.0, "note": note}


def replace_markdown_citations(section_dir: Path, replacements: dict[str, str], dry_run: bool) -> tuple[int, list[str], dict[str, int]]:
    total_replacements = 0
    touched_files: list[str] = []
    per_reference_counts = {raw_ref: 0 for raw_ref in replacements}

    for md_path in sorted(section_dir.rglob("*.md")):
        original = md_path.read_text(encoding="utf-8")
        updated = original
        file_replacements = 0

        for raw_ref, cite_key in replacements.items():
            pattern = f"[{raw_ref}]"
            replacement = f"\\cite{{{cite_key}}}"
            count = updated.count(pattern)
            if count:
                updated = updated.replace(pattern, replacement)
                file_replacements += count
                per_reference_counts[raw_ref] += count

        if updated != original:
            total_replacements += file_replacements
            touched_files.append(os.fspath(md_path.relative_to(ROOT)))
            if not dry_run:
                md_path.write_text(updated, encoding="utf-8")

    return total_replacements, touched_files, per_reference_counts


# ---------------------------------------------------------------------------
# Minimal bibtex parsing (regex/brace-counting — avoids a bibtex dependency)
# ---------------------------------------------------------------------------

def split_bib_entries(text: str) -> list[dict]:
    """Split a .bib file's text into top-level @type{key, ...} entries."""
    entries = []
    i = 0
    n = len(text)
    header_re = re.compile(r"@(\w+)\s*\{")
    while True:
        m = header_re.search(text, i)
        if not m:
            break
        entry_type = m.group(1)
        brace_start = m.end() - 1  # index of the opening '{'
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
            break  # unbalanced braces, bail out rather than mangling the file
        raw = text[m.start():j + 1]
        key, fields = parse_entry_fields(raw)
        entries.append({
            "start": m.start(),
            "end": j + 1,
            "type": entry_type,
            "key": key,
            "fields": fields,
            "raw": raw,
        })
        i = j + 1
    return entries


def iter_repo_bib_entries() -> list[dict]:
    entries: list[dict] = []
    seen_paths: set[Path] = set()

    for pattern in REPO_BIB_PATTERNS:
        for bib_path in sorted(ROOT.glob(pattern)):
            if bib_path in seen_paths or not bib_path.exists():
                continue
            seen_paths.add(bib_path)
            for entry in split_bib_entries(bib_path.read_text(encoding="utf-8")):
                fields = entry["fields"]
                title = fields.get("title", "").strip()
                entries.append({
                    "path": bib_path,
                    "key": entry["key"],
                    "raw": entry["raw"],
                    "fields": fields,
                    "title": title,
                    "norm_title": normalize(title) if title else "",
                })

    return entries


def is_generic_placeholder_label(raw_ref: str) -> bool:
    tokens = set(normalize(raw_ref).split())
    return any(word in tokens for word in GENERIC_PLACEHOLDER_WORDS)


def placeholder_search_terms(raw_ref: str) -> list[str]:
    terms = []
    for token in re.findall(r"[A-Za-z0-9_+-]+", raw_ref):
        normalized = normalize(token)
        if not normalized or normalized in GENERIC_PLACEHOLDER_WORDS:
            continue
        if len(normalized) >= 4 or any(char.isdigit() for char in normalized):
            terms.append(normalized)
    return terms


def find_local_bib_candidate(raw_ref: str, repo_entries: list[dict]) -> dict | None:
    normalized_ref = normalize(raw_ref)
    exact_matches = [entry for entry in repo_entries if entry["norm_title"] == normalized_ref]
    if len(exact_matches) == 1:
        return exact_matches[0]

    if not is_generic_placeholder_label(raw_ref):
        return None

    terms = placeholder_search_terms(raw_ref)
    if not terms:
        return None

    candidates = [
        entry for entry in repo_entries
        if entry["norm_title"] and all(term in entry["norm_title"] for term in terms)
    ]
    if len(candidates) == 1:
        return candidates[0]
    return None


def parse_entry_fields(raw: str) -> tuple[str, dict]:
    """Parse the cite key and field dict out of one raw @type{...} entry."""
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


def add_missing_fields(raw: str, missing: dict) -> str:
    """Insert fields not already present into a raw entry, before its closing brace."""
    if not missing:
        return raw
    body = raw[:-1].rstrip()  # drop the closing '}'
    if not body.endswith(","):
        body += ","
    lines = [body]
    for fname, fval in missing.items():
        lines.append(f"  {fname} = {{{fval}}},")
    return "\n".join(lines) + "\n}"


def entry_query_string(fields: dict) -> str | None:
    """Best-effort text to search Crossref/arXiv with, when there's no DOI."""
    parts = [fields.get(k, "") for k in ("title", "author", "year")]
    query = " ".join(p for p in parts if p).strip()
    return query or None


# ---------------------------------------------------------------------------
# from-list: messy raw references -> verified bibtex, appended
# ---------------------------------------------------------------------------

def run_from_list(input_path: Path, bib_path: Path, flagged_path: Path, dry_run: bool):
    with open(input_path, encoding="utf-8") as f:
        raw_refs = [line.strip() for line in f if line.strip()]

    # Load existing DOIs to avoid appending duplicates
    existing_dois: set[str] = set()
    if bib_path.exists():
        existing_text = bib_path.read_text(encoding="utf-8")
        for m in re.finditer(r"\bdoi\s*=\s*\{([^}]+)\}", existing_text, re.IGNORECASE):
            existing_dois.add(m.group(1).strip().lower())

    bib_entries = []
    flagged = []

    for i, ref in enumerate(raw_refs, 1):
        print(f"[{i}/{len(raw_refs)}] {ref[:70]}...")

        cr = crossref_lookup(ref)
        time.sleep(REQUEST_DELAY)

        if cr and cr["score"] >= TITLE_MATCH_THRESHOLD:
            doi_norm = (cr["doi"] or "").strip().lower()
            if doi_norm and doi_norm in existing_dois:
                print(f"    -> SKIPPED (already in bib): {cr['title']}")
                continue
            bibtex = fetch_bibtex_for_doi(cr["doi"])
            time.sleep(REQUEST_DELAY)
            if bibtex:
                key, parsed_fields = parse_entry_fields(bibtex)
                parsed_fields = merge_missing_metadata(parsed_fields, cr.get("abstract"))
                bibtex = add_missing_fields(
                    bibtex,
                    {"abstract": parsed_fields["abstract"]} if parsed_fields.get("abstract") else {},
                )
                print(
                    f"    -> VERIFIED (score {cr['score']:.2f}): {cr['title']}")
                bib_entries.append(bibtex)
                if doi_norm:
                    existing_dois.add(doi_norm)
                continue

        # fall back to arXiv for preprints
        ax = arxiv_lookup(ref)
        time.sleep(REQUEST_DELAY)
        if ax and ax["score"] >= TITLE_MATCH_THRESHOLD:
            print(
                f"    -> VERIFIED via arXiv (score {ax['score']:.2f}): {ax['title']}")
            bibtex = arxiv_bibtex(ax["arxiv_id"], ax["title"])
            if ax.get("abstract"):
                bibtex = add_missing_fields(bibtex, {"abstract": ax["abstract"]})
            bib_entries.append(bibtex)
            continue

        # nothing resolved with confidence
        if cr:
            best_note = f"closest Crossref match ({cr['score']:.2f}): {cr['title']}"
        elif ax:
            best_note = f"closest arXiv match ({ax['score']:.2f}): {ax['title']}"
        else:
            best_note = "no candidate match found at all"
        print(f"    -> FLAGGED: {best_note}")
        flagged.append(f"{ref}\n    {best_note}\n")

    if dry_run:
        print(
            f"\n[dry-run] would append {len(bib_entries)} entries -> {bib_path}")
        print(f"[dry-run] would flag {len(flagged)} entries -> {flagged_path}")
        return

    if bib_entries:
        with open(bib_path, "a", encoding="utf-8") as f:
            if bib_path.stat().st_size > 0:
                f.write("\n\n")
            f.write("\n\n".join(bib_entries))

    if flagged:
        flagged_exists = flagged_path.exists() and flagged_path.stat().st_size > 0
        with open(flagged_path, "a", encoding="utf-8") as f:
            if flagged_exists:
                f.write("\n\n")
            f.write("\n\n".join(flagged))

    print(f"\nDone. {len(bib_entries)} verified -> {bib_path}")
    print(f"{len(flagged)} unresolved -> {flagged_path} (check these by hand;")
    print("some may be real-but-obscure sources, others may be fabricated).")


# ---------------------------------------------------------------------------
# check-bib: verify entries already in a .bib file, fill gaps, flag the rest
# ---------------------------------------------------------------------------

def run_check_bib(bib_path: Path, flagged_path: Path, dry_run: bool):
    if not bib_path.exists():
        print(f"error: {bib_path} does not exist")
        sys.exit(1)

    text = bib_path.read_text(encoding="utf-8")
    entries = split_bib_entries(text)
    if not entries:
        print(f"No bibtex entries found in {bib_path}")
        return

    flagged = []
    n_updated = 0
    n_ok = 0

    for i, entry in enumerate(entries, 1):
        key, fields = entry["key"], entry["fields"]
        title = fields.get("title", "")
        label = title[:70] if title else key
        print(f"[{i}/{len(entries)}] {key}: {label}...")

        canonical_fields = None
        note = None

        doi = fields.get("doi")
        if doi:
            bibtex = fetch_bibtex_for_doi(doi)
            time.sleep(REQUEST_DELAY)
            if bibtex:
                _, c_fields = parse_entry_fields(bibtex)
                metadata = fetch_crossref_metadata(doi)
                time.sleep(REQUEST_DELAY)
                if metadata:
                    c_fields = merge_missing_metadata(
                        c_fields, metadata.get("abstract"))
                c_title = c_fields.get("title", "")
                if title and c_title and title_similarity(title, c_title) < TITLE_MATCH_THRESHOLD:
                    note = f"doi {doi} resolves to a different title: {c_title}"
                else:
                    canonical_fields = c_fields
                    print(f"    -> VERIFIED via DOI: {c_title or doi}")
            else:
                note = f"doi {doi} did not resolve"

        if canonical_fields is None and note is None:
            query = entry_query_string(fields)
            if not query:
                note = "entry has no title/author/year to search with"
            else:
                # score_against=title: score candidates against the BARE
                # title (when we have one), not the title+author+year blob
                # sent as the search query -- see PATCH NOTE at top of file.
                cr = crossref_lookup(query, score_against=title or None)
                time.sleep(REQUEST_DELAY)
                if cr and cr["score"] >= TITLE_MATCH_THRESHOLD:
                    bibtex = fetch_bibtex_for_doi(cr["doi"])
                    time.sleep(REQUEST_DELAY)
                    if bibtex:
                        _, canonical_fields = parse_entry_fields(bibtex)
                        canonical_fields = merge_missing_metadata(
                            canonical_fields, cr.get("abstract"))
                        print(
                            f"    -> VERIFIED via Crossref (score {cr['score']:.2f}): {cr['title']}")

                ax = None
                if canonical_fields is None:
                    ax = arxiv_lookup(query, score_against=title or None)
                    time.sleep(REQUEST_DELAY)
                    if ax and ax["score"] >= TITLE_MATCH_THRESHOLD:
                        _, canonical_fields = parse_entry_fields(
                            arxiv_bibtex(ax["arxiv_id"], ax["title"])
                        )
                        canonical_fields = merge_missing_metadata(
                            canonical_fields, ax.get("abstract"))
                        print(
                            f"    -> VERIFIED via arXiv (score {ax['score']:.2f}): {ax['title']}")

                if canonical_fields is None:
                    if cr:
                        note = f"closest Crossref match ({cr['score']:.2f}): {cr['title']}"
                    elif ax:
                        note = f"closest arXiv match ({ax['score']:.2f}): {ax['title']}"
                    else:
                        note = "no candidate match found at all"

        if canonical_fields is not None:
            # any canonical field missing or blank in the original gets filled in
            missing = {
                k: v for k, v in canonical_fields.items()
                if not fields.get(k, "").strip()
            }
            if missing:
                entry["new_raw"] = add_missing_fields(entry["raw"], missing)
                n_updated += 1
                print(f"    -> added fields: {', '.join(missing)}")
            else:
                n_ok += 1
        else:
            print(f"    -> FLAGGED: {note}")
            flagged.append(f"{key}: {title or '(no title)'}\n    {note}\n")

    if dry_run:
        print(f"\n[dry-run] would update {n_updated} entries in {bib_path}")
        print(f"[dry-run] would flag {len(flagged)} entries -> {flagged_path}")
        return

    # rewrite entries with new fields, from the end so offsets stay valid
    new_text = text
    for entry in sorted(entries, key=lambda e: e["start"], reverse=True):
        if "new_raw" in entry:
            new_text = new_text[:entry["start"]] + \
                entry["new_raw"] + new_text[entry["end"]:]
    if new_text != text:
        bib_path.write_text(new_text, encoding="utf-8")

    if flagged:
        flagged_exists = flagged_path.exists() and flagged_path.stat().st_size > 0
        with open(flagged_path, "a", encoding="utf-8") as f:
            if flagged_exists:
                f.write("\n\n")
            f.write("\n\n".join(flagged))

    print(
        f"\nDone. {n_ok} already complete, {n_updated} updated -> {bib_path}")
    print(f"{len(flagged)} unresolved -> {flagged_path} (check these by hand;")
    print("some may be real-but-obscure sources, others may need manual fixes).")


def run_sync_unresolved_markdown(input_path: Path, bib_path: Path, flagged_path: Path, resolved_path: Path, dry_run: bool, prepare_only: bool):
    if not input_path.exists():
        print(f"error: {input_path} does not exist")
        sys.exit(1)

    sections = parse_unresolved_sections(input_path)
    _, doi_to_key, title_to_key = build_existing_bib_indexes(bib_path)
    repo_entries = iter_repo_bib_entries()
    bib_entries: list[str] = []
    resolved_sections: OrderedDict[str, list[dict]] = OrderedDict()
    unresolved_sections: OrderedDict[str, list[str]] = OrderedDict()
    section_replacements: dict[str, dict[str, str]] = {}

    for section, refs in sections.items():
        resolved_sections.setdefault(section, [])
        unresolved_sections.setdefault(section, [])
        if section not in MARKDOWN_SECTION_DIRS:
            unresolved_sections[section].extend(refs)
            print(f"[{section}] no markdown directory mapping configured; left {len(refs)} references unresolved")
            continue

        replacements: dict[str, str] = {}
        for index, ref in enumerate(refs, 1):
            print(f"[{section} {index}/{len(refs)}] {ref[:70]}...")
            result = resolve_reference_to_bib(ref, doi_to_key, title_to_key, repo_entries)
            if result["status"] == "unresolved":
                print(f"    -> FLAGGED: {result['note']}")
                unresolved_sections[section].append(ref)
                continue

            print(f"    -> {result['status'].upper()}: {result['key']} ({result['note']})")
            replacements[ref] = result["key"]
            resolved_sections[section].append({
                "raw_ref": ref,
                "status": result["status"],
                "title": result["title"],
                "key": result["key"],
                "note": result["note"],
                "bibtex": result.get("bibtex"),
            })
            if result["status"] == "new":
                bib_entries.append(result["bibtex"])

        section_replacements[section] = replacements

    resolved_output = format_resolved_sections(resolved_sections)
    unresolved_output = format_unresolved_sections(unresolved_sections)

    if dry_run and prepare_only:
        print(f"\n[dry-run] would write resolved citations -> {resolved_path}")
        print(f"[dry-run] would rewrite unresolved list -> {flagged_path}")
        print("[dry-run] would stop before BibTeX append and markdown replacement")
        return

    if prepare_only:
        resolved_path.write_text(resolved_output, encoding="utf-8")
        flagged_path.write_text(unresolved_output, encoding="utf-8")
        print(f"\nWrote resolved citations -> {resolved_path}")
        print(f"Updated unresolved list -> {flagged_path}")
        print("Stopped before BibTeX append and markdown replacement")
        return

    total_markdown_replacements = 0
    touched_files: list[str] = []
    refs_without_placeholder: list[str] = []

    for section, replacements in section_replacements.items():
        if not replacements:
            continue
        section_dir = MARKDOWN_SECTION_DIRS[section]
        replaced_count, files, per_reference_counts = replace_markdown_citations(section_dir, replacements, dry_run)
        total_markdown_replacements += replaced_count
        touched_files.extend(files)
        for ref, count in per_reference_counts.items():
            if count == 0:
                refs_without_placeholder.append(f"{section}: {ref}")

    if dry_run:
        print(f"\n[dry-run] would write resolved citations -> {resolved_path}")
        print(f"\n[dry-run] would append {len(bib_entries)} entries -> {bib_path}")
        print(f"[dry-run] would replace {total_markdown_replacements} markdown citation placeholders")
        print(f"[dry-run] would rewrite unresolved list -> {flagged_path}")
        if touched_files:
            print("[dry-run] markdown files to update:")
            for path in touched_files:
                print(f"    {path}")
        if refs_without_placeholder:
            print("[dry-run] verified references without matching markdown placeholders:")
            for item in refs_without_placeholder:
                print(f"    {item}")
        return

    resolved_path.write_text(resolved_output, encoding="utf-8")

    if bib_entries:
        existing_size = bib_path.stat().st_size if bib_path.exists() else 0
        with open(bib_path, "a", encoding="utf-8") as handle:
            if existing_size > 0:
                handle.write("\n\n")
            handle.write("\n\n".join(bib_entries))

    flagged_path.write_text(unresolved_output, encoding="utf-8")

    print(f"\nWrote resolved citations -> {resolved_path}")
    print(f"Done. {len(bib_entries)} verified entries appended -> {bib_path}")
    print(f"{total_markdown_replacements} markdown placeholders replaced")
    print(f"Updated unresolved list -> {flagged_path}")
    if refs_without_placeholder:
        print("Verified references without matching markdown placeholders:")
        for item in refs_without_placeholder:
            print(f"    {item}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--flagged", type=Path, default=FLAGGED_FILE,
                        help=f"File to append unresolved entries to (default: {FLAGGED_FILE})")
    common.add_argument("--email", default=None,
                        help="Contact email sent to Crossref's polite pool (default: unset)")
    common.add_argument("--threshold", type=float, default=TITLE_MATCH_THRESHOLD,
                        help=f"Title-similarity threshold, 0-1 (default: {TITLE_MATCH_THRESHOLD})")
    common.add_argument("--delay", type=float, default=REQUEST_DELAY,
                        help=f"Seconds to wait between API calls (default: {REQUEST_DELAY})")
    common.add_argument("--dry-run", action="store_true",
                        help="Report what would change without writing any files")

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("from-list", parents=[common],
                            help="Verify a messy list of raw references and append them to a bib file")
    p_list.add_argument("input", type=Path,
                        help="Text file with one raw reference per line")
    p_list.add_argument("--bib", type=Path, default=BIB_FILE,
                        help=f"Bib file to append verified entries to (default: {BIB_FILE})")

    p_check = sub.add_parser("check-bib", parents=[common],
                             help="Verify entries already in a bib file, filling in missing fields")
    p_check.add_argument("bib", type=Path, nargs="?", default=BIB_FILE,
                         help=f"Bib file to check (default: {BIB_FILE})")

    p_sync = sub.add_parser(
        "sync-unresolved-markdown",
        parents=[common],
        help="Verify unresolved thesis references, append bib entries, and replace markdown placeholders with \\cite{}",
    )
    p_sync.add_argument("input", type=Path, nargs="?", default=FLAGGED_FILE,
                        help=f"Sectioned unresolved citation file (default: {FLAGGED_FILE})")
    p_sync.add_argument("--bib", type=Path, default=BIB_FILE,
                        help=f"Bib file to append verified entries to (default: {BIB_FILE})")
    p_sync.add_argument("--resolved", type=Path, default=RESOLVED_FILE,
                        help=f"File to write resolved citations to before BibTeX updates (default: {RESOLVED_FILE})")
    p_sync.add_argument("--prepare-only", action="store_true",
                        help="Write resolved and unresolved citation files, then stop before BibTeX and markdown updates")

    return parser


def main():
    args = build_parser().parse_args()

    global TITLE_MATCH_THRESHOLD, REQUEST_DELAY, HEADERS
    TITLE_MATCH_THRESHOLD = args.threshold
    REQUEST_DELAY = args.delay
    if args.email:
        HEADERS = {"User-Agent": f"bib-verifier/1.0 (mailto:{args.email})"}

    if args.command == "from-list":
        run_from_list(args.input, args.bib, args.flagged, args.dry_run)
    elif args.command == "check-bib":
        run_check_bib(args.bib, args.flagged, args.dry_run)
    elif args.command == "sync-unresolved-markdown":
        run_sync_unresolved_markdown(args.input, args.bib, args.flagged, args.resolved, args.dry_run, args.prepare_only)


if __name__ == "__main__":
    main()
