#!/usr/bin/env bash
# Cold archive: compress Wazuh alerts to immutable, hash-verified, metadata-tagged
# files under /archive/YYYY/Month/<timestamp>/ (logs.json.gz + manifest.sha256 + metadata.json).
set -euo pipefail
SRC="${SRC:-/wazuh-logs/alerts/alerts.json}"
OUT_BASE="${OUT_BASE:-/archive}"
if [ ! -f "$SRC" ]; then echo "[archive] source not found: $SRC (is logging enabled?)"; exit 0; fi

NOW_DATE="$(date -u +%Y-%m-%d)"
YEAR="$(date -u +%Y)"; MONTH="$(date -u +%B)"; STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DEST="${OUT_BASE}/${YEAR}/${MONTH}/${STAMP}"
mkdir -p "$DEST"

EVENTS="$(wc -l < "$SRC" | tr -d ' ')"
gzip -c "$SRC" > "${DEST}/logs.json.gz"
HASH="$(sha256sum "${DEST}/logs.json.gz" | awk '{print $1}')"
echo "${HASH}  logs.json.gz" > "${DEST}/manifest.sha256"
cat > "${DEST}/metadata.json" <<EOF
{
  "export_date": "${NOW_DATE}",
  "source": "wazuh-manager",
  "source_file": "${SRC}",
  "archived_file": "logs.json.gz",
  "events": ${EVENTS},
  "compression": "gzip",
  "hash": "sha256",
  "sha256": "${HASH}"
}
EOF
# Approximate WORM: read-only. For real object storage use S3 Object Lock (see README).
chmod 0444 "${DEST}/logs.json.gz" "${DEST}/manifest.sha256" "${DEST}/metadata.json"
echo "[archive] ${EVENTS} events -> ${DEST}/logs.json.gz (sha256 ${HASH})"