#!/usr/bin/env bash
set -euo pipefail

: "${MIHOMO_BIN:=mihomo}"
mkdir -p output/domain output/ip
for file in data/domain/*.txt; do
  name="${file##*/}"; name="${name%.txt}"
  "$MIHOMO_BIN" convert-ruleset domain text "$file" "output/domain/${name}.mrs"
done
for file in data/ip/*.txt; do
  name="${file##*/}"; name="${name%.txt}"
  "$MIHOMO_BIN" convert-ruleset ipcidr text "$file" "output/ip/${name}.mrs"
done
