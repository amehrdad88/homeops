import os
import requests
from collections import defaultdict
from flask import Flask, render_template_string

# =============================
# Home Assistant API setup
# =============================

SUPERVISOR_TOKEN = os.environ.get("SUPERVISOR_TOKEN")
HA_URL = "http://supervisor/core/api"

HEADERS = {
    "Authorization": f"Bearer {SUPERVISOR_TOKEN}",
    "Content-Type": "application/json",
}

app = Flask(__name__)

# Domains that usually represent "real world breakage"
IMPORTANT_DOMAINS = {
    "light",
    "switch",
    "lock",
    "climate",
    "cover",
    "fan",
    "media_player",
}

# =============================
# Helper functions
# =============================

def ha_get(path):
    r = requests.get(f"{HA_URL}{path}", headers=HEADERS, timeout=10)
    r.raise_for_status()
    return r.json()


def analyze_health(states):
    unavailable = []
    unavailable_by_domain = defaultdict(list)
    critical_unavailable = []
    updates = []

    for s in states:
        entity_id = s.get("entity_id", "")
        state = s.get("state")
        attrs = s.get("attributes", {})

        domain = entity_id.split(".")[0] if "." in entity_id else "unknown"

        # --- Unavailable entities ---
        if state in ("unavailable", "unknown"):
            unavailable.append(entity_id)
            unavailable_by_domain[domain].append(entity_id)

            if domain in IMPORTANT_DOMAINS:
                critical_unavailable.append(entity_id)

        # --- Pending updates ---
        if entity_id.startswith("update."):
            latest = attrs.get("latest_version")
            installed = attrs.get("installed_version")

            if state == "on" or (latest and installed and latest != installed):
                updates.append({
                    "entity_id": entity_id,
                    "installed": installed,
                    "latest": latest,
                })

    # --- Severity logic ---
    if len(critical_unavailable) >= 5:
        severity = "critical"
    elif critical_unavailable or updates:
        severity = "warning"
    else:
        severity = "healthy"

    return {
        "severity": severity,
        "unavailable": {
            "total_count": len(unavailable),
            "critical_count": len(critical_unavailable),
            "by_domain": {
                domain: len(entities)
                for domain, entities in sorted(
                    unavailable_by_domain.items(),
                    key=lambda x: len(x[1]),
                    reverse=True
                )
            },
        },
        "updates": {
            "count": len(updates),
            "items": updates,
        },
    }


# =============================
# Routes
# =============================

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
                "unavailable": {
                    "total_count": 0,
                    "critical_count": 0,
                    "by_domain": {},
                },
                "updates": {
                    "count": 0,
                    "items": [],
                },
            },
        }

    return render_template_string(TEMPLATE, data=data)


# =============================
# UI Template
# =============================

TEMPLATE = """
<!doctype html>
<html>
<head>
  <title>HomeOps Doctor</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 24px; background: #f4f6f8; }
    h1 { margin-bottom: 4px; }
    h2 { margin-top: 32px; }

    .cards { display: flex; gap: 16px; margin-top: 16px; }
    .card {
      padding: 16px;
      border-radius: 8px;
      background: white;
      min-width: 180px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }

    .critical { color: #b00020; }
    .warning { color: #e65100; }
    .healthy { color: #2e7d32; }
    .unknown { color: #555; }

    .issue {
      padding: 16px;
      border-left: 4px solid #ccc;
      margin-bottom: 16px;
      background: white;
      box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    .issue.critical { border-color: #b00020; }
    .issue.warning { border-color: #e65100; }

    table {
      border-collapse: collapse;
      margin-top: 8px;
    }
    td {
      padding: 4px 12px 4px 0;
    }
  </style>
</head>
<body>

<h1>HomeOps Doctor</h1>
<p>
  Home Assistant {{ data.ha_version }} · {{ data.entity_count }} entities
</p>

<h2>Health Summary</h2>

<div class="cards">
  <div class="card">
    <strong>Overall</strong><br>
    <span class="{{ data.health.severity }}">
      {{ data.health.severity | upper }}
    </span>
  </div>

  <div class="card">
    <strong>Unavailable</strong><br>
    {{ data.health.unavailable.total_count }}
  </div>

  <div class="card">
    <strong>Critical Unavailable</strong><br>
    {{ data.health.unavailable.critical_count }}
  </div>

  <div class="card">
    <strong>Updates</strong><br>
    {{ data.health.updates.count }}
  </div>
</div>

<h2>Top Issues</h2>

{% if data.health.unavailable.critical_count > 0 %}
<div class="issue critical">
  <strong>
    {{ data.health.unavailable.critical_count }} critical devices unavailable
  </strong>
  <p>
    These affect core functionality (lights, climate, locks, media).
  </p>
  <p>
    Most affected domains:
  </p>
  <table>
    {% for domain, count in data.health.unavailable.by_domain.items() %}
      <tr>
        <td>{{ domain }}</td>
        <td>{{ count }}</td>
      </tr>
    {% endfor %}
  </table>
</div>
{% endif %}

{% if data.health.updates.count > 0 %}
<div class="issue warning">
  <strong>{{ data.health.updates.count }} updates pending</strong>
  <p>
    Updates may introduce breaking changes.
  </p>
  <p>
    Recommended: review release notes before upgrading.
  </p>
</div>
{% endif %}

{% if data.health.severity == "healthy" %}
<div class="issue healthy">
  No issues detected. Your system looks healthy.
</div>
{% endif %}

{% if data.health.severity == "unknown" %}
<div class="issue">
  Health status could not be determined.
</div>
{% endif %}

</body>
</html>
"""

# =============================
# Entrypoint
# =============================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
