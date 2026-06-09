#!/usr/bin/env python3
"""Wazuh -> Shuffle integration.
Invoked by the Wazuh integrator as:
    custom-shuffle <alert_file> <api_key> <hook_url> [options]
Forwards the full alert JSON to the Shuffle webhook. Only alerts with
rule.level >= 7 are sent (the <integration><level> filter also enforces this).
"""
import sys
import json
import time

try:
    import requests
except ImportError:
    sys.stderr.write("custom-shuffle: python 'requests' module missing\n")
    sys.exit(1)

MIN_LEVEL = 7
RETRIES = 3
TIMEOUT = 10


def main(argv):
    if len(argv) < 4:
        sys.stderr.write("custom-shuffle: usage: <alert_file> <api_key> <hook_url>\n")
        sys.exit(1)

    alert_file, _api_key, hook_url = argv[1], argv[2], argv[3]

    with open(alert_file, "r", encoding="utf-8") as fh:
        alert = json.load(fh)

    level = int(alert.get("rule", {}).get("level", 0) or 0)
    if level < MIN_LEVEL:
        sys.exit(0)  # filtered as noise

    headers = {"Content-Type": "application/json"}
    body = json.dumps(alert)

    for attempt in range(1, RETRIES + 1):
        try:
            resp = requests.post(hook_url, data=body, headers=headers,
                                 timeout=TIMEOUT, verify=False)
            if resp.status_code < 300:
                sys.exit(0)
            sys.stderr.write("custom-shuffle: HTTP %s (attempt %d)\n"
                             % (resp.status_code, attempt))
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write("custom-shuffle: POST failed (attempt %d): %s\n"
                             % (attempt, exc))
        time.sleep(2 * attempt)

    sys.stderr.write("custom-shuffle: giving up after %d attempts\n" % RETRIES)
    sys.exit(0)  # never block the integrator queue


if __name__ == "__main__":
    main(sys.argv)