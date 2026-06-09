# Cortex + Analyzers

## Bring up
```
docker compose -f cortex/docker-compose.yml up -d
```
Open http://127.0.0.1:9001

## First boot
1. Create the Cortex superadmin account (first screen), then log in.
2. **Update/refresh analyzers** (Organization may need creating first):
   create an organisation `soc-lab`, add an `org-admin` user.
3. As org-admin: enable analyzers and set their API keys from `.env`:
   - **VirusTotal_GetReport_3_1** -> `VIRUSTOTAL_API_KEY`
   - **AbuseIPDB_1_0** -> `ABUSEIPDB_API_KEY`
   Set each analyzer "Cache" (TTL) to e.g. 30 minutes to respect free-tier quotas
   (global job cache is also 30m in cortex-application.conf).
4. Create an **API key** for the org user (Organization -> Users -> Create API key).
   Put it in `.env` as `CORTEX_API_KEY` (TheHive uses it in Task 7).

## Notes
- Analyzers run as Docker containers; the Docker socket and /tmp/cortex-jobs are
  mounted. On Docker Desktop (WSL2) the daemon runs in the WSL VM, so the shared
  job path resolves correctly for sibling analyzer containers.
- Verify an analyzer: run VirusTotal_GetReport on a known-bad IP/hash -> "malicious".