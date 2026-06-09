#!/usr/bin/env python3
"""Manual rollback: undo a block recorded in responses.db.

Usage:
  python3 unblock.py --incident-id case~123     # unblock by incident
  python3 unblock.py --ip 45.155.205.99         # unblock by IP
  python3 unblock.py --list                     # show response history
Runs the stored rollback_command (also relies on the firewall-drop <timeout>
auto-expiry as defense in depth).
"""
import argparse
import os
import sqlite3
import subprocess
import sys

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "responses.db")


def rows(where="", params=()):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    q = ("SELECT id,timestamp,incident_id,action,target,approved_by,"
         "rollback_command FROM responses %s ORDER BY id DESC" % where)
    return conn.execute(q, params).fetchall()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--incident-id")
    ap.add_argument("--ip")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(DB_PATH):
        print("no responses.db yet"); sys.exit(0)

    if args.list:
        for r in rows():
            print(dict(r))
        return

    if args.incident_id:
        sel = rows("WHERE incident_id=?", (args.incident_id,))
    elif args.ip:
        sel = rows("WHERE target=?", (args.ip,))
    else:
        ap.error("provide --incident-id, --ip or --list")

    for r in sel:
        cmd = r["rollback_command"]
        if not cmd or cmd == "n/a":
            continue
        print("[*] %s" % cmd)
        subprocess.run(cmd, shell=True, check=False)
    print("[+] rollback complete")


if __name__ == "__main__":
    main()