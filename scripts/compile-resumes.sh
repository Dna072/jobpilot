#!/usr/bin/env bash
# Compile the three JobPilot master resumes with the same engine JobPilot uses.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENGINE="$(command -v tectonic || true)"
if [[ -z "$ENGINE" ]]; then
  ENGINE="$(command -v pdflatex || true)"
fi
if [[ -z "$ENGINE" ]]; then
  ENGINE="$(command -v xelatex || true)"
fi
if [[ -z "$ENGINE" ]]; then
  echo "Install tectonic or pdflatex (texlive with FiraSans + fontawesome)." >&2
  exit 1
fi

compile_one() {
  local tex="$1"
  local dest
  dest="$(dirname "$tex")"
  echo "Compiling $tex"
  if [[ "$(basename "$ENGINE")" == "tectonic" ]]; then
    "$ENGINE" -X compile "$tex" --outdir "$dest"
  else
    "$ENGINE" -interaction=nonstopmode -output-directory "$dest" "$tex"
    "$ENGINE" -interaction=nonstopmode -output-directory "$dest" "$tex"
  fi
}

compile_one "$ROOT/cv/data-engineer/master.tex"
compile_one "$ROOT/cv/backend-engineer/master.tex"
compile_one "$ROOT/cv/frontend-engineer/master.tex"
echo "Done."
