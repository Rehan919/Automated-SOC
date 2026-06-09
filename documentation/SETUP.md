# Full Setup & Rebuild Guide

Step-by-step to get the lab running from a fresh clone. Follow top to bottom.
This is the **exact working flow** (including the gotchas that bit us the first time).

> Auto-case creation is done by the **responder** service (Wazuh -> responder ->
> TheHive). Shuffle is included for the SOAR view but is **optional** - you do NOT
> need to build a Shuffle workflow to get working, auto-created cases.

---

## 0. Prerequisites

- **16 GB RAM** recommended (12 GB min), ~60 GB free disk.
- **Docker + Docker Compose v2** (`docker compose version` >= 2.20).
- **Windows:** Docker Desktop with the **WSL2 backend**, and **Git Bash**
  (ships with Git for Windows) to run the `.sh` helper scripts.
- A free **VirusTotal** API key and **AbuseIPDB** API key.

**Windows - give Docker memory (once):**
```powershell
copy .wslconfig $env:USERPROFILE\.wslconfig
wsl --shutdown
```
**Linux - raise map count (once):**
```bash
sudo sysctl -w vm.max_map_count=262144
```

---

## 1. Clone

```bash
git clone https://github.com/Rehan919/Automated-SOC.git
cd Automated-SOC
```

---

## 2. Secrets

```bash
cp .env.example .env                 # Windows: copy .env.example .env
cp shuffle/.env.example shuffle/.env # Windows: copy shuffle\.env.example shuffle\.env
```
Edit both files and replace every `CHANGE_ME`. Generate strong values with
`openssl rand -base64 24`. Put your VirusTotal + AbuseIPDB keys in `.env`.
Leave `CORTEX_API_KEY`, `THEHIVE_API_KEY`, `SHUFFLE_WEBHOOK_URL` as `CHANGE_ME`
for now (created after first boot).

> Password rules: `THEHIVE_SECRET`/`CORTEX_SECRET` >= 32 chars.
> `WAZUH_API_PASSWORD` needs upper+lower+digit+symbol, 8-64 chars.

---

## 3. Certificates + password rotation (once)

```bash
docker compose -f wazuh/generate-indexer-certs.yml run --rm generator
bash scripts/wazuh-change-passwords.sh      # Windows: run in Git Bash
```
(`wazuh-change-passwords.sh` makes the indexer/dashboard match your `.env` and
fills the API password into `wazuh/config/wazuh_dashboard/wazuh.yml`.)

---

## 4. Start the stack

```bash
docker compose up -d
docker compose ps        # wait until healthy (first boot pulls images: ~5-10 min)
```

**Web UIs (localhost):**

| Service | URL | Login |
|---|---|---|
| Wazuh dashboard | https://localhost (443) | `admin` / your `INDEXER_PASSWORD` |
| TheHive | http://localhost:9000 | `admin@thehive.local` / `secret` |
| Cortex | http://localhost:9001 | create admin on first visit |
| Shuffle (optional) | http://localhost:3001 | `admin` / your `SHUFFLE_DEFAULT_PASSWORD` |

> **Gotcha - manager unhealthy on a brand-new volume?** If `wazuh.manager` stays
> "starting"/unhealthy with `Could not open file 'etc/shared/ar.conf'` in its log:
> ```bash
> docker exec soc-wazuh.manager-1 sh -c 'mkdir -p /var/ossec/etc/shared/default && touch /var/ossec/etc/shared/ar.conf && chown -R wazuh:wazuh /var/ossec/etc/shared'
> docker compose restart wazuh.manager
> ```

---

## 5. Connect Cortex + TheHive (one time)

### 5a. Cortex (http://localhost:9001)
1. Create the admin account on first visit and log in.
   - **Gotcha:** if you see **"userInit not found"**, the DB needs init. Run:
     ```bash
     curl -s -X POST http://127.0.0.1:9001/api/maintenance/migrate -d '{}'
     ```
     then refresh and create the admin.
2. **Organizations -> Add** `soc-lab` (enable it).
3. Open `soc-lab` -> **Users -> Add user**: login `soc-analyst`, roles
   **read, analyze, orgAdmin** -> create -> **Create API key** -> copy it.
4. Put that key in `.env` as `CORTEX_API_KEY`.
5. **Organization -> Analyzers** -> enable **VirusTotal_GetReport** and
   **AbuseIPDB**, pasting your API keys (set cache ~30 min).

### 5b. TheHive (http://localhost:9000)
1. Log in `admin@thehive.local` / `secret`, change the password.
2. **Organizations -> Add** `soc-lab` -> add a user -> **Create API key** -> copy.
3. Put it in `.env` as `THEHIVE_API_KEY`.

### 5c. Apply the keys
```bash
docker compose up -d thehive responder    # reloads with CORTEX_API_KEY + THEHIVE_API_KEY
bash retention/apply-ism-policy.sh         # optional: 30-day hot retention
```

That's it - alerts at level >= 7 now auto-create enriched TheHive cases.

---

## 6. Test it works

```bash
# Windows
.\scripts\attack.ps1
# Linux/macOS
docker compose --profile attack run --rm attacker
```
Within ~30s a case appears in TheHive (http://localhost:9000, log in as your
`soc-analyst` user - cases live in the `soc-lab` org). Check the responder:
```bash
docker logs --tail 3 soc-responder      # should show: case: {... 'action': 'created' ...}
```

---

## 7. (Optional) Monitor your own machines

Expose the manager's agent ports to your LAN (edit `wazuh/docker-compose.yml`:
change `127.0.0.1:1514`/`1515` to `0.0.0.0:1514`/`1515`), open the firewall
(`New-NetFirewallRule ... -LocalPort 1514`/`1515` on Windows), then install an agent:

**Linux:**
```bash
curl -so wazuh-agent.deb https://packages.wazuh.com/4.x/apt/pool/main/w/wazuh-agent/wazuh-agent_4.9.2-1_amd64.deb
sudo WAZUH_MANAGER="<MANAGER_IP>" dpkg -i ./wazuh-agent.deb && sudo systemctl start wazuh-agent
```
**Windows (admin):**
```powershell
msiexec.exe /i wazuh-agent-4.9.2-1.msi /q WAZUH_MANAGER="<MANAGER_IP>" WAZUH_AGENT_NAME="my-pc"; NET START WazuhSvc
```

---

## 8. (Optional) Shuffle SOAR view
The responder already creates cases. If you also want Shuffle to receive alerts:
open http://localhost:3001 -> open the `SOC Pipeline` workflow -> add a **Webhook**
trigger -> copy its URL into `.env` as `SHUFFLE_WEBHOOK_URL` ->
`bash scripts/set-shuffle-webhook.sh` -> `docker compose restart wazuh.manager`.

---

## 9. Daily commands

```bash
docker compose up -d          # start (resume - data persists in volumes)
docker compose down           # stop, KEEP data
docker compose down -v        # stop and WIPE all data (full reset)
docker compose ps             # status
docker exec soc-wazuh.manager-1 /var/ossec/bin/agent_control -l   # list agents
```

> After `docker compose down` (without `-v`), just `docker compose up -d` to get
> everything back exactly as it was - cases, agents, and config persist in volumes.
> You only repeat Steps 2-5 if you wiped volumes (`-v`) or cloned fresh.

---

## 10. If something breaks
See `documentation/troubleshooting.md` for the known first-run issues
(agent enrollment "Duplicate agent name", dashboard YAML crash, manager `ar.conf`)
and their one-line fixes.