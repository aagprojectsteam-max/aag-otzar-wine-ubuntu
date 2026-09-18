#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

fail=0
echo '== forbidden file extensions ==' 
while IFS= read -r -d '' f; do
  echo "FORBIDDEN_FILE=$f"
  fail=1
done < <(find . -path './.git' -prune -o -path './.build' -prune -o -type f \( -name '*.db' -o -name '*.sqlite' -o -name '*.sqlite3' -o -name '*.asar' -o -name '*.exe' -o -name '*.dll' -o -name '*.node' \) -print0)

echo '== personal / secret patterns ==' 
patterns=(
  '/home/aag-linux'
  'aag.projects.team@gmail.com'
  'gho_[A-Za-z0-9]+'
  'sk-[A-Za-z0-9]+'
  '-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----'
)
for pattern in "${patterns[@]}"; do
  if grep -RInE --exclude-dir=.git --exclude-dir=.build --exclude=public-scan.sh -- "$pattern" .; then
    fail=1
  fi
done

echo '== large tracked candidates ==' 
find . -path './.git' -prune -o -path './.build' -prune -o -type f -size +5M -print

if (( fail )); then
  echo PUBLIC_SCAN=FAIL >&2
  exit 1
fi
echo PUBLIC_SCAN=PASS
