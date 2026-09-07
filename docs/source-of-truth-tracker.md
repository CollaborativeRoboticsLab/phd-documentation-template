# Source-of-Truth Tracker

Use this file to record where the canonical version of a topic currently lives and what downstream files still need synchronization.

## Current Registry

| Scope | Current canonical file | Previous canonical file | Mirrors or dependents | Status | Last verified | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Thesis introduction | `thesis/latex/introduction/` | TBD | `thesis/markdown/introduction/`, `thesis/markdown/introduction.md` | pending | 2026-08-31 | Thesis introduction currently lives in the LaTeX section files |
| Literature review | `thesis/markdown/literature/` | TBD | `thesis/latex/literature/`, `papers/gpsfsm-2026/conference_101719.tex` | pending | 2026-09-07 | Markdown literature folder is the active thesis-facing canonical source, with chapter content distributed across focused subsection files |
| Contribution 1 | `thesis/markdown/contribution_1/` | `papers/capabilities2-2025/conference_101719.tex` | `thesis/latex/contribution_1/`, `papers/capabilities2-2025/conference_101719.tex`, `papers/gpsfsm-2026/conference_101719.tex` | pending | 2026-09-07 | Markdown chapter folder is now the thesis-facing canonical source after consolidating paper material and additional literature review subsections gathered over time |
| Contribution 2 | `thesis/markdown/contribution_2/` | TBD | `thesis/latex/contribution_2/`, `papers/gpsfsm-2026/conference_101719.tex` | pending | 2026-09-07 | Markdown chapter folder is the canonical consolidated source, including pulled text from LaTeX and paper drafts plus later literature-review additions stored as numbered subsection files |
| Contribution 3 | TBD | TBD | TBD | undecided | 2026-08-31 | Not started yet |
| Conclusion | TBD | TBD | TBD | undecided | 2026-08-31 | Not started yet |
| GPSFSM 2026 experiment content | `paper-experiments/gpsfsm-2026/README.md` | TBD | `paper-experiments/gpsfsm-2026/docs/index.html`, `papers/gpsfsm-2026/conference_101719.tex` | pending | 2026-08-31 | Repository root README recorded as the canonical experiment entry point |
| GPSFSM 2026 paper | `papers/gpsfsm-2026/conference_101719.tex` | TBD | `thesis/markdown/contribution_2/`, `thesis/latex/contribution_2/`, `paper-experiments/gpsfsm-2026/README.md` | pending | 2026-08-31 | Canonical manuscript source declared for the 2026 GPSFSM paper |
| Capabilities2 2025 paper | `papers/capabilities2-2025/conference_101719.tex` | TBD | `papers/capabilities2-2025/references.bib`, `papers/capabilities2-2025/bibliography.bib` | pending | 2026-08-31 | Canonical manuscript source declared for the 2025 Capabilities2 paper |

## Change Log

Add a new entry whenever the canonical location for a content area changes or when a deliberate divergence is introduced.

