#!/usr/bin/env python3
"""SOC auto-responder: receives Wazuh alerts (level>=7) and creates TheHive cases.
Stdlib only (no pip). Listens on :8080, POST /alert with the Wazuh alert JSON."""
import json, os, urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

BASE = os.environ.get("THEHIVE_URL", "http://thehive:9000").rstrip("/")
APIKEY = os.environ["THEHIVE_API_KEY"]
HDR = {"Authorization": "Bearer " + APIKEY, "Content-Type": "application/json"}


def th(method, path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(BASE + path, data=data, headers=HDR, method=method)
    with urllib.request.urlopen(req, timeout=15) as r:
        body = r.read().decode()
    return json.loads(body) if body else {}


def sev(l):
    l = int(l or 0)
    return 4 if l >= 13 else (2 if l >= 10 else 1)


def handle(alert):
    if "rule" not in alert:
        for k in ("body", "alert", "data"):
            if isinstance(alert.get(k), dict) and "rule" in alert[k]:
                alert = alert[k]; break
    r = alert.get("rule", {})
    lvl = int(r.get("level", 0) or 0); rid = str(r.get("id", "?"))
    desc = r.get("description", "Wazuh alert")
    agent = alert.get("agent", {}).get("name", "unknown")
    srcip = alert.get("data", {}).get("srcip")
    key = srcip if srcip else agent + ":" + rid
    tag = "dedup:" + key
    q = {"query": [{"_name": "listCase"},
                   {"_name": "filter", "_and": [
                       {"_field": "status", "_value": "Open"},
                       {"_field": "tags", "_value": tag}]},
                   {"_name": "page", "from": 0, "to": 1}]}
    ex = th("POST", "/api/v1/query", q)
    if ex:
        cid = ex[0]["_id"]
        th("POST", "/api/v1/case/%s/comment" % cid,
           {"message": "Repeat Wazuh alert rule %s level %s on %s" % (rid, lvl, agent)})
        return {"case_id": cid, "action": "updated"}
    mitre = r.get("mitre", {}).get("id", []) or []
    body = {"title": "[Wazuh] " + desc,
            "description": "Agent: %s\nRule: %s (level %s)\nMITRE: %s\nSource IP: %s"
                           % (agent, rid, lvl, ",".join(mitre), srcip),
            "severity": sev(lvl),
            "tags": ["wazuh", "rule:" + rid, tag] + mitre, "tlp": 2, "pap": 2}
    cid = th("POST", "/api/v1/case", body)["_id"]
    if srcip:
        th("POST", "/api/v1/case/%s/observable" % cid,
           {"dataType": "ip", "data": srcip, "ioc": True, "tlp": 2,
            "message": "Source IP from Wazuh alert"})
    return {"case_id": cid, "action": "created", "severity": sev(lvl), "observable_ip": srcip}


class H(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        self._send(200 if self.path == "/health" else 404, {"status": "ok"})

    def do_POST(self):
        if self.path != "/alert":
            self._send(404, {"error": "not found"}); return
        try:
            n = int(self.headers.get("Content-Length", 0))
            alert = json.loads(self.rfile.read(n).decode())
            res = handle(alert)
            print("case:", res, flush=True)
            self._send(200, res)
        except Exception as e:  # noqa: BLE001
            print("error:", e, flush=True)
            self._send(500, {"error": str(e)})

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    print("responder listening on :8080 -> %s" % BASE, flush=True)
    HTTPServer(("0.0.0.0", 8080), H).serve_forever()