# Troubleshooting (issues found during first live bring-up)

All fixes below are already applied to the repo. Documented for reproducibility.

## 1. SSH events never reached Wazuh (no alerts)
Symptom: attack runs but no rule 100100; `/var/log/auth.log` empty on the agent.
Cause: agent entrypoint ran `sshd -D -e`; `-e` logs to stderr, not syslog.
Fix: `endpoints/ubuntu-ssh-target/entrypoint.sh` now runs `sshd -D` (logs via
syslog -> rsyslog -> /var/log/auth.log, which the agent monitors).

## 2. Manager unhealthy / authd + wazuh-db down
Symptom: `wazuh-analysisd: (1103) Could not open file 'etc/shared/ar.conf'` ->
`CRITICAL (1202) Configuration error` -> manager never finishes init.
Cause: a custom `<active-response>` block required `etc/shared/ar.conf`, which
does not exist before the manager finishes first-run init (chicken/egg), so
analysisd crashed and aborted the rest of startup.
Fix: removed the `<active-response>` block from `ossec.conf`. Active response for
Task 11 is invoked via the Wazuh API; if you re-add an `<active-response>` block,
first ensure `/var/ossec/etc/shared/ar.conf` exists:
```
docker exec soc-wazuh.manager-1 sh -c 'mkdir -p /var/ossec/etc/shared/default && \
  touch /var/ossec/etc/shared/ar.conf && chown -R wazuh:wazuh /var/ossec/etc/shared'
docker compose restart wazuh.manager
```

## 3. Dashboard crash-loop ("incomplete explicit mapping pair")
Cause: `wazuh.yml` lacked a trailing newline and used a host key the dashboard
entrypoint did not recognize, so the entrypoint appended a second `hosts:` block
producing invalid YAML (`run_as: falsehosts:`).
Fix: `wazuh/config/wazuh_dashboard/wazuh.yml` now uses the canonical single host
(`1513629884013`) with a trailing newline; the entrypoint stays idempotent.

## 4. Agent cannot re-enroll after recreate ("Duplicate agent name")
Symptom: recreated `ubuntu-ssh-target` loops on `agent-auth ... Duplicate agent
name`, so sshd (the entrypoint's final exec) never starts.
Cause: the agent's client.keys lives in the container fs (not persisted); on
recreate it re-enrolls, but the manager still holds the old (active) registration.
Fix: added a `<force>` block to the manager `<auth>` config so a re-registering
agent replaces the stale entry. If an agent still won't enroll, remove the stale
one and restart the agent:
```
docker exec soc-wazuh.manager-1 /var/ossec/bin/manage_agents   # (R)emove, then quit
docker restart ubuntu-ssh-target
```

## Handy checks
```
docker compose ps
docker exec soc-wazuh.manager-1 /var/ossec/bin/agent_control -l
docker exec soc-wazuh.manager-1 sh -c 'grep -c 100100 /var/ossec/logs/alerts/alerts.json'
```