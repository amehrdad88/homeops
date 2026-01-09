import os
from flask import Flask, jsonify, render_template

from app.ha_client import HAClient
from app.health.analyzer import analyze_health, build_report

def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "static"),
    )

    client = HAClient()

    @app.get("/")
    def index():
        data = _build_data(client)
        return render_template("index.html", data=data)

    @app.get("/api/report")
    def api_report():
        return jsonify(_build_data(client))

    return app

def _build_data(client: HAClient):
    try:
        config = client.get_config()
        states = client.get_states()
        health = analyze_health(states)
        report = build_report(health)
        return {
            "ha_version": config.get("version", "unknown"),
            "entity_count": len(states),
            "health": health,
            "report": report,
        }
    except Exception as exc:
        return {
            "ha_version": "unknown",
            "entity_count": 0,
            "health": {
                "severity": "unknown",
                "unavailable": {"total_count": 0, "critical_count": 0, "by_domain": {}},
                "updates": {"count": 0, "items": []},
            },
            "report": {
                "headline": "HomeOps can’t reach Home Assistant right now",
                "severity": "unknown",
                "description": str(exc),
                "start_here": [
                    "Open HomeOps add-on logs to confirm it’s running.",
                    "Confirm `homeassistant_api: true` is enabled for the add-on.",
                ],
                "details": "",
            },
        }
