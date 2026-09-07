# Copilot Workspace Instructions

This workspace manages research content that may exist in multiple forms at the same time, including thesis markdown, thesis LaTeX, papers, and experiment repositories. The active source of truth can change as the documentation matures.

## Core Operating Rules

1. Treat source-of-truth selection as an explicit repository concern, not an assumption.
2. Before editing content that may exist in more than one place, check `docs/source-of-truth-tracker.md` and align to the currently declared canonical file.
3. If the tracker does not cover the content being edited, pause broad propagation work and either:
   - update only the file the user explicitly requested, or
   - propose a tracker entry before synchronizing duplicates.
4. When a change affects mirrored content, state which files were updated and which related files still need reconciliation.
5. Prefer editing the canonical source first, then propagate to derived or mirrored documents.
6. Do not silently rewrite the same research claim in multiple locations with different wording unless the user asks for audience-specific adaptation.

## Documentation Workflow Rules

1. Preserve the distinction between content sources and presentation formats.
2. For thesis content, keep markdown and LaTeX structurally aligned when both are intended to represent the same section.
3. For paper content derived from thesis sections, preserve venue-specific framing while keeping research facts, claims, and citations consistent with the canonical source.
4. Do not edit build artifacts under `build/` unless the user explicitly asks for generated outputs to be inspected.
5. Do not change class files, style files, or bibliography style assets unless the user asks for formatting or tooling changes.
6. When adding new sections or files, follow the existing folder split by document type and chapter/contribution. If the file is too long and can be divided into sections, create separate files and name them with a stable section stem plus an ordered numeric suffix, for example `literature_01.md` or `methodology_03.md`.
7. In thesis markdown folders, numbered files such as `literature_01.md` are intentional canonical subsection content, not temporary fragments. Preserve their numbering, keep one focused subsection per file, and treat any matching top-level file such as `literature.md` or `methodology.md` as a short roadmap or assembly anchor for that section.
8. When there is a citation, check the paper name in the thesis/bibliography and if it's there, mention the correct reference name in the text. If the reference is missing, add the paper name to the unresolved_cite.txt

## Citation Handling Rules

1. Prefer exact `\cite{bibtex_key}` citations whenever the source already exists in a workspace bibliography file.
2. Before leaving a citation unresolved, check the available bibliography files in the thesis and any relevant paper folder for an existing BibTeX entry or matching title.
3. If an exact BibTeX key cannot be found, leave a trackable inline placeholder in the text using the paper title or a short descriptive label, and record the same item in `thesis/unresloved_cite.txt`.
4. When a placeholder is later resolved to a BibTeX key, replace the inline placeholder with `\cite{bibtex_key}` and remove the matching item from `thesis/unresloved_cite.txt`.
5. Do not invent BibTeX keys, paper titles, or citation mappings that are not present in the workspace sources.
6. Keep unresolved citations grouped by relevant section or contribution in `thesis/unresloved_cite.txt` so unrelated items do not get mixed together.


## Source-of-Truth Change Rules

1. Any change in the canonical home of a topic, section, figure, table, or experiment summary should be recorded in `docs/source-of-truth-tracker.md`.
2. A tracker update should include:
   - the scope of the content
   - the new canonical file
   - the previous canonical file, if any
   - the reason for the change
   - the dependent files that need syncing
   - the sync status
3. If a requested edit implies a source-of-truth transition, call that out explicitly before or while making the change.

## Editing Heuristics For Copilot

1. Prefer small, traceable edits over broad rewrites across thesis and paper surfaces.
2. When the user asks for content refinement, preserve technical meaning, citation intent, and cross-document consistency.
3. When uncertainty exists about whether markdown or LaTeX is primary for a thesis section, ask or defer propagation rather than inventing a direction.
4. When touching experiment-linked claims, check whether `paper-experiments/` contains a corresponding repository or note the dependency if it is outside this workspace.

## Expected Response Pattern

When working on documentation tasks in this workspace, Copilot should explicitly communicate:

1. which file is being treated as canonical for the requested change
2. whether parallel copies exist
3. whether the tracker was updated or should be updated
4. what remains unsynchronized, if anything