# SOC Automation Lab v2

Enterprise-style SOC lab on a single Windows host (Docker Desktop + WSL2):

**Wazuh** (SIEM/EDR/detection) -> **Shuffle** (SOAR) -> **TheHive** (cases) <-> **Cortex** (enrichment) -> human-approved active response -> forensic log retention.

## Quick start
1. Install Docker Desktop (WSL2 backend) on a host with >= 16 GB RAM.
2. Copy `.wslconfig` to `%USERPROFILE%\.wslconfig`, then `wsl --shutdown`.
3. `copy .env.example .env` and replace every `CHANGE_ME`.
4. Follow `documentation/prerequisites.md`, then `documentation/runbook.md`.
   Full stack: `docker compose up -d`.

## Layout
| Folder | Purpose |
|---|---|
| `wazuh/` | Manager + Indexer + Dashboard, manager config, active-response |
| `endpoints/` | `ubuntu-ssh-target` + `attacker` containers; Windows+Sysmon docs |
| `thehive/` | TheHive 5 + Cassandra + Elasticsearch |
| `cortex/` | Cortex + analyzer config |
| `shuffle/` | Shuffle SOAR stack + exported workflows |
| `detections/` | Detection-as-code: `wazuh-rules/`, `sigma/`, `test-events/` |
| `retention/` | ISM policy + hot->cold archive job |
| `scripts/` | Wazuh->Shuffle integration, responses.db helper, backup |
| `documentation/` | Prerequisites, architecture, runbook |

## Security
Lab only. All services bind to `127.0.0.1`. Rotate every default credential.
Secrets live in `.env` (gitignored). Do NOT expose to a public network.