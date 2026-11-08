"""Minimal Python client for a running Virtual BAS server (``vbas serve``).

Uses only the standard library so that any agent runtime can import it::

    from virtualbas.ai.client import VBASClient
    bas = VBASClient("http://127.0.0.1:8000")
    print(bas.read(["AHU-1/SA-T", "ZN-Core_mid/ZN-T"]))
    bas.inject("sensor_drift", "ZN-Core_mid/ZN-T", params={"rate_per_day": 0.5}, duration="7d", source="ai")
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any


class VBASClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000", timeout: float = 30.0):
        self.base = base_url.rstrip("/")
        self.timeout = timeout

    # ------------------------------------------------------------------ http
    def _req(self, method: str, path: str, body: Any = None, params: dict[str, Any] | None = None) -> Any:
        url = self.base + path
        if params:
            url += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            return json.loads(r.read().decode() or "null")

    # ------------------------------------------------------------------ read
    def info(self) -> dict:
        return self._req("GET", "/api/info")

    def status(self) -> dict:
        return self._req("GET", "/api/status")

    def points(self, equip: str | None = None, kind: str | None = None, tier: str | None = None) -> list[dict]:
        return self._req("GET", "/api/points", params={"equip": equip, "kind": kind, "tier": tier})

    def forecast(self, hours: int = 48) -> dict:
        """Hourly weather forecast for the next ``hours`` hours (as issued by the weather service)."""
        return self._req("GET", "/api/forecast", params={"hours": hours})

    def equipment(self) -> list[dict]:
        return self._req("GET", "/api/equipment")

    def snapshot(self, truth: bool = False) -> dict:
        return self._req("GET", "/api/snapshot", params={"truth": str(truth).lower()})

    def read(self, points: list[str], truth: bool = False) -> dict:
        return self._req("GET", "/api/read", params={"points": ",".join(points), "truth": str(truth).lower()})

    def trend(self, points: list[str], n: int = 288, source: str = "observed") -> dict:
        return self._req("GET", "/api/trend", params={"points": ",".join(points), "n": n, "source": source})

    def alarms(self) -> dict:
        return self._req("GET", "/api/alarms")

    # ------------------------------------------------------------------ write / control
    def write(self, point: str, value: float | None, priority: int = 10, duration_s: float | None = None,
              source: str = "ai") -> dict:
        return self._req("POST", "/api/write", {"point": point, "value": value, "priority": priority,
                                                 "duration_s": duration_s, "source": source})

    def control(self, action: str, value: Any = None) -> dict:
        return self._req("POST", "/api/control", {"action": action, "value": value})

    def pause(self):
        return self.control("pause")

    def resume(self):
        return self.control("resume")

    def step(self, n: int = 1):
        return self.control("step", n)

    def set_speed(self, speed: str | float):
        return self.control("speed", speed)

    # ------------------------------------------------------------------ faults & events
    def fault_catalog(self) -> list[dict]:
        return self._req("GET", "/api/faults/catalog")

    def injections(self) -> list[dict]:
        return self._req("GET", "/api/injections")

    def inject(self, type: str, target: str = "building", params: dict | None = None, start: str = "now",
               duration: str | None = None, end: str | None = None, profile: str = "step", source: str = "ai",
               note: str = "", ramp_s: float = 3600.0) -> dict:
        return self._req("POST", "/api/injections", {"type": type, "target": target, "params": params or {},
                                                      "start": start, "duration": duration, "end": end,
                                                      "profile": profile, "source": source, "note": note,
                                                      "ramp_s": ramp_s})

    def clear(self, inj_id: str) -> dict:
        return self._req("DELETE", f"/api/injections/{inj_id}")

    def new_session(self, scenario: dict, speed: str = "60x") -> dict:
        return self._req("POST", "/api/session", {"scenario": scenario, "speed": speed})
