import os
import requests
from flask import Flask, render_template_string

SUPERVISOR_TOKEN = os.environ.get("SUPERVISOR_TOKEN")
HA_URL = "http://supervisor/core/api"

HEADERS = {
    "Authorization": f"Bearer {SUPERVISOR_TOKEN}",
    "Content-Type": "application/json",
}

app = Flask(__name__)


def ha_get(path):
    r = requests.get(f"{HA_URL}{path}", headers=HEADERS, timeout=10)
    r.raise_for_status()
    return r.json()


def analyze_health(states):
    unavailable = []
    updates = []

    for s in states:
        entity_id = s.get("entity_id", "")
        state = s.get("state")
        attrs = s.get("attributes", {})

        if state in ("unavailable", "unknown"):
            unavailable.append(entity_id)

        if entity_id.startswith("update."):
            latest = attrs.get("latest_version")
            installed = attrs.get("installed_version")
            if state == "on" or (latest and installed and latest != installed):
                updates.append({
                    "entity_id": entity_id,
                    "installed": installed,
                    "latest": latest,
                })

    if len(unavailable) >= 10:
        severity = "critical"
    elif unavailable or updates:
        severity = "warning"
    else:
        severity = "healthy"

    return {
        "severity": severity,
        "unavailable": {
            "count": len(unavailable),
            "entities": unavailable[:50],
        },
        "updates": {
            "count": len(updates),
            "items": updates,
        },
    }


@app.route("/")
def index():
    try:
        config = ha_get("/config")
        states = ha_get("/states")
        health = analyze_health(states)

        data = {
            "ha_version": config.get("version"),
            "entity_count": len(states),
            "health": health,
        }
    except Exception as e:
        data = {
            "ha_version": "unknown",
            "entity_count": 0,
            "health": {
                "severity": "unknown",
                "error": str(e),
                "unavailable": {"count": 0, "entities": []},
                "updates": {"count": 0, "items": []},
            },
        }

    return render_template_string(TEMPLATE, data=data)


TEMPLATE = """
<!doctype html>
<html>
<head>
  <title>HomeOps Doctor</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 24px; }
    h1 { margin-bottom: 8px; }
    h2 { margin-top: 32px; }
    .cards { display: flex; gap: 16px; }
    .card { padding: 16px; border-radius: 8px; background: #f5f5f5; min-width: 160px; }
    .critical { color: #b00020; }
    .warning { color: #e65100; }
    .healthy { color: #2e7d32; }
    .unknown { color: #555; }
    .issue { padding: 12px; border-left: 4px solid #ccc; margin-bottom: 12px; background: #fafafa; }
    .issue.critical { border-color: #b00020; }
    .issue.warning { border-color: #e65100; }
  </style>
</head>
<body>

<h1>HomeOps Doctor</h1>
<p>Home Assistant {{ data.ha_version }} · {{ data.entity_count }} entities</p>

<h2>Health Summary</h2>
<div class="cards">
  <div class="card">
    <strong>Overall</strong><br>
    <span class="{{ data.health.severity }}">{{ data.health.severity | upper }}</span>
  </div>
  <div class="card">
    <strong>Unavailable</strong><br>
    {{ data.health.unavailable.count }}
  </div>
  <div class="card">
    <strong>Updates</strong><br>
    {{ data.health.updates.count }}
  </div>
</div>

<h2>Top Issues</h2>

{% if data.health.unavailable.count > 0 %}
<div class="issue critical">
  <strong>{{ data.health.unavailable.count }} entities unavailable</strong>
  <p>Likely causes: offline devices, network issues, failed integrations.</p>
</div>
{% endif %}

{% if data.health.updates.count > 0 %}
<div class="issue warning">
  <strong>{{ data.health.updates.count }} updates pending</strong>
  <p>Review release notes before upgrading.</p>
</div>
{% endif %}

{% if data.health.severity == "healthy" %}
<div class="issue healthy">No issues detected.</div>
{% endif %}

</body>
</html>
"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
