# Source-of-Truth Tracker

Use this file to record where the canonical version of a topic currently lives and what downstream files still need synchronization.

## Current Registry

| Scope | Current canonical file | Previous canonical file | Mirrors or dependents | Status | Last verified | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Thesis introduction | TBD | TBD | TBD | undecided | TBD | Fill when ownership is agreed |
| Literature review | TBD | TBD | TBD | undecided | TBD | Fill when ownership is agreed |
| Contribution 1 | TBD | TBD | TBD | undecided | TBD | Fill when ownership is agreed |
| Contribution 2 | TBD | TBD | TBD | undecided | TBD | Fill when ownership is agreed |
| Contribution 3 | TBD | TBD | TBD | undecided | TBD | Fill when ownership is agreed |
| Conclusion | TBD | TBD | TBD | undecided | TBD | Fill when ownership is agreed |

## Change Log

Add a new entry whenever the canonical location for a content area changes or when a deliberate divergence is introduced.

| Date | Scope | New canonical file | Previous canonical file | Reason for change | Mirrors or dependents | Sync status | Owner | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| YYYY-MM-DD | Example: Contribution 1 methodology | `thesis/markdown/contribution_1/methodology.md` | `papers/ieee-ras/root.tex` | Drafting moved back to thesis markdown after review feedback | `thesis/latex/contribution_1/methodology.tex`, `papers/ieee-ras/root.tex` | pending | TBD | Replace this example row when first used |

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