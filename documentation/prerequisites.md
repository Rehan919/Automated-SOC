# Prerequisites & host preparation

## Hardware
- Windows 10/11, >= 16 GB system RAM (8 GB will boot but thrash), >= 60 GB free disk.

## 1. WSL2 + Docker Desktop
- Install Docker Desktop and enable the **WSL2 backend** (Settings > General).
- Copy `.wslconfig` (repo root) to `%USERPROFILE%\.wslconfig` and run `wsl --shutdown`.
- Verify allocation after Docker restarts: `wsl -e bash -lc "free -h"` (expect ~12G).

## 2. Kernel setting for the Wazuh Indexer (OpenSearch)
The indexer requires a high mmap count. The provided `.wslconfig` sets
`vm.max_map_count=262144` via kernelCommandLine. Verify:
```
wsl -d docker-desktop sysctl vm.max_map_count   # expect 262144
```

## 3. Secrets
```
copy .env.example .env
```
Replace every `CHANGE_ME`. Generate strong secrets: `wsl -e bash -lc "openssl rand -base64 24"`.
`THEHIVE_SECRET` / `CORTEX_SECRET` must be >= 32 chars.

## 4. Validate the compose definitions
```
docker compose config                                 # whole lab
docker compose -f wazuh/docker-compose.yml config     # per-component
```
Both must succeed and show the `soc-lab` network before bring-up.