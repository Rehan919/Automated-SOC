#!/usr/bin/env bash
# Apply the 30-day hot-retention ISM policy to the Wazuh indexer. Run from repo root.
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; . ./.env; set +a
curl -sk -u "${INDEXER_USERNAME}:${INDEXER_PASSWORD}" -X PUT \
  "https://127.0.0.1:9200/_plugins/_ism/policies/soc-lab-retention" \
  -H 'Content-Type: application/json' \
  --data-binary @retention/ism-policy.json
echo
echo "[+] ISM policy applied. New wazuh-alerts-* indices will adopt it (30d hot -> delete)."