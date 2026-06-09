# Shuffle workflow: SSH brute force / suspicious PowerShell -> TheHive

This folder holds the workflow logic as portable Python so it is testable and
reviewable. Build the workflow in the Shuffle UI as follows.

## 1. Webhook trigger (Task 9)
- Add a **Webhook** trigger. Copy its URL.
- Put it in the root `.env` as `SHUFFLE_WEBHOOK_URL`, then run
  `bash scripts/set-shuffle-webhook.sh` and `docker compose restart wazuh.manager`.
  Wazuh now POSTs every alert (level >= 7) to this webhook.

## 2. Create / update TheHive case (Task 10)
- Add a **Run Python** action (Shuffle Tools -> execute_python) containing
  `thehive_case.py` (this folder).
- Provide `THEHIVE_URL` (http://thehive:9000) and `THEHIVE_API_KEY` to the action
  (Shuffle org/workflow variables; inject into the code or os.environ).
- Input: the webhook body (`$exec`), passed to the script on stdin.

### Severity mapping (Wazuh level -> TheHive severity)
| Wazuh level | TheHive severity |
|---|---|
| 7-9   | 1 Low |
| 10-12 | 2 Medium |
| 13-15 | 4 Critical |

### Dedup
Open cases are tagged `dedup:<key>` where `key` = source IP (if present) else
`<agent>:<rule_id>`. A repeat alert updates the existing open case (adds a
comment) instead of creating a duplicate.

### Enrichment
When a source IP exists it is added as an `ip` observable, which triggers
TheHive's RunAnalyzer notification -> Cortex (VirusTotal + AbuseIPDB) (Task 7).

## 3. Approval + response (Task 11)
Continue the workflow with a User Input (approval) node and the active-response
step -- see `documentation/approval-and-response.md`.

## Test the logic offline
```
THEHIVE_API_KEY=dummy python3 thehive_case.py < ../../detections/test-events/wazuh_alert_ssh.json
```