| Date | Scope | New canonical file | Previous canonical file | Reason for change | Mirrors or dependents | Sync status | Owner | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-08-31 | Thesis introduction | `thesis/latex/introduction/` | TBD | Initial source-of-truth declaration for the introduction section | `thesis/markdown/introduction/`, `thesis/markdown/introduction.md` | pending | user | LaTeX is the current drafting home for the thesis introduction |
| 2026-08-31 | Literature review | TBD | TBD | Recorded currently available source material while canonical ownership remains unresolved | `thesis/latex/literature/`, `thesis/markdown/literature/`, `papers/gpsfsm-2026/conference_101719.tex` | undecided | user | Literature review content is currently split across thesis LaTeX, thesis markdown, and the GPSFSM paper |
| 2026-09-07 | Literature review | `thesis/markdown/literature/` | TBD | Declared the markdown literature folder as the active thesis-facing source of truth after consolidating long-form review material into focused subsection files | `thesis/latex/literature/`, `papers/gpsfsm-2026/conference_101719.tex` | pending | user | Focused markdown subsection files are intentional canonical chapter content rather than temporary fragments |
| 2026-08-31 | Contribution 1 | TBD | TBD | Recorded current source material and noted outdated thesis LaTeX copy | `papers/capabilities2-2025/conference_101719.tex`, `papers/gpsfsm-2026/conference_101719.tex`, `thesis/latex/contribution_1/` | undecided | user | Contribution 1 content currently comes from the two paper drafts; the thesis LaTeX version is outdated |
| 2026-09-04 | Contribution 1 | `papers/capabilities2-2025/conference_101719.tex` | TBD | Declared the finalized Capabilities2 paper as the canonical source for Contribution 1 and synchronized the thesis markdown chapter from it | `thesis/markdown/contribution_1/`, `thesis/latex/contribution_1/`, `papers/gpsfsm-2026/conference_101719.tex` | pending | Copilot | Thesis markdown now reflects the paper; the thesis LaTeX chapter and related paper surfaces remain to be checked |
| 2026-09-04 | Contribution 1 | `papers/capabilities2-2025/conference_101719.tex` | TBD | Consolidated GPSFSM paper material related to Fabric, PromptTools, and Capabilities2 runtime modifications, together with retained thesis LaTeX material, into the thesis markdown chapter | `thesis/markdown/contribution_1/`, `thesis/latex/contribution_1/`, `papers/gpsfsm-2026/conference_101719.tex` | pending | Copilot | Canonical ownership did not change; the markdown chapter now acts as the consolidated thesis-facing view of Contribution 1 |
| 2026-09-07 | Contribution 1 | `thesis/markdown/contribution_1/` | `papers/capabilities2-2025/conference_101719.tex` | Declared the markdown chapter folder as the active thesis-facing source of truth after additional consolidation and subsection-based literature organization in the repo | `thesis/latex/contribution_1/`, `papers/capabilities2-2025/conference_101719.tex`, `papers/gpsfsm-2026/conference_101719.tex` | pending | user | Numbered markdown subsection files are intentional chapter content slices rather than temporary notes |
| 2026-08-31 | Contribution 3 | TBD | TBD | Recorded current project status | TBD | undecided | user | Section not started yet |
| 2026-08-31 | Conclusion | TBD | TBD | Recorded current project status | TBD | undecided | user | Section not started yet |
| 2026-08-31 | Contribution 2 | `thesis/markdown/contribution_2/` | TBD | Initial source-of-truth declaration for the thesis contribution section | `thesis/latex/contribution_2/` | pending | user | Section-level ownership spans multiple markdown files in this directory |
| 2026-09-07 | Contribution 2 | `thesis/markdown/contribution_2/` | TBD | Confirmed the markdown chapter folder as the active source of truth after importing material from LaTeX and paper drafts and renaming subsection files to the correct `literature_xx` scheme | `thesis/latex/contribution_2/`, `papers/gpsfsm-2026/conference_101719.tex` | pending | user | Numbered markdown subsection files are intended as the real chapter subsections; markdown cross-links were updated after the filename mismatch fix |
| 2026-08-31 | GPSFSM 2026 experiment content | `paper-experiments/gpsfsm-2026/README.md` | TBD | Initial source-of-truth declaration for the experiment repository content | `paper-experiments/gpsfsm-2026/docs/index.html`, `papers/gpsfsm-2026/conference_101719.tex` | pending | user | README is used as the canonical repository entry point |
| 2026-08-31 | GPSFSM 2026 paper | `papers/gpsfsm-2026/conference_101719.tex` | TBD | Initial source-of-truth declaration for the paper manuscript | `thesis/markdown/contribution_2/`, `thesis/latex/contribution_2/`, `paper-experiments/gpsfsm-2026/README.md` | pending | user | Mirrors and derived summaries still need reconciliation against the paper draft |
| 2026-08-31 | Capabilities2 2025 paper | `papers/capabilities2-2025/conference_101719.tex` | TBD | Initial source-of-truth declaration for the paper manuscript | `papers/capabilities2-2025/references.bib`, `papers/capabilities2-2025/bibliography.bib` | pending | user | Bibliography files are tracked as immediate manuscript dependents |

## Status Values

Use one of these values in the registry and log:

| Status | Meaning |
| --- | --- |
| `aligned` | Canonical file and mirrors are in sync |
| `pending` | Canonical file changed and mirrors still need updates |
| `diverged-intentionally` | Differences are expected and documented |
| `undecided` | Canonical file has not been formally chosen |

## Update Procedure

1. Identify the content scope that changed.
2. Set or update the current canonical file in the registry.
3. Add a dated row to the change log.
4. List downstream files that need updates.
5. Mark the status as `aligned` only after those files have been checked.