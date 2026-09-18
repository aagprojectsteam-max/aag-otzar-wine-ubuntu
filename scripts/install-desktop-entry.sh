#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FINAL_ROOT="${1:?Usage: install-desktop-entry.sh /absolute/final/root}"
case "$FINAL_ROOT" in /*) ;; *) echo "FINAL_ROOT must be absolute" >&2; exit 2;; esac
DEST="$HOME/.local/share/applications/aag-otzar-wine.desktop"
mkdir -p "$(dirname "$DEST")"
sed "s#@@FINAL_ROOT@@#$FINAL_ROOT#g" "$ROOT/templates/aag-otzar-wine.desktop.in" > "$DEST"
chmod 644 "$DEST"
update-desktop-database "$HOME/.local/share/applications" >/dev/null 2>&1 || true
echo "INSTALLED=$DEST"
