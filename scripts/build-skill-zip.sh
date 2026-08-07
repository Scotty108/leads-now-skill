#!/usr/bin/env bash
# Build the installable skill zip from skills/leads-now/ and stage it into every
# place the site serves it from.
#
# The zip is what a user actually installs, so it drifting behind the skill is a
# silent correctness bug: on 2026-08-07 the served zip was two cycles stale and
# still shipped the healthcare-silted version this project had already fixed.
# Run this after ANY change under skills/leads-now/.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/skills/leads-now"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

# Gate: never ship a skill that fails its own invariants.
python3 "$ROOT/bench/test_invariants.py" --skill ours >/dev/null || {
  echo "REFUSING to build: invariants are red" >&2; exit 1; }

mkdir -p "$STAGE/leads-now"
# Copy the skill only — no bench, no runs, no scratch. What ships is what a
# reviewer reads.
for item in SKILL.md references scripts assets; do
  [ -e "$SRC/$item" ] && cp -R "$SRC/$item" "$STAGE/leads-now/"
done
find "$STAGE" \( -name '__pycache__' -o -name '.DS_Store' -o -name '*.pyc' \) \
  -exec rm -rf {} + 2>/dev/null || true

OUT="$STAGE/leads-now-skill.zip"
( cd "$STAGE" && zip -qr "$OUT" leads-now )
SHA="$(shasum -a 256 "$OUT" | awk '{print $1}')"

for dest in "$ROOT/dist/skill/download" \
            "$ROOT/leads-now-skill/public/download" \
            "$ROOT/leads-now-skill/out/download"; do
  [ -d "$dest" ] || continue
  cp "$OUT" "$dest/leads-now-skill.zip"
  printf '%s  leads-now-skill.zip\n' "$SHA" > "$dest/leads-now-skill.zip.sha256"
  echo "staged -> $dest"
done

echo
echo "files: $(unzip -l "$OUT" | tail -1 | awk '{print $2}')"
echo "sha256: $SHA"
