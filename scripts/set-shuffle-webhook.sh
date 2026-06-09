#!/usr/bin/env bash
# Replace the Shuffle webhook placeholder in the manager ossec.conf with
# SHUFFLE_WEBHOOK_URL from .env. Run from repo root, then restart the manager.
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] || { echo "ERROR: .env not found"; exit 1; }
set -a; . ./.env; set +a
CONF="wazuh/config/wazuh_cluster/wazuh_manager.conf"
[ -n "${SHUFFLE_WEBHOOK_URL:-}" ] || { echo "ERROR: SHUFFLE_WEBHOOK_URL unset in .env"; exit 1; }
sed -i "s|http://shuffle-backend:5001/api/v1/hooks/webhook_REPLACE_ME|${SHUFFLE_WEBHOOK_URL}|g" "$CONF"
echo "[+] webhook set. Restart the manager: docker compose restart wazuh.manager"