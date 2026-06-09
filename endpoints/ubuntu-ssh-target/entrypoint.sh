#!/bin/bash
set -e
# SSH host keys + rsyslog (so sshd auth events land in /var/log/auth.log)
ssh-keygen -A
rsyslogd
# Enroll the Wazuh agent (retry until the manager authd is reachable)
if [ ! -s /var/ossec/etc/client.keys ]; then
  for i in $(seq 1 30); do
    if /var/ossec/bin/agent-auth -m wazuh.manager; then break; fi
    echo "[agent] waiting for wazuh.manager authd ($i/30)..."; sleep 5
  done
fi
/var/ossec/bin/wazuh-control start
# Keep container in foreground on sshd
exec /usr/sbin/sshd -D