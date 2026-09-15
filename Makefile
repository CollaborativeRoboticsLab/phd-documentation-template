SHELL := /usr/bin/env bash

# Usage examples:
#   make build-paper experience-2027
#   make build-paper experience-2027 conference_101719.tex
#   make clean-paper experience-2027
#   make dedupe-paper experience-2027
#   make verify-paper experience-2027
#   make unused-paper experience-2027
#   make build-thesis
#   make wordcount
#   make dedupe
#   make verify
#   make unused
#   make clean
#   make feed-citations thesis
#   make feed-citations paper experience-2027

# Positional arguments are read from MAKECMDGOALS so the command surface stays
# close to a CLI, for example `make build-paper experience-2027`.
COMMAND := $(firstword $(MAKECMDGOALS))
ARG2 := $(word 2,$(MAKECMDGOALS))
ARG3 := $(word 3,$(MAKECMDGOALS))

# Allow ENTRY=<filename> to override the positional entry argument.
ENTRY ?=

# Paper commands use the second argument for the paper directory and the third
# argument for the optional entry file.
PAPER := $(if $(filter build-paper clean-paper dedupe-paper verify-paper unused-paper,$(COMMAND)),$(ARG2),)
PAPER_ENTRY := $(if $(ENTRY),$(ENTRY),$(if $(filter build-paper,$(COMMAND)),$(ARG3),))
PAPER_DIR := papers/$(PAPER)
PAPER_OUTDIR := build/papers/$(PAPER)
PAPER_BIB := $(PAPER_DIR)/references.bib
PAPER_FLAGGED := $(PAPER_DIR)/unresolved_cite.txt

FEED_SCOPE := $(if $(filter feed-citations,$(COMMAND)),$(ARG2),)
FEED_PAPER := $(if $(filter feed-citations,$(COMMAND)),$(ARG3),)
FEED_PAPER_DIR := papers/$(FEED_PAPER)
FEED_BIB := $(if $(filter thesis,$(FEED_SCOPE)),$(THESIS_BIB),$(if $(filter paper,$(FEED_SCOPE)),$(FEED_PAPER_DIR)/references.bib,))

THESIS_DIR := thesis/latex
THESIS_DOC := $(THESIS_DIR)/main.tex
THESIS_OUTDIR := build/thesis/latex
THESIS_BIB := $(THESIS_DIR)/Bibliography.bib

.PHONY: all build-paper build-thesis clean-paper dedupe-paper verify-paper unused-paper wordcount dedupe verify unused clean thesis-wordcount thesis-dedupe thesis-verify thesis-unused thesis-clean thesis-resolve-citations resolve-citations thesis-feed-citations feed-citations thesis-sync-citations sync-citations

all: build-thesis

wordcount: thesis-wordcount

dedupe: thesis-dedupe

verify: thesis-verify

unused: thesis-unused

clean: thesis-clean

# Build one paper into its matching build/papers/<paper-dir> output directory.
build-paper:
	@test -n "$(PAPER)" || { echo "usage: make build-paper <paper-dir>"; exit 1; }
	@test -d "$(PAPER_DIR)" || { echo "missing paper directory: $(PAPER_DIR)"; exit 1; }
	@mkdir -p "$(PAPER_OUTDIR)"
	@doc_path="$$(python3 scripts/select_tex_entry.py --directory "$(PAPER_DIR)" --entry "$(PAPER_ENTRY)")"; \
	  bash scripts/latexmk-outdir.sh -synctex=1 -interaction=nonstopmode -file-line-error -pdf -outdir="$(PAPER_OUTDIR)" "$$doc_path"


# Remove the generated artifacts for one paper directory only.
clean-paper:
	@test -n "$(PAPER)" || { echo "usage: make clean-paper <paper-dir>"; exit 1; }
	@test -d "$(PAPER_OUTDIR)" || { echo "nothing to clean: $(PAPER_OUTDIR)"; exit 1; }
	@rm -rf "$(PAPER_OUTDIR)"
	@echo "removed $(PAPER_OUTDIR)"

