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

    def get(self, path: str):
        r = requests.get(f"{HA_BASE}{path}", headers=self._headers, timeout=self._timeout)
        r.raise_for_status()
        return r.json()

    def config(self):
        return self.get("/config")

    def states(self):
        return self.get("/states")

    def error_log(self):
        # Optional; may require permission depending on HA config
        return self.get("/error_log")
