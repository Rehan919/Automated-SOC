# Task 11: Approval gate, active response & safety database

## Flow (in the Shuffle workflow, after the case is enriched)
1. **Gate on verdict:** branch only when Cortex enrichment marks the IP malicious
   (e.g. AbuseIPDB confidence high or VirusTotal positives > 0).
2. **Approval (human-in-the-loop):** add a Shuffle **User Input** node configured
   to email `ANALYST_EMAIL` with Approve / Deny links. The workflow PAUSES here.
3. **On Approve:** run `scripts/active_response.py`:
   ```
   python3 scripts/active_response.py --ip <srcip> --agent-id <id> \
       --incident-id <case_id> --approved-by <analyst>
   ```
   - Refuses any IP on `RESPONSE_ALLOWLIST` (exact IP or CIDR).
   - Calls the Wazuh API `firewall-drop` active response on the target agent
     (iptables DROP of the source IP).
   - Writes an auditable row to `scripts/responses.db`.
4. **On Deny:** log only (no block, no DB row beyond the audit comment).
5. **Notify:** Shuffle posts the outcome back to the analyst / TheHive case.

## Active-response registration
`ossec.conf` registers `firewall-drop` with `rules_id 999999` (never matches ->
never auto-fires) and `timeout 600` (auto-unblock after 10 min, defense in depth).

## Accountability database (scripts/responses.db, SQLite)
Columns: `timestamp, incident_id, action, target, approved_by, rollback_command`.
Actions seen: `firewall-drop`, `block-skipped-allowlist`, `block-dry-run`.

## Manual rollback / unblock
```
python3 scripts/unblock.py --list                 # history
python3 scripts/unblock.py --incident-id case~123 # undo by incident
python3 scripts/unblock.py --ip 45.155.205.99     # undo by IP
```

## Safety notes
- Destructive action is gated behind explicit human approval.
- Critical infrastructure is protected via `RESPONSE_ALLOWLIST`.
- Every block is attributable (who approved, when) and reversible (rollback cmd).