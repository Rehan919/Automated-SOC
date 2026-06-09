#!/usr/bin/env python3
"""Task 11: human-approved active response with allowlist + accountability DB.

Called by the Shuffle workflow AFTER an analyst approves the block. Steps:
  1. Refuse to block any IP on the RESPONSE_ALLOWLIST (exact IP or CIDR).
  2. Invoke the Wazuh `firewall-drop` active response on the target agent via
     the Wazuh API (drops the source IP with iptables on that host).
  3. Record an auditable row in scripts/responses.db with a rollback command.

Env: WAZUH_API_URL, WAZUH_API_USERNAME, WAZUH_API_PASSWORD, RESPONSE_ALLOWLIST.
Usage:
  python3 active_response.py --ip 45.155.205.99 --agent-id 001 \
      --incident-id case~123 --approved-by analyst@soc --target ubuntu-ssh-target
  (add --dry-run to skip the API call, e.g. for allowlist/DB testing)
"""
import argparse
import ipaddress
import json
import os
import sqlite3
import sys
import time

import requests

requests.packages.urllib3.disable_warnings()

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "responses.db")
AR_COMMAND = os.environ.get("AR_COMMAND", "firewall-drop")


def is_allowlisted(ip, allowlist):
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return True  # not a valid IP -> never block
    for entry in allowlist:
        entry = entry.strip()
        if not entry:
            continue
        try:
            if "/" in entry:
                if addr in ipaddress.ip_network(entry, strict=False):
                    return True
            elif ip == entry:
                return True
        except ValueError:
            continue
    return False


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS responses ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, incident_id TEXT, "
        "action TEXT, target TEXT, approved_by TEXT, rollback_command TEXT)")
    conn.commit()
    return conn


def log_response(conn, incident_id, action, target, approved_by, rollback_command):
    conn.execute(
        "INSERT INTO responses (timestamp, incident_id, action, target, "
        "approved_by, rollback_command) VALUES (?,?,?,?,?,?)",
        (time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), incident_id,
         action, target, approved_by, rollback_command))
    conn.commit()


def wazuh_firewall_drop(ip, agent_id):
    base = os.environ.get("WAZUH_API_URL", "https://wazuh.manager:55000").rstrip("/")
    user = os.environ["WAZUH_API_USERNAME"]
    pwd = os.environ["WAZUH_API_PASSWORD"]
    auth = requests.get("%s/security/user/authenticate" % base,
                        auth=(user, pwd), timeout=15, verify=False)
    auth.raise_for_status()
    token = auth.json()["data"]["token"]
    body = {"command": AR_COMMAND, "arguments": [],
            "alert": {"data": {"srcip": ip}}}
    r = requests.put("%s/active-response?agents_list=%s" % (base, agent_id),
                     headers={"Authorization": "Bearer %s" % token,
                              "Content-Type": "application/json"},
                     data=json.dumps(body), timeout=15, verify=False)
    r.raise_for_status()
    return r.json()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ip", required=True)
    ap.add_argument("--agent-id", required=True)
    ap.add_argument("--incident-id", required=True)
    ap.add_argument("--approved-by", required=True)
    ap.add_argument("--target", default="ubuntu-ssh-target")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    allowlist = os.environ.get("RESPONSE_ALLOWLIST", "127.0.0.1").split(",")
    conn = init_db()
    rollback = "docker exec %s iptables -D INPUT -s %s -j DROP" % (args.target, args.ip)

    if is_allowlisted(args.ip, allowlist):
        log_response(conn, args.incident_id, "block-skipped-allowlist",
                     args.ip, args.approved_by, "n/a")
        print(json.dumps({"status": "skipped", "reason": "allowlisted",
                          "ip": args.ip}))
        return

    if args.dry_run:
        log_response(conn, args.incident_id, "block-dry-run", args.ip,
                     args.approved_by, rollback)
        print(json.dumps({"status": "dry-run", "ip": args.ip,
                          "rollback_command": rollback}))
        return

    result = wazuh_firewall_drop(args.ip, args.agent_id)
    log_response(conn, args.incident_id, "firewall-drop", args.ip,
                 args.approved_by, rollback)
    print(json.dumps({"status": "blocked", "ip": args.ip,
                      "rollback_command": rollback, "api": result}))


if __name__ == "__main__":
    main()