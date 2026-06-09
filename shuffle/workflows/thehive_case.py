#!/usr/bin/env python3
"""Shuffle step: Wazuh alert -> TheHive case (severity mapping + dedup).

Runs inside a Shuffle "Run Python" action, or standalone for testing:
    THEHIVE_URL=http://thehive:9000 THEHIVE_API_KEY=xxx \
        python3 thehive_case.py < alert.json

Behaviour:
  * Maps Wazuh rule.level -> TheHive severity:
        7-9  -> 1 (Low)
        10-12 -> 2 (Medium)
        13-15 -> 4 (Critical)
  * Dedup: if an OPEN case already carries tag dedup:<key> it is reused
    (a comment is appended) instead of creating a duplicate.
        key = source IP if present, else "<agent>:<rule_id>"
  * Adds the source IP (if any) as an `ip` observable, which triggers
    TheHive's RunAnalyzer notification (Cortex enrichment, Task 7).
"""
import json
import os
import sys

import requests

requests.packages.urllib3.disable_warnings()  # lab self-signed/no-TLS


def severity_from_level(level):
    if level >= 13:
        return 4
    if level >= 10:
        return 2
    return 1


def _hdr(api_key):
    return {"Authorization": "Bearer %s" % api_key,
            "Content-Type": "application/json"}


def find_open_case(base, api_key, dedup_tag):
    """Return an open case id carrying dedup_tag, or None."""
    query = {"query": [
        {"_name": "listCase"},
        {"_name": "filter", "_and": [
            {"_field": "status", "_value": "Open"},
            {"_field": "tags", "_value": dedup_tag},
        ]},
        {"_name": "page", "from": 0, "to": 1},
    ]}
    r = requests.post("%s/api/v1/query" % base, headers=_hdr(api_key),
                      data=json.dumps(query), timeout=15, verify=False)
    r.raise_for_status()
    rows = r.json()
    return rows[0]["_id"] if rows else None


def add_comment(base, api_key, case_id, message):
    requests.post("%s/api/v1/case/%s/comment" % (base, case_id),
                  headers=_hdr(api_key), data=json.dumps({"message": message}),
                  timeout=15, verify=False)


def create_case(base, api_key, title, description, severity, tags):
    payload = {"title": title, "description": description,
               "severity": severity, "tags": tags, "tlp": 2, "pap": 2}
    r = requests.post("%s/api/v1/case" % base, headers=_hdr(api_key),
                      data=json.dumps(payload), timeout=15, verify=False)
    r.raise_for_status()
    return r.json()["_id"]


def add_ip_observable(base, api_key, case_id, ip):
    payload = {"dataType": "ip", "data": ip, "tlp": 2,
               "message": "Source IP from Wazuh alert", "ioc": True}
    requests.post("%s/api/v1/case/%s/observable" % (base, case_id),
                  headers=_hdr(api_key), data=json.dumps(payload),
                  timeout=15, verify=False)


def run(alert, base, api_key):
    rule = alert.get("rule", {})
    level = int(rule.get("level", 0) or 0)
    rule_id = str(rule.get("id", "unknown"))
    desc = rule.get("description", "Wazuh alert")
    agent = alert.get("agent", {}).get("name", "unknown")
    srcip = alert.get("data", {}).get("srcip")

    severity = severity_from_level(level)
    dedup_key = srcip if srcip else "%s:%s" % (agent, rule_id)
    dedup_tag = "dedup:%s" % dedup_key

    existing = find_open_case(base, api_key, dedup_tag)
    if existing:
        add_comment(base, api_key, existing,
                    "Repeat Wazuh alert (rule %s, level %s) on %s" %
                    (rule_id, level, agent))
        return {"case_id": existing, "action": "updated", "severity": severity}

    title = "[Wazuh] %s" % desc
    description = (
        "**Agent:** %s\n\n**Rule:** %s (level %s)\n\n**MITRE:** %s\n\n"
        "**Source IP:** %s\n\n```\n%s\n```" % (
            agent, rule_id, level,
            ", ".join(rule.get("mitre", {}).get("id", []) or []),
            srcip or "n/a", alert.get("full_log", "")[:2000]))
    tags = ["wazuh", "rule:%s" % rule_id, dedup_tag]
    tags += rule.get("mitre", {}).get("id", []) or []

    case_id = create_case(base, api_key, title, description, severity, tags)
    if srcip:
        add_ip_observable(base, api_key, case_id, srcip)
    return {"case_id": case_id, "action": "created", "severity": severity,
            "observable_ip": srcip}


def main():
    base = os.environ.get("THEHIVE_URL", "http://thehive:9000").rstrip("/")
    api_key = os.environ["THEHIVE_API_KEY"]
    alert = json.load(sys.stdin)
    # Shuffle may wrap the body; unwrap common shapes
    if "rule" not in alert:
        for k in ("body", "alert", "data"):
            if isinstance(alert.get(k), dict) and "rule" in alert[k]:
                alert = alert[k]
                break
    print(json.dumps(run(alert, base, api_key)))


if __name__ == "__main__":
    main()