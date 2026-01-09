import os
import requests

SUPERVISOR_TOKEN = os.environ.get("SUPERVISOR_TOKEN")
HA_BASE = "http://supervisor/core/api"

class HAClient:
    def __init__(self, timeout_s: int = 10):
        if not SUPERVISOR_TOKEN:
            raise RuntimeError("SUPERVISOR_TOKEN is not set. Ensure homeassistant_api: true in add-on config.")
        self._headers = {
            "Authorization": f"Bearer {SUPERVISOR_TOKEN}",
            "Content-Type": "application/json",
        }
        self._timeout = timeout_s

    def _get(self, path: str):
        r = requests.get(f"{HA_BASE}{path}", headers=self._headers, timeout=self._timeout)
        r.raise_for_status()
        return r.json()

    def get_config(self):
        return self._get("/config")

    def get_states(self):
        return self._get("/states")
