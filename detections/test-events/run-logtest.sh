#!/usr/bin/env bash
# Replay test events through the running Wazuh manager rule engine.
# Run from anywhere after the Wazuh stack is up.
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR/../.."   # repo root (compose project dir)

echo "=== SSH brute-force replay (expect rule id 100100, level 12) ==="
docker compose exec -T wazuh.manager /var/ossec/bin/wazuh-logtest -v < "$DIR/ssh_bruteforce.log"

echo
echo "=== Suspicious PowerShell replay (expect rule id 100200, level 13) ==="
docker compose exec -T wazuh.manager /var/ossec/bin/wazuh-logtest -v < "$DIR/powershell_sysmon.json"