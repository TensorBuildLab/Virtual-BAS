r"""Random fault / event generator (the "chaos" source of the outer space).

Fault arrivals follow a homogeneous Poisson process with rate :math:`\lambda` [1/week]; the
type, target, magnitude and duration of each arrival are drawn from configurable
distributions. Every generated injection is labelled with ``source="random"``. This module
is also the reference implementation of an *AI injector*: any agent that can produce the
same JSON dictionaries can drive the virtual BAS through the REST API.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .faults import Injection

# type -> (target selector, parameter samplers, duration range in hours, profile choices)
DEFAULT_MENU: dict[str, dict[str, Any]] = {
    "sensor_bias": {"targets": "sensor:temp", "params": {"bias": ("choice", [-3, -2, -1.5, 1.5, 2, 3])}, "hours": (24, 240)},
    "sensor_drift": {"targets": "sensor:temp", "params": {"rate_per_day": ("uniform", -0.6, 0.6)}, "hours": (72, 480)},
    "sensor_stuck": {"targets": "sensor:any", "params": {}, "hours": (6, 96)},
    "sensor_dropout": {"targets": "sensor:any", "params": {"prob": ("choice", [0.3, 1.0])}, "hours": (1, 48)},
    "sensor_noise": {"targets": "sensor:temp", "params": {"std": ("uniform", 0.5, 2.0)}, "hours": (12, 120)},
    "vav_damper_stuck": {"targets": "equip:VAV", "params": {"position": ("choice", [0, 20, 50, 100])}, "hours": (24, 240)},
    "reheat_valve_stuck_closed": {"targets": "equip:VAV", "params": {}, "hours": (24, 120)},
    "oa_damper_stuck": {"targets": "equip:AHU", "params": {"position": ("choice", [0, 15, 100])}, "hours": (24, 240)},
    "filter_fouling": {"targets": "equip:AHU", "params": {"dp_add": ("uniform", 100, 350)}, "hours": (240, 720), "profile": "ramp"},
    "fan_degradation": {"targets": "equip:AHU", "params": {"loss": ("uniform", 0.1, 0.35)}, "hours": (240, 720), "profile": "ramp"},
    "chiller_fouling": {"targets": "equip:Chiller", "params": {"ratio": ("uniform", 0.55, 0.85)}, "hours": (240, 720), "profile": "ramp"},
    "schedule_error_always_on": {"targets": "equip:AHU", "params": {}, "hours": (24, 168)},
    "economizer_disabled": {"targets": "equip:AHU", "params": {}, "hours": (48, 336)},
    "comm_loss": {"targets": "equip:VAV", "params": {}, "hours": (0.5, 12)},
    "occupancy_surge": {"targets": "zone", "params": {"multiplier": ("choice", [0.2, 1.5, 2.0])}, "hours": (1, 6)},
    "window_open": {"targets": "zone", "params": {"ach": ("uniform", 0.5, 3.0)}, "hours": (1, 10)},
}


@dataclass
class RandomInjector:
    rate_per_week: float = 2.0
    menu: dict[str, dict[str, Any]] = field(default_factory=lambda: dict(DEFAULT_MENU))
    seed: int = 0

    def __post_init__(self):
        self.rng = np.random.default_rng(self.seed)
        self.next_time: dt.datetime | None = None

    def _sample(self, spec):
        kind = spec[0]
        if kind == "uniform":
            return float(self.rng.uniform(spec[1], spec[2]))
        if kind == "choice":
            return self.rng.choice(spec[1]).item()
        return spec

    def _targets(self, sel: str, catalog) -> list[str]:
        if sel == "sensor:temp":
            return [p.id for p in catalog.points.values() if p.kind == "sensor" and p.unit == "degC" and not p.meta.get("surrogate")]
        if sel == "sensor:any":
            return [p.id for p in catalog.points.values() if p.kind == "sensor" and not p.meta.get("surrogate")]
        if sel.startswith("sensor:") and sel.count(":") == 2:
            # sensor:<EquipType>:<unit>  e.g. sensor:AHU:degC
            _, et, unit = sel.split(":")
            return [p.id for p in catalog.points.values() if p.kind == "sensor" and p.equip_type == et
                    and unit in ("*", p.unit) and not p.meta.get("surrogate")]
        if sel.startswith("equip:"):
            return [e.id for e in catalog.equipment.values() if e.type == sel.split(":", 1)[1]]
        if sel == "zone":
            return [e.id for e in catalog.equipment.values() if e.type == "Zone"]
        return []

    def poll(self, t: dt.datetime, catalog) -> list[Injection]:
        """Return injections that start at time ``t`` (call once per step)."""
        out: list[Injection] = []
        if self.rate_per_week <= 0:
            return out
        if self.next_time is None:
            self.next_time = t + dt.timedelta(hours=float(self.rng.exponential(168.0 / self.rate_per_week)))
        while t >= self.next_time:
            ftype = self.rng.choice(sorted(self.menu))
            spec = self.menu[ftype]
            targets = self._targets(spec["targets"], catalog)
            if targets:
                target = str(self.rng.choice(targets))
                if spec["targets"] == "zone":
                    target = catalog.zone_of_equip.get(target, target)
                h = float(self.rng.uniform(*spec["hours"]))
                params = {k: self._sample(v) for k, v in spec["params"].items()}
                profile = spec.get("profile", "step")
                out.append(Injection(type=str(ftype), target=target, start=t, end=t + dt.timedelta(hours=h), profile=profile,
                                     ramp_s=h * 3600 * 0.5, params=params, source="random"))
            self.next_time = self.next_time + dt.timedelta(hours=float(self.rng.exponential(168.0 / self.rate_per_week)))
        return out
