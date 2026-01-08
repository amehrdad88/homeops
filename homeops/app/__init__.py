"""Flask application factory for HomeOps Doctor.

This module exposes a `create_app()` function that constructs a Flask
application configured to serve both HTML and JSON responses.  It binds
routes for the main dashboard and for an API endpoint that returns the
raw health report as JSON.  The factory pattern makes it easy to test
and extend the application in the future.
"""

from __future__ import annotations

import os
from flask import Flask, jsonify, render_template

from .ha_client import HAClient
from .health.analyzer import analyze_health, build_report


def create_app() -> Flask:
    """Construct and configure the Flask app.

    The app will read the Home Assistant API token from the `SUPERVISOR_TOKEN`
    environment variable, query `/api/config` and `/api/states` via the
    internal Supervisor proxy, and produce a health report.  The report
    contains a headline, a short start‑here action list, and some
    supporting details.  The HTML template then renders the report
    minimally, emphasising the headline and next action.
    """

    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "static"),
    )

    client = HAClient()

    @app.route("/")
    def index() -> str:
        """Render the HomeOps dashboard.

        On each request, fetch the latest Home Assistant configuration and
        state, compute a health report, and render the template.  If
        anything goes wrong (e.g. the API is unavailable), the
        `analyze_health` function will catch exceptions and return a
        placeholder report indicating unknown state.
        """
        try:
            config = client.get_config()
            states = client.get_states()
            health = analyze_health(states)
            report = build_report(health)
            data = {
                "ha_version": config.get("version"),
                "entity_count": len(states),
                "health": health,
                "report": report,
            }
        except Exception as exc:  # pylint: disable=broad-except
            # If anything goes wrong, fail gracefully and mark state unknown
            data = {
                "ha_version": "unknown",
                "entity_count": 0,
                "health": {
                    "severity": "unknown",
                    "unavailable": {
                        "total_count": 0,
                        "critical_count": 0,
                        "by_domain": {},
                    },
                    "updates": {"count": 0, "items": []},
                },
                "report": {
                    "headline": "Unable to determine health",
                    "description": str(exc),
                    "start_here": [],
                    "details": "",
                },
            }
        return render_template("index.html", data=data)

    @app.route("/api/report")
    def api_report() -> "flask.Response":
        """Return the raw health report as JSON.

        This endpoint can be used by tools or support personnel to
        programmatically retrieve a full diagnostic snapshot.  It
        contains the same information used by the HTML dashboard, but
        without any of the presentation logic.
        """
        try:
            config = client.get_config()
            states = client.get_states()
            health = analyze_health(states)
            report = build_report(health)
            data = {
                "ha_version": config.get("version"),
                "entity_count": len(states),
                "health": health,
                "report": report,
            }
        except Exception as exc:  # pylint: disable=broad-except
            data = {
                "ha_version": "unknown",
                "entity_count": 0,
                "health": {
                    "severity": "unknown",
                    "unavailable": {
                        "total_count": 0,
                        "critical_count": 0,
                        "by_domain": {},
                    },
                    "updates": {"count": 0, "items": []},
                },
                "report": {
                    "headline": "Unable to determine health",
                    "description": str(exc),
                    "start_here": [],
                    "details": "",
                },
            }
        return jsonify(data)

    return app