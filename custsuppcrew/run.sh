#!/usr/bin/env bash
# Run custsuppcrew with this project's .venv (avoids parent AAMD-main/.venv mismatch).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# Drop a wrong outer venv / conda-exported VIRTUAL_ENV before activating ours.
unset VIRTUAL_ENV
# shellcheck disable=SC1091
source "$ROOT/.venv/bin/activate"

if [[ ! -x "$ROOT/.venv/bin/crewai" ]]; then
  echo "Project .venv missing crewai. Run: crewai install" >&2
  exit 1
fi

exec "$ROOT/.venv/bin/crewai" run "$@"
