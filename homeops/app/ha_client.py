"""Wrapper for Home Assistant Supervisor API.

Home Assistant add-ons run inside a Supervisor-managed container that
proxies API requests through `http://supervisor/core/api`.  This
module wraps that proxy and handles authentication using the
`SUPERVISOR_TOKEN` environment variable.  It exposes helper
functions to fetch configuration and state information from Home
Assistant.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List

import requests


class HAClient:
    """Minimal client for accessing Home Assistant's REST API via the Supervisor proxy."""

    def __init__(self) -> None:
        token = os.environ.get("SUPERVISOR_TOKEN")
        if not token:
            raise RuntimeError(
                "SUPERVISOR_TOKEN environment variable is not set. This add‑on must run under the Supervisor."
            )
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        # Endpoint for the Supervisor proxy; see https://www.home-assistant.io/add-ons/communicating-with-home-assistant
        self._base_url = "http://supervisor/core/api"

    def _request(self, path: str) -> Any:
        """Internal helper to issue a GET request and return JSON."""
        url = f"{self._base_url}{path}"
        resp = requests.get(url, headers=self._headers, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def get_config(self) -> Dict[str, Any]:
        """Return the Home Assistant config information (version, location, etc.)."""
        return self._request("/config")

    def get_states(self) -> List[Dict[str, Any]]:
        """Return the list of all entity states."""
        return self._request("/states")