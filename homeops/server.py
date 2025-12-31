#!/usr/bin/env python3
# HomeOps v0: Doctor (read-only)
#
# Runs as a Home Assistant add-on with Ingress enabled.
# - UI: / (simple HTML)
# - API: /api/doctor (JSON)
#
# Data source:
# - Home Assistant Core API via internal proxy:
#   http://supervisor/core/api/
# Requires:
# - config.yaml: homeassistant_api: true
# - Authorization header: Bearer $SUPERVISOR_TOKEN

from __future__ import annotations

import json
import os
import socketserver
import time
from http.server import BaseHTTPRequestHandler
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

HOST = "0.0.0.0"
PORT = int(os.environ.get("HOMEOPS_PORT", "8000"))

SUPERVISOR_TOKEN = os.environ.get("SUPERVISOR_TOKEN", "")
CORE_API_BASE = os.environ.get("HOMEOPS_CORE_API_BASE", "http://supervisor/core/api")

START_TIME = time.time()


def _ha_get(path: str):
    if not SUPERVISOR_TOKEN:
        raise RuntimeError("SUPERVISOR_TOKEN is missing. Did you set homeassistant_api: true in config.yaml?")

    url = f"{CORE_API_BASE.rstrip('/')}/{path.lstrip('/')}"
    req = Request(url, method="GET")
    req.add_header("Authorization", f"Bearer {SUPERVISOR_TOKEN}")
    req.add_header("Content-Type", "application/json")

    with urlopen(req, timeout=10) as resp:
        data = resp.read().decode("utf-8")
        return json.loads(data)


def _safe_domain_counts(states):
    counts = {}
    for s in states:
        eid = s.get("entity_id", "")
        if "." in eid:
            domain = eid.split(".", 1)[0]
            counts[domain] = counts.get(domain, 0) + 1
    return sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:12]


INDEX_HTML = """<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>HomeOps</title>
    <style>
      :root {
        --bg: #0b0c10;
        --panel: #12141b;
        --text: #e9eef6;
        --muted: #9aa4b2;
        --border: #23283b;
      }
      body { margin:0; font-family: -apple-system, system-ui, Segoe UI, Roboto, Helvetica, Arial; background: var(--bg); color: var(--text); }
      .wrap { max-width: 920px; margin: 0 auto; padding: 28px 18px 60px; }
      .top { display:flex; align-items:center; justify-content:space-between; gap: 12px; }
      h1 { margin:0; font-size: 22px; letter-spacing: .2px; }
      .pill { font-size: 12px; padding: 6px 10px; border: 1px solid var(--border); border-radius: 999px; background: rgba(255,255,255,.03); color: var(--muted); }
      .grid { display:grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 14px; }
      .card { background: var(--panel); border:1px solid var(--border); border-radius: 14px; padding: 14px; }
      .k { color: var(--muted); font-size: 12px; }
      .v { font-size: 16px; margin-top: 4px; }
      .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }
      .small { font-size: 12px; color: var(--muted); }
      .bar { display:flex; gap: 8px; flex-wrap: wrap; margin-top: 10px; }
      button { background: rgba(255,255,255,.06); border:1px solid var(--border); color: var(--text); padding: 10px 12px; border-radius: 12px; cursor:pointer; }
      button:hover { background: rgba(255,255,255,.09); }
      pre { white-space: pre-wrap; word-wrap: break-word; background: rgba(0,0,0,.25); border:1px solid var(--border); padding: 12px; border-radius: 12px; overflow:auto; }
      @media (max-width: 760px) { .grid { grid-template-columns: 1fr; } }
    </style>
  </head>
  <body>
    <div class="wrap">
      <div class="top">
        <h1>HomeOps <span class="pill">Doctor v0 (read‑only)</span></h1>
        <div class="small mono" id="uptime">…</div>
      </div>

      <div class="grid">
        <div class="card">
          <div class="k">Home Assistant version</div>
          <div class="v" id="ha_version">…</div>
        </div>
        <div class="card">
          <div class="k">Entities</div>
          <div class="v" id="entity_count">…</div>
          <div class="small" id="domain_counts"></div>
        </div>
        <div class="card">
          <div class="k">Location name</div>
          <div class="v" id="location_name">…</div>
        </div>
        <div class="card">
          <div class="k">Time zone</div>
          <div class="v mono" id="time_zone">…</div>
        </div>
      </div>

      <div class="card" style="margin-top:12px;">
        <div class="k">Diagnostics snapshot</div>
        <div class="bar">
          <button onclick="copyDiag()">Copy diagnostics</button>
          <button onclick="refresh()">Refresh</button>
        </div>
        <pre id="diag">Loading…</pre>
      </div>

      <p class="small" style="margin-top:12px;">
        Next: health checks, repair suggestions, and Safe Change Engine approval flows.
      </p>
    </div>

    <script>
      let last = null;

      function fmtUptime(sec) {
        const s = Math.floor(sec);
        const h = Math.floor(s / 3600);
        const m = Math.floor((s % 3600) / 60);
        const r = s % 60;
        return `${h}h ${m}m ${r}s`;
      }

      async function refresh() {
        const res = await fetch("./api/doctor");
        const data = await res.json();
        last = data;

        document.getElementById("ha_version").textContent = data.ha_version ?? "unknown";
        document.getElementById("entity_count").textContent = String(data.entity_count ?? "unknown");
        document.getElementById("location_name").textContent = data.location_name ?? "—";
        document.getElementById("time_zone").textContent = data.time_zone ?? "—";

        const dc = (data.domain_counts || []).map(([d,c]) => `${d}:${c}`).join("  •  ");
        document.getElementById("domain_counts").textContent = dc ? `Top domains: ${dc}` : "";

        document.getElementById("diag").textContent = JSON.stringify(data, null, 2);
      }

      async function copyDiag() {
        if (!last) return;
        await navigator.clipboard.writeText(JSON.stringify(last, null, 2));
        alert("Diagnostics copied.");
      }

      setInterval(() => {
        const up = last?.homeops_uptime_s ?? 0;
        document.getElementById("uptime").textContent = `HomeOps uptime: ${fmtUptime(up)}`;
      }, 1000);

      refresh();
    </script>
  </body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def _json(self, obj, code=200):
        raw = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _html(self, html, code=200):
        raw = html.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, fmt, *args):
        return

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._html(INDEX_HTML)
            return

        if self.path == "/healthz":
            self._json({"ok": True})
            return

        if self.path.startswith("/api/doctor"):
            try:
                config = _ha_get("/config")
                states = _ha_get("/states")

                resp = {
                    "ha_version": config.get("version"),
                    "location_name": config.get("location_name"),
                    "time_zone": config.get("time_zone"),
                    "unit_system": config.get("unit_system"),
                    "entity_count": len(states) if isinstance(states, list) else None,
                    "domain_counts": _safe_domain_counts(states) if isinstance(states, list) else [],
                    "homeops_uptime_s": int(time.time() - START_TIME),
                }
                self._json(resp)
            except HTTPError as e:
                self._json({"error": f"HTTPError {e.code}", "detail": str(e)}, 502)
            except URLError as e:
                self._json({"error": "URLError", "detail": str(e)}, 502)
            except Exception as e:
                self._json({"error": "Exception", "detail": str(e)}, 500)
            return

        self._json({"error": "Not found"}, 404)


def main():
    with socketserver.TCPServer((HOST, PORT), Handler) as httpd:
        print(f"[HomeOps] listening on http://{HOST}:{PORT}")
        httpd.serve_forever()


if __name__ == "__main__":
    main()
