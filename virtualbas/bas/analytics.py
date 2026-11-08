"""BAS-side calculated ("virtual") points.

Real BAS front-ends compute many values from the *present values* of physical points: run-hours,
start counts, chiller kW/ton, cooling-tower approach and range, outdoor-air fraction from the mixing
temperatures, 15-minute electric demand and its monthly peak, degree-days, ... Because they are computed
from observed values, sensor errors propagate into them exactly as in a real building (e.g. a biased
return-air sensor corrupts the calculated OA fraction). The definitions follow common BAS practice.
"""
from __future__ import annotations

import datetime as dt
import math
from collections import deque
from typing import Any

TON_KW = 3.51685          # 1 refrigeration ton in kW
CP_W = 4.186              # kJ/(kg K)
RHO_W = 998.0


def _ok(x) -> bool:
    return x is not None and isinstance(x, (int, float)) and math.isfinite(x)


class Analytics:
    def __init__(self, catalog):
        self.cat = catalog
        self.status_points = [p for p in catalog.points.values()
                              if p.kind == "sensor" and p.sensor_class == "binary" and p.name.endswith("STS")
                              and p.equip_type in ("AHU", "Pump", "Chiller", "Boiler", "CoolingTower")]
        self.runhrs: dict[str, float] = {p.id: 0.0 for p in self.status_points}
        self.starts: dict[str, int] = {p.id: 0 for p in self.status_points}
        self.last: dict[str, float] = {}
        self.dmd: deque = deque()
        self.peak_month = 0.0
        self.peak_day = 0.0
        self.month = None
        self.day = None
        self.dd = {"hdd": 0.0, "cdd": 0.0}

    @staticmethod
    def _rn(name: str) -> str:
        # SF-STS -> SF-RUNHRS, STS -> RUNHRS, FAN-STS -> FAN-RUNHRS
        return name[:-3]

    def step(self, t: dt.datetime, dts: float, pv: dict[str, float], out: dict[str, float]) -> None:
        h = dts / 3600.0
        # ---- run-hours and starts from observed status
        for p in self.status_points:
            v = pv.get(p.id)
            on = _ok(v) and v > 0.5
            if on:
                self.runhrs[p.id] += h
            if on and self.last.get(p.id, 0.0) < 0.5:
                self.starts[p.id] += 1
            self.last[p.id] = 1.0 if on else 0.0
            pre = self._rn(p.name)
            out[f"{p.equip}/{pre}RUNHRS"] = self.runhrs[p.id]
            out[f"{p.equip}/{pre}STARTS"] = float(self.starts[p.id])
        g = pv.get
        # ---- AHU calculations
        for a in self.cat.equipment_of_type("AHU"):
            i = a.id
            oat, rat, mat = g("WX/OA-T"), g(f"{i}/RA-T"), g(f"{i}/MA-T")
            if _ok(oat) and _ok(rat) and _ok(mat) and abs(rat - oat) > 2.0:
                out[f"{i}/OA-FRAC-CALC"] = max(-50.0, min(150.0, 100.0 * (rat - mat) / (rat - oat)))
            else:
                out[f"{i}/OA-FRAC-CALC"] = math.nan
            saf, oaf = g(f"{i}/SA-F"), g(f"{i}/OA-F")
            if _ok(saf) and _ok(oaf) and saf > 0.05:
                out[f"{i}/OA-FRAC-AFMS"] = 100.0 * oaf / saf
            else:
                out[f"{i}/OA-FRAC-AFMS"] = math.nan
            kw = g(f"{i}/SF-KW")
            out[f"{i}/SF-W-PER-CMS"] = 1000.0 * kw / saf if _ok(kw) and _ok(saf) and saf > 0.05 else math.nan
        # ---- chillers
        for c in self.cat.equipment_of_type("Chiller"):
            kw, load = g(f"{c.id}/KW"), g(f"{c.id}/LOAD")
            out[f"{c.id}/KW-TON"] = kw / (load / TON_KW) if _ok(kw) and _ok(load) and load > 5.0 else math.nan
            out[f"{c.id}/LOAD-TONS"] = load / TON_KW if _ok(load) else math.nan
        # ---- towers
        for c in self.cat.equipment_of_type("CoolingTower"):
            lwt, ewt, wb = g(f"{c.id}/LWT"), g(f"{c.id}/EWT"), g("WX/OA-WB")
            out[f"{c.id}/APPROACH"] = lwt - wb if _ok(lwt) and _ok(wb) else math.nan
            out[f"{c.id}/RANGE"] = ewt - lwt if _ok(lwt) and _ok(ewt) else math.nan
        # ---- plant
        plant_kw = 0.0
        for e in self.cat.equipment.values():
            if e.type == "Chiller":
                plant_kw += g(f"{e.id}/KW") if _ok(g(f"{e.id}/KW")) else 0.0
            elif e.type == "CoolingTower":
                plant_kw += g(f"{e.id}/FAN-KW") if _ok(g(f"{e.id}/FAN-KW")) else 0.0
            elif e.type == "Pump" and e.parent in ("CHW-SYS", "CW-SYS"):
                plant_kw += g(f"{e.id}/KW") if _ok(g(f"{e.id}/KW")) else 0.0
        for pl in self.cat.equipment_of_type("PlantLoop"):
            pre = pl.id.split("-")[0]
            st, rt, fl = g(f"{pl.id}/{pre}-ST"), g(f"{pl.id}/{pre}-RT"), g(f"{pl.id}/{pre}-F")
            if _ok(st) and _ok(rt):
                out[f"{pl.id}/{pre}-DT"] = (rt - st) if pre != "HW" else (st - rt)
            else:
                out[f"{pl.id}/{pre}-DT"] = math.nan
            if pre == "CHW":
                dtw = out[f"{pl.id}/{pre}-DT"]
                load = fl / 1000.0 * RHO_W * CP_W * dtw if _ok(fl) and _ok(dtw) else math.nan
                out[f"{pl.id}/CHW-TONS"] = load / TON_KW if _ok(load) else math.nan
                out[f"{pl.id}/PLANT-KW-TON"] = plant_kw / (load / TON_KW) if _ok(load) and load > 20.0 else math.nan
        # ---- demand, degree-days
        if self.month != t.month:
            self.month, self.peak_month = t.month, 0.0
        if self.day != t.date():
            self.day, self.peak_day, self.dd = t.date(), 0.0, {"hdd": 0.0, "cdd": 0.0}
        kw = g("MTR/BLDG-ELEC-KW")
        if _ok(kw):
            self.dmd.append((t, kw))
        while self.dmd and (t - self.dmd[0][0]).total_seconds() >= 900.0:
            self.dmd.popleft()
        d15 = sum(v for _, v in self.dmd) / len(self.dmd) if self.dmd else math.nan
        if _ok(d15):
            self.peak_month = max(self.peak_month, d15)
            self.peak_day = max(self.peak_day, d15)
        out["MTR/BLDG-DMD-15"] = d15
        out["MTR/PEAK-DMD-DAY"] = self.peak_day
        out["MTR/PEAK-DMD-MONTH"] = self.peak_month
        oat = g("WX/OA-T")
        if _ok(oat):
            self.dd["hdd"] += max(0.0, 18.0 - oat) * dts / 86400.0
            self.dd["cdd"] += max(0.0, oat - 18.0) * dts / 86400.0
        out["WX/HDD-TODAY"] = self.dd["hdd"]
        out["WX/CDD-TODAY"] = self.dd["cdd"]
        # ---- VAV terminal state, G36 requests and low-flow alarm
        for v in self.cat.equipment_of_type("VAV"):
            i = v.id
            zid = v.meta.get("zone_equip")
            clg, htg = out.get(f"{i}/CLG-LOOP", 0.0), out.get(f"{i}/HTG-LOOP", 0.0)
            out[f"{i}/ZN-MODE"] = 1.0 if clg > 0.5 else (2.0 if htg > 0.5 else 0.0)
            tz, csp, hsp = g(f"{zid}/ZN-T"), out.get(f"{zid}/CLG-SP"), out.get(f"{zid}/HTG-SP")
            # G36 5.6.8: cooling SAT requests 3/2/1 by zone temperature above set point or loop saturation
            r = 0
            if _ok(tz) and csp is not None:
                r = 3 if tz > csp + 3.0 else 2 if tz > csp + 2.0 else 1 if clg > 95.0 else 0
            out[f"{i}/CLG-REQ"] = float(r)
            sp, fl = out.get(f"{i}/DA-F-SP"), g(f"{i}/DA-F")
            dmp = out.get(f"{i}/DMPR-CMD", 0.0)
            r = 0
            if sp and _ok(fl) and sp > 0.0:
                r = 3 if (fl < 0.5 * sp and dmp > 95) else 2 if (fl < 0.7 * sp and dmp > 95) else 1 if dmp > 95 else 0
            out[f"{i}/PRS-REQ"] = float(r)
            r = 0
            if _ok(tz) and hsp is not None:
                r = 3 if tz < hsp - 3.0 else 2 if tz < hsp - 2.0 else 1 if htg > 95.0 else 0
            out[f"{i}/HW-REQ"] = float(r)
            # evaluated only while the serving fan is commanded on and proven (status) - G36 5.6.6
            aid = v.parent
            fan_ok = out.get(f"{aid}/SF-CMD", 1.0) > 0.5 and (g(f"{aid}/SF-STS") or 0.0) > 0.5 if aid else True
            low = bool(fan_ok and sp and _ok(fl) and sp > 0.02 and fl < 0.7 * sp)
            k = f"{i}/LOW-FLOW"
            self._lowflow = getattr(self, "_lowflow", {})
            # timer starts at the first low sample: the alarm needs the condition to persist for 5 minutes
            self._lowflow[k] = (self._lowflow[k] + dts if k in self._lowflow else 0.0) if low else None
            if self._lowflow[k] is None:
                del self._lowflow[k]
            out[f"{i}/LOW-FLOW-ALM"] = 1.0 if self._lowflow.get(k, 0.0) >= 300.0 else 0.0
        # building occupancy (people counters)
        n = 0.0
        for z in self.cat.equipment_of_type("Zone"):
            v = g(f"{z.id}/OCC-COUNT")
            if _ok(v):
                n += v * float(z.meta.get("multiplier", 1) or 1)
        out["BLDG/OCC-COUNT"] = n

    def state(self) -> dict[str, Any]:
        return {"runhrs": self.runhrs, "starts": self.starts, "peak_month_kw": self.peak_month}
