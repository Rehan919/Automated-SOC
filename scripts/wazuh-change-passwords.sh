#!/usr/bin/env bash
# Rotate Wazuh indexer/dashboard/API default passwords to match .env.
# Run from the repo root BEFORE the first `docker compose up`:
#   bash scripts/wazuh-change-passwords.sh
# To re-apply against an already-running indexer, add: --apply
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] || { echo "ERROR: .env not found (copy .env.example -> .env first)"; exit 1; }
set -a; . ./.env; set +a

IMG="wazuh/wazuh-indexer:4.9.2"
IU="wazuh/config/wazuh_indexer/internal_users.yml"
WY="wazuh/config/wazuh_dashboard/wazuh.yml"

hash_pw() { # bcrypt hash via the indexer image
  docker run --rm "$IMG" \
    bash /usr/share/wazuh-indexer/plugins/opensearch-security/tools/hash.sh -p "$1" \
    | tail -n1
}

echo "[*] Generating bcrypt hashes..."
ADMIN_HASH="$(hash_pw "$INDEXER_PASSWORD")"
KIBANA_HASH="$(hash_pw "$DASHBOARD_PASSWORD")"

echo "[*] Writing $IU ..."
cat > "$IU" <<EOF
---
_meta:
  type: "internalusers"
  config_version: 2

admin:
  hash: "$ADMIN_HASH"
  reserved: true
  backend_roles:
    - "admin"
  description: "Wazuh indexer admin"

kibanaserver:
  hash: "$KIBANA_HASH"
  reserved: true
  description: "Wazuh dashboard server user"
EOF

echo "[*] Syncing API password into $WY ..."
sed -i "s|WAZUH_API_PASSWORD_PLACEHOLDER|$WAZUH_API_PASSWORD|g" "$WY"

if [ "${1:-}" = "--apply" ]; then
  echo "[*] Applying security config to running indexer..."
  docker compose cp "$IU" wazuh.indexer:/usr/share/wazuh-indexer/opensearch-security/internal_users.yml
  docker compose exec wazuh.indexer bash -c '\
    export JAVA_HOME=/usr/share/wazuh-indexer/jdk && \
    /usr/share/wazuh-indexer/plugins/opensearch-security/tools/securityadmin.sh \
      -cd /usr/share/wazuh-indexer/opensearch-security/ \
      -nhnv -cacert /usr/share/wazuh-indexer/certs/root-ca.pem \
      -cert /usr/share/wazuh-indexer/certs/admin.pem \
      -key /usr/share/wazuh-indexer/certs/admin-key.pem -icl'
fi
echo "[+] Done. Passwords now match .env. (On a fresh volume they apply on first boot.)"