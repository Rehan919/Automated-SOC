# Task 7: TheHive <-> Cortex (enrichment ownership)

TheHive owns analyzer execution. Shuffle never calls Cortex directly.

## 1. Cortex connector (already wired)
`thehive/docker-compose.yml` passes:
```
--cortex-hostnames cortex --cortex-port 9001 --cortex-keys ${CORTEX_API_KEY}
```
So set `CORTEX_API_KEY` in `.env` (from cortex/README.md) BEFORE starting TheHive.
Verify: TheHive -> Admin -> Cortex servers shows `cortex` as connected (green).

## 2. Auto-run analyzers on `ip` observables (TheHive-native)
Use a TheHive **Notification** with the **RunAnalyzer** notifier so enrichment
fires automatically when Shuffle adds the IP observable (Task 10):

Organisation -> Notifications -> Add:
- Trigger: `FilteredEvent`  on `object-type == "Observable"` and `dataType == "ip"`
  (or simply `AnyEvent` filtered to Observable creation)
- Notifier: **RunAnalyzer**
  - analyzers: `VirusTotal_GetReport_3_1`, `AbuseIPDB_1_0`
- Save & enable.

Now every IP observable added to a case is enriched automatically; the VirusTotal
and AbuseIPDB reports attach to the observable and drive the malicious verdict
consumed by the Shuffle approval gate (Task 11).

## Demo
Create a case, add an `ip` observable for a known-bad IP -> analyzers auto-run ->
reports show "malicious".