dedupe-paper:
	@test -n "$(PAPER)" || { echo "usage: make dedupe-paper <paper-dir>"; exit 1; }
	@test -f "$(PAPER_BIB)" || { echo "missing paper bibliography: $(PAPER_BIB)"; exit 1; }
	@python3 scripts/deduplicate_bib.py "$(PAPER_BIB)"

verify-paper:
	@test -n "$(PAPER)" || { echo "usage: make verify-paper <paper-dir>"; exit 1; }
	@test -f "$(PAPER_BIB)" || { echo "missing paper bibliography: $(PAPER_BIB)"; exit 1; }
	@python3 scripts/verify_citations.py check-bib "$(PAPER_BIB)" --flagged "$(PAPER_FLAGGED)"

unused-paper:
	@test -n "$(PAPER)" || { echo "usage: make unused-paper <paper-dir>"; exit 1; }
	@test -f "$(PAPER_BIB)" || { echo "missing paper bibliography: $(PAPER_BIB)"; exit 1; }
	@python3 scripts/used_citations.py "$(PAPER_BIB)"

# Swallow the paper directory argument so `make build-paper experience-2027`
# treats it as data for the target above instead of as an unknown goal.
%:
	@:

# Build the thesis from thesis/latex/main.tex into build/thesis/latex.
build-thesis:
	@test -d "$(THESIS_DIR)" || { echo "missing thesis directory: $(THESIS_DIR)"; exit 1; }
	@test -f "$(THESIS_DOC)" || { echo "missing thesis entry: $(THESIS_DOC)"; exit 1; }
	@mkdir -p "$(THESIS_OUTDIR)"
	@bash scripts/latexmk-outdir.sh -synctex=1 -interaction=nonstopmode -file-line-error -pdf -outdir="$(THESIS_OUTDIR)" "$(THESIS_DOC)"

# Thesis-focused bibliography maintenance helpers.

thesis-wordcount:
	@texcount -inc -sum "$(THESIS_DOC)"

thesis-dedupe:
	@python3 scripts/deduplicate_bib.py "$(THESIS_BIB)"

thesis-verify:
	@python3 scripts/verify_citations.py check-bib "$(THESIS_BIB)"

thesis-resolve-citations:
	@python3 scripts/verify_citations.py sync-unresolved-markdown "thesis/unresolved_cite.txt" --bib "$(THESIS_BIB)" --flagged "thesis/unresolved_cite.txt" --resolved "thesis/resolved_cite.txt" --prepare-only

resolve-citations: thesis-resolve-citations

thesis-feed-citations:
	@python3 scripts/feed_citations.py "thesis/resolved_cite.txt" --bib "$(THESIS_BIB)"

feed-citations:
	@test -n "$(FEED_SCOPE)" || { echo "usage: make feed-citations thesis | make feed-citations paper <paper-dir>"; exit 1; }
	@if [ "$(FEED_SCOPE)" = "thesis" ]; then \
		python3 scripts/feed_citations.py "thesis/resolved_cite.txt" --bib "$(THESIS_BIB)"; \
	elif [ "$(FEED_SCOPE)" = "paper" ]; then \
		test -n "$(FEED_PAPER)" || { echo "usage: make feed-citations paper <paper-dir>"; exit 1; }; \
		test -d "$(FEED_PAPER_DIR)" || { echo "missing paper directory: $(FEED_PAPER_DIR)"; exit 1; }; \
		python3 scripts/feed_citations.py "thesis/resolved_cite.txt" --bib "$(FEED_BIB)"; \
	else \
		echo "usage: make feed-citations thesis | make feed-citations paper <paper-dir>"; \
		exit 1; \
	fi

thesis-sync-citations:
	@python3 scripts/verify_citations.py sync-unresolved-markdown "thesis/unresolved_cite.txt" --bib "$(THESIS_BIB)" --flagged "thesis/unresolved_cite.txt" --resolved "thesis/resolved_cite.txt" --prepare-only
	@python3 scripts/feed_citations.py "thesis/resolved_cite.txt" --bib "$(THESIS_BIB)"

sync-citations: thesis-sync-citations

thesis-unused:
	@python3 scripts/used_citations.py "$(THESIS_BIB)"

thesis-clean:
	@latexmk -C -outdir="$(THESIS_OUTDIR)" "$(THESIS_DOC)"
