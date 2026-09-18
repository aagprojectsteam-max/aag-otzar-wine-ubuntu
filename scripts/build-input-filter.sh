#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${1:-$ROOT/build/input-filter.exe}"
mkdir -p "$(dirname "$OUT")"
command -v x86_64-w64-mingw32-gcc >/dev/null
x86_64-w64-mingw32-gcc -O2 -Wall -Wextra \
  "$ROOT/src/input-filter.c" -o "$OUT" -luser32 -lkernel32
echo "BUILT=$OUT"
sha256sum "$OUT"
