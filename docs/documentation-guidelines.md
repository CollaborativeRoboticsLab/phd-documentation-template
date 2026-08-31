# Documentation Guidelines

## Purpose

This repository holds research content across thesis, papers, and experiment-linked artifacts. Because the same ideas may appear in multiple places, every content update should distinguish between:

1. the canonical source of the content
2. mirrored or derived copies
3. presentation-specific adaptations

## Document Roles

| Area | Typical role |
| --- | --- |
| `thesis/markdown/` | drafting and fast iteration |
| `thesis/latex/` | thesis publication format |
| `papers/` | venue-specific paper manuscripts |
| `paper-experiments/` | experiment evidence, code, and results provenance |

These roles are defaults, not hard rules. The active source of truth may move from one area to another as a section matures.

## Source-of-Truth Policy

1. Every substantial topic should have one declared canonical location at a time.
2. Canonical means the file that should be edited first when the research content itself changes.
3. Mirrored files may differ in formatting, compression, and audience framing, but not in factual claims unless the divergence is intentional and documented.
4. If the canonical location changes, record it in `docs/source-of-truth-tracker.md` before or as part of the related content update.

## Editing Rules

1. Update the canonical source first.
2. Propagate the change to mirrored files in the same task when feasible.
3. If full propagation is not feasible, leave a clear tracker note showing what remains out of sync.
4. Keep section names and hierarchy as aligned as practical across markdown and LaTeX versions of the thesis.
5. Avoid creating duplicate content files unless there is a clear document-specific need.
6. Keep citations and references consistent across mirrored sections.

## Stage-Based Workflow

Use the following workflow when content matures across documents:

1. Draft stage: prefer the fastest editing surface.
2. Review stage: declare the active canonical file for the section being reviewed.
3. Publication stage: if accepted paper wording becomes canonical for a topic, record the handoff.
4. Consolidation stage: sync downstream thesis or paper sections back to the active canonical source.

## Change Recording Rules

Record a source-of-truth tracker entry when any of the following happens:

1. a section's canonical file changes
2. a figure or table is moved to a different authoritative location
3. experiment results in a paper are superseded by a linked experiment repository
4. thesis markdown and thesis LaTeX stop matching for intentional reasons
5. a paper becomes the reference text for a thesis subsection, or the reverse

## Practical Expectations For Copilot And Collaborators

1. State the canonical file when making substantive edits.
2. Name affected mirrors when they exist.
3. Update the tracker when a handoff occurs.
4. Do not treat generated files in `build/` as editable sources.
5. Do not assume that thesis content always overrides paper content or vice versa.