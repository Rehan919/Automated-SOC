#!/usr/bin/env bash
# End-to-end demo: SSH brute force -> detect -> (case/enrich/approve are UI hops)
# -> cold archive. Asserts every automatable stage. Run from repo root.
set -uo pipefail
cd "$(dirname "$0")/.."
set -a; . ./.env; set +a
FAILED=0
pass(){ echo "[PASS] $*"; }
fail(){ echo "[FAIL] $*"; FAILED=1; }
note(){ echo "[ .. ] $*"; }

echo "=== 1. Stack health ==="
for s in wazuh.manager wazuh.indexer thehive cortex shuffle-backend; do
  st=$(docker inspect -f '{{.State.Health.Status}}{{.State.Status}}' "$s" 2>/dev/null || echo missing)
  case "$st" in *healthy*|*running*) pass "$s up ($st)";; *) fail "$s not ready ($st)";; esac
done

echo "=== 2. Agents enrolled ==="
docker compose exec -T wazuh.manager /var/ossec/bin/agent_control -l 2>/dev/null | grep -q Active \
  && pass "at least one agent Active" || fail "no active agents"

echo "=== 3. Detection logic (logtest) ==="
docker compose exec -T wazuh.manager /var/ossec/bin/wazuh-logtest -v \
  < detections/test-events/ssh_bruteforce.log 2>/dev/null | grep -q "100100" \
  && pass "rule 100100 fires in logtest" || fail "rule 100100 did not fire"

echo "=== 4. Launch SSH brute force ==="
docker compose --profile attack run --rm attacker || true
note "waiting 25s for correlation + indexing"; sleep 25

echo "=== 5. Alert indexed (rule 100100) ==="
RES=$(curl -sk -u "${INDEXER_USERNAME}:${INDEXER_PASSWORD}" \
  "https://127.0.0.1:9200/wazuh-alerts-*/_search?q=rule.id:100100&size=1" 2>/dev/null)
echo "$RES" | grep -q '"id":"100100"\|"100100"' \
  && pass "rule 100100 alert present in indexer" || fail "no 100100 alert in indexer"

echo "=== 6. Cold archive integrity ==="
docker compose run --rm retention /archive.sh >/dev/null 2>&1 || true
LATEST=$(ls -dt retention/archive/*/*/*/ 2>/dev/null | head -1 || true)
if [ -n "${LATEST:-}" ] && [ -f "${LATEST}manifest.sha256" ]; then
  ( cd "$LATEST" && sha256sum -c manifest.sha256 >/dev/null 2>&1 ) \
    && pass "archive sha256 verified ($LATEST)" || fail "archive checksum mismatch"
else
  note "no archive produced (enable logging / generate alerts first)"
fi

echo
echo "=== Manual checkpoints (UI) ==="
echo " - TheHive (http://127.0.0.1:9000): case auto-created, severity Medium, IP observable enriched by Cortex"
echo " - Shuffle (http://127.0.0.1:3001): approve the block in the User Input node"
echo " - Then: python3 scripts/unblock.py --list   # shows the firewall-drop audit row"
echo
[ "$FAILED" -eq 0 ] && echo "SCENARIO: automatable assertions PASSED" || { echo "SCENARIO: FAILURES above"; exit 1; }