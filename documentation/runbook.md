# SOC Automation Lab v2 -- Runbook

## A. One-time prep
1. `documentation/prerequisites.md` (Docker Desktop + WSL2, copy `.wslconfig`, `wsl --shutdown`).
2. Secrets:
   ```
   copy .env.example .env                 # fill every CHANGE_ME
   copy shuffle\.env.example shuffle\.env  # fill every CHANGE_ME
   ```
3. Wazuh certs (once):
   ```
   docker compose -f wazuh/generate-indexer-certs.yml run --rm generator
   ```
4. Rotate Wazuh default passwords to match .env (once, before first boot):
   ```
   bash scripts/wazuh-change-passwords.sh
   ```

## B. Bring-up order
The whole lab: `docker compose up -d` (uses include of all components). For a
controlled first boot, bring tiers up in order and wait for healthy each time:
```
docker compose up -d wazuh.indexer wazuh.manager wazuh.dashboard
docker compose up -d ubuntu-ssh-target
docker compose up -d cortex-elasticsearch cortex
docker compose up -d cassandra elasticsearch            # TheHive backends
docker compose up -d shuffle-opensearch shuffle-backend shuffle-frontend shuffle-orborus
docker compose ps        # confirm health
```

## C. First-boot configuration (the cross-component keys)
1. **Cortex** (http://127.0.0.1:9001): create superadmin + org `soc-lab`; enable
   VirusTotal_GetReport_3_1 + AbuseIPDB_1_0 with keys from .env; create an API
   key -> set `CORTEX_API_KEY` in `.env`. (cortex/README.md)
2. **TheHive**: `docker compose up -d thehive` (now CORTEX_API_KEY is set).
   Login admin@thehive.local/secret -> change password; create org + API key
   -> set `THEHIVE_API_KEY` in `.env`; verify Cortex server is green; add the
   RunAnalyzer notification on `ip` observables. (thehive/cortex-integration.md)
3. **Shuffle** (http://127.0.0.1:3001): add a Webhook trigger -> set
   `SHUFFLE_WEBHOOK_URL` in `.env`; run `bash scripts/set-shuffle-webhook.sh`
   then `docker compose restart wazuh.manager`. Build the workflow:
   Webhook -> Run Python (shuffle/workflows/thehive_case.py) -> User Input
   (approval) -> Run Python (scripts/active_response.py) -> notify.
   (shuffle/workflows/README.md, documentation/approval-and-response.md)
4. **Retention**: `bash retention/apply-ism-policy.sh`.
5. **Windows endpoint**: endpoints/windows-sysmon/README.md.

## D. Demo / validation
```
bash scripts/run-scenario.sh
```
Drives the SSH brute force and asserts each hop. Secondary scenario: trigger a
suspicious PowerShell on the Windows endpoint (rule 100200).

## E. Operations
- Detection logic test:  `bash detections/test-events/run-logtest.sh`
- Response history:      `python3 scripts/unblock.py --list`
- Unblock an IP:         `python3 scripts/unblock.py --ip <ip>`
- Cold archive (manual): `docker compose run --rm retention /archive.sh`
- Config/secret backup:  `bash backups/backup.sh`

## F. Teardown
```
docker compose down              # keep data volumes
docker compose down -v           # WIPE all data (destructive)
```