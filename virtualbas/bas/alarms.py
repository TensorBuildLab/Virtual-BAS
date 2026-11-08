"""Rule-based BAS alarm engine operating on *observed* present values.

Like a real BAS, alarms are raised from what the BAS sees, so sensor faults can cause false
alarms and hide real problems. Each rule has a condition and an on-delay.
"""
from __future__ import annotations

import datetime as dt
import math
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class AlarmRule:
    id: str
    equip: str
    message: str
    severity: str
    condition: Callable[[dict[str, float], dict[str, float]], bool]
    delay_s: float = 1800.0
    _since: dt.datetime | None = None
    active: bool = False


@dataclass
class AlarmEngine:
    rules: list[AlarmRule] = field(default_factory=list)
    history: list[dict] = field(default_factory=list)

    def evaluate(self, t: dt.datetime, pv: dict[str, float], cmd: dict[str, float]) -> list[dict]:
        for r in self.rules:
            try:
                cond = bool(r.condition(pv, cmd))
            except Exception:  # noqa: BLE001
                cond = False
            if cond:
                if r._since is None:
                    r._since = t
                if not r.active and (t - r._since).total_seconds() >= r.delay_s:
                    r.active = True
                    self.history.append({"time": t.isoformat(), "id": r.id, "equip": r.equip, "state": "ALARM",
                                         "severity": r.severity, "message": r.message})
            else:
                if r.active:
                    self.history.append({"time": t.isoformat(), "id": r.id, "equip": r.equip, "state": "NORMAL",
                                         "severity": r.severity, "message": r.message})
                r._since = None
                r.active = False
        return self.active()

    def active(self) -> list[dict]:
        return [{"id": r.id, "equip": r.equip, "message": r.message, "severity": r.severity,
                 "since": r._since.isoformat() if r._since else None} for r in self.rules if r.active]


def _g(d, k):
    v = d.get(k, math.nan)
    return v if v is not None else math.nan


def default_rules(catalog) -> AlarmEngine:
    eng = AlarmEngine()
    for e in catalog.equipment.values():
        if e.type == "Zone":
            z = e.id
            eng.rules.append(AlarmRule(f"{z}:HIGH-T", z, "Zone temperature high (> cooling SP + 2 K)", "medium",
                                       lambda pv, c, z=z: _g(pv, f"{z}/ZN-T") > _g(c, f"{z}/CLG-SP") + 2.0, 1800))
            eng.rules.append(AlarmRule(f"{z}:LOW-T", z, "Zone temperature low (< heating SP - 2 K)", "medium",
                                       lambda pv, c, z=z: _g(pv, f"{z}/ZN-T") < _g(c, f"{z}/HTG-SP") - 2.0, 1800))
            if f"{z}/ZN-CO2" in catalog.points:
                eng.rules.append(AlarmRule(f"{z}:HIGH-CO2", z, "Zone CO2 above 1100 ppm", "low",
                                           lambda pv, c, z=z: _g(pv, f"{z}/ZN-CO2") > 1100, 900))
        elif e.type == "AHU":
            a = e.id
            eng.rules.append(AlarmRule(f"{a}:SAT-DEV", a, "Supply air temperature deviates > 2 K from set point", "high",
                                       lambda pv, c, a=a: c.get(f"{a}/SF-CMD", 0) > 0.5 and
                                       abs(_g(pv, f"{a}/SA-T") - _g(c, f"{a}/SA-T-SP")) > 2.0, 1800))
            eng.rules.append(AlarmRule(f"{a}:FAN-FAIL", a, "Supply fan commanded on but status off", "critical",
                                       lambda pv, c, a=a: c.get(f"{a}/SF-CMD", 0) > 0.5 and _g(pv, f"{a}/SF-STS") < 0.5, 600))
            eng.rules.append(AlarmRule(f"{a}:FILTER", a, "Filter differential pressure high", "low",
                                       lambda pv, c, a=a: _g(pv, f"{a}/FLT-DP") > 250, 3600))
        elif e.type == "PlantLoop" and e.id == "CHW-SYS":
            eng.rules.append(AlarmRule("CHW-SYS:ST-DEV", e.id, "Chilled water supply temperature > SP + 1.5 K", "high",
                                       lambda pv, c: _g(pv, "CHW-SYS/CHW-ST") > _g(c, "CHW-SYS/CHW-ST-SP") + 1.5
                                       and _g(pv, "CHW-SYS/CHW-F") > 1.0, 1800))
        elif e.type == "PlantLoop" and e.id == "HW-SYS":
            eng.rules.append(AlarmRule("HW-SYS:ST-DEV", e.id, "Hot water supply temperature < SP - 5 K", "high",
                                       lambda pv, c: _g(pv, "HW-SYS/HW-ST") < _g(c, "HW-SYS/HW-ST-SP") - 5.0
                                       and _g(pv, "HW-SYS/HW-F") > 0.5, 1800))
    return eng
