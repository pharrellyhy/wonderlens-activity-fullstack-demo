#!/usr/bin/env bash
# Generate one flat-Nordic activity asset via Codex imagegen and copy it to a target path.
# Captures the new ~/.codex/generated_images dir by before/after diff to avoid the newest-dir race.
# Usage: gen_beat.sh <dest_png_path> <prompt_file>
set -euo pipefail

DEST="$1"
PROMPT_FILE="$2"
STYLE_REF="/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/prompts/style-reference-flat-nordic.png"
GEN_DIR="$HOME/.codex/generated_images"

mkdir -p "$GEN_DIR" "$(dirname "$DEST")"
BEFORE="$(mktemp)"; AFTER="$(mktemp)"
ls -1 "$GEN_DIR" 2>/dev/null | sort > "$BEFORE"

codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox -i "$STYLE_REF" < "$PROMPT_FILE" >/tmp/codex_gen.log 2>&1 || { echo "CODEX_FAIL"; tail -5 /tmp/codex_gen.log; exit 3; }

ls -1 "$GEN_DIR" 2>/dev/null | sort > "$AFTER"
NEW_DIRS="$(comm -13 "$BEFORE" "$AFTER")"
rm -f "$BEFORE" "$AFTER"
if [ -z "$NEW_DIRS" ]; then echo "NO_NEW_DIR"; exit 4; fi

# pick the newest produced png among new dirs
SRC_PNG=""
while IFS= read -r d; do
  [ -z "$d" ] && continue
  for p in "$GEN_DIR/$d"/*.png; do [ -f "$p" ] && SRC_PNG="$p"; done
done <<< "$NEW_DIRS"
if [ -z "$SRC_PNG" ]; then echo "NO_PNG"; exit 5; fi

# normalize to 512x512 PNG
python3 - "$SRC_PNG" "$DEST" <<'PY'
import sys
from PIL import Image
src, dest = sys.argv[1], sys.argv[2]
im = Image.open(src).convert("RGB")
if im.size != (512, 512):
    im = im.resize((512, 512), Image.LANCZOS)
im.save(dest, "PNG")
print(f"OK {dest} <- {src}")
PY
