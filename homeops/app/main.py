import os
from flask import Flask, jsonify, render_template
from app.ha_client import HAClient
from app.health.analyzer import build_report

def create_app() -> Flask:
    app = Flask(__name__, template_folder="../templates", static_folder="../static")

    @app.get("/")
    def index():
        report_dict = _get_report()
        return render_template("index.html", data=report_dict)

    @app.get("/api/report")
    def api_report():
        return jsonify(_get_report())

    def _get_report():
        try:
            ha = HAClient(timeout_s=10)
            config = ha.config()
            states = ha.states()
            report = build_report(ha_version=config.get("version"), states=states)
            # Convert dataclasses to dict (without extra dependency)
            return _dataclass_to_dict(report)
        except Exception as e:
            return {
                "ha_version": "unknown",
                "entity_count": 0,
                "severity": "unknown",
                "generated_at_iso": "",
                "error": str(e),
                "unavailable": {"total_count": 0, "critical_count": 0, "by_domain": {}, "sample_entities": []},
                "updates": {"count": 0, "items": []},
                "issues": [
                    {
                        "id": "unknown",
                        "title": "Health status could not be determined",
                        "severity": "unknown",
                        "summary": "HomeOps could not query Home Assistant. Check add-on logs and Supervisor connectivity.",
                        "start_here": ["Open the HomeOps add-on logs and verify it is running."],
                        "evidence": {"error": str(e)},
                    }
                ],
            }

    return app

def _dataclass_to_dict(obj):
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    if isinstance(obj, list):
        return [_dataclass_to_dict(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _dataclass_to_dict(v) for k, v in obj.items()}
    if hasattr(obj, "__dict__"):
        return {k: _dataclass_to_dict(v) for k, v in obj.__dict__.items()}
    return str(obj)

if __name__ == "__main__":
    port = int(os.environ.get("INGRESS_PORT", "8000"))
    app = create_app()
    app.run(host="0.0.0.0", port=port)
