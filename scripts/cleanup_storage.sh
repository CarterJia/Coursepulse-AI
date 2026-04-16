#!/bin/sh
set -eu

ROOT="${FILE_STORAGE_ROOT:-/app/storage}"

for sub in slides assignments derived; do
  dir="$ROOT/$sub"
  if [ -d "$dir" ]; then
    find "$dir" -type f -mtime +7 -delete 2>/dev/null || true
    find "$dir" -type d -empty -delete 2>/dev/null || true
  fi
done

echo "[cleanup] Storage cleanup complete. Root: $ROOT"
