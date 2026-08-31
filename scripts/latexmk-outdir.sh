#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -eq 0 ]]; then
  echo "usage: latexmk-outdir.sh [latexmk args ...] <document>" >&2
  exit 1
fi

doc_path="${!#}"
outdir=""
latexmk_args=()

for arg in "$@"; do
  case "$arg" in
    -outdir=*)
      outdir="${arg#-outdir=}"
      ;;
  esac
done

if [[ -z "$outdir" ]]; then
  echo "latexmk-outdir.sh: missing -outdir argument" >&2
  exit 1
fi

doc_dir="$(cd "$(dirname "$doc_path")" && pwd)"
doc_file="$(basename "$doc_path")"

if [[ "$outdir" = /* ]]; then
  outdir_abs="$outdir"
else
  outdir_abs="$(cd "$PWD" && pwd)/$outdir"
fi

mkdir -p "$outdir_abs"

while IFS= read -r rel_dir; do
  [[ -z "$rel_dir" ]] && continue
  mkdir -p "$outdir_abs/$rel_dir"
done < <(cd "$doc_dir" && find . -type d -printf '%P\n')

for arg in "${@:1:$(($# - 1))}"; do
  case "$arg" in
    -outdir=*)
      latexmk_args+=("-outdir=$outdir_abs")
      ;;
    *)
      latexmk_args+=("$arg")
      ;;
  esac
done

cd "$doc_dir"
exec latexmk "${latexmk_args[@]}" "$doc_file"