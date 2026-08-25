#!/usr/bin/env bash
#
# upload_pdfs.sh — stage the raw Bosch PDFs into their two MANAGED UC Volumes.
#
#   etl/data/manuals/*.pdf     -> /Volumes/$CATALOG/$SCHEMA/productmanuals/  (KA source)
#   etl/data/datasheets/*.pdf  -> /Volumes/$CATALOG/$SCHEMA/datasheets/      (IDP source)
#
# Idempotent: uses `databricks fs cp --overwrite`, so re-running restages the
# same files in place (no duplicates, no renaming — kebab filenames are kept
# exactly, e.g. gsr-18v-55.pdf). Safe to run before every KA re-sync / IDP
# full-refresh. Requires the two Volumes to already exist (bundle deploy).
#
# Usage (locked to the FEVM profile):
#   scripts/upload_pdfs.sh                       # FEVM defaults
#   CATALOG=... SCHEMA=... scripts/upload_pdfs.sh
#   scripts/upload_pdfs.sh FEVM <catalog> <schema> <manuals_volume> <datasheets_volume>
set -euo pipefail

# Repo root = parent of this script's dir, so source paths resolve regardless
# of the caller's cwd.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PROFILE="${1:-${PROFILE:-FEVM}}"
CATALOG="${2:-${CATALOG:-nikks_fevm_workspace_7405607030687545}}"
SCHEMA="${3:-${SCHEMA:-techsummit}}"
VOLUME_MANUALS="${4:-${VOLUME_MANUALS:-productmanuals}}"
VOLUME_DATASHEETS="${5:-${VOLUME_DATASHEETS:-datasheets}}"

# Guardrail: this demo is hard-locked to the FEVM profile.
if [[ "${PROFILE,,}" != "fevm" ]]; then
  echo "ERROR: this script is locked to the FEVM profile (got PROFILE=$PROFILE)" >&2
  exit 1
fi

# Guardrail: this demo only ever touches techsummit, never cdp (case-insensitive).
if [[ "${SCHEMA,,}" == "cdp" || "${CATALOG,,}" == *cdp* ]]; then
  echo "ERROR: refusing to touch cdp (catalog=$CATALOG schema=$SCHEMA)" >&2
  exit 1
fi

upload_dir() {
  local src_dir="$1" volume="$2" label="$3"
  local dest="dbfs:/Volumes/${CATALOG}/${SCHEMA}/${volume}"
  echo "==> ${label}: ${src_dir}/*.pdf -> ${dest}/"
  local count=0
  shopt -s nullglob
  for pdf in "${src_dir}"/*.pdf; do
    local base
    base="$(basename "$pdf")"
    echo "    cp ${base}"
    databricks fs cp --overwrite "$pdf" "${dest}/${base}" -p "$PROFILE"
    count=$((count + 1))
  done
  shopt -u nullglob
  if [[ "$count" -eq 0 ]]; then
    echo "ERROR: no PDFs found in ${src_dir}" >&2
    exit 1
  fi
  echo "    ${count} file(s) staged to ${volume}."
}

echo "Profile=${PROFILE} Catalog=${CATALOG} Schema=${SCHEMA}"
upload_dir "${REPO_ROOT}/etl/data/manuals"    "${VOLUME_MANUALS}"    "manuals"
upload_dir "${REPO_ROOT}/etl/data/datasheets" "${VOLUME_DATASHEETS}" "datasheets"
echo "Done."
