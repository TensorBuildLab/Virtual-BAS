r"""Extended indoor/outdoor environment of the outer space, driven by inner-space (EnergyPlus) flows.

EnergyPlus already solves heat, moisture and CO2 balances. A real BAS (and the next generation of
IEQ-aware building systems) also reports quantities EnergyPlus does not model. They are computed here
from the EnergyPlus state at every step, so they stay consistent with the simulated air flows,
occupants, lighting power and solar gains. Every model below is an explicit equation:

**Zone air quality (PM2.5, PM10, TVOC)** - well-mixed mass balance of zone :math:`z` with volume
:math:`V`, supply flow :math:`Q_s`, infiltration :math:`Q_i`, deposition/sink rate :math:`k` and
source :math:`S`:

.. math::

    V\,\frac{dC}{dt} = Q_s C_s + P\,Q_i\,C_o + S - (Q_s + Q_i + kV)\,C,
    \qquad C_s = (1-\eta)\big(x_{OA} C_o + (1-x_{OA})\,\bar C_{ret}\big)

with outdoor concentration :math:`C_o`, infiltration penetration :math:`P`, AHU outdoor-air fraction
:math:`x_{OA}`, filter efficiency :math:`\eta` and flow-weighted return concentration :math:`\bar C_{ret}`.
It is integrated exactly over the step, :math:`C^+ = C^\* + (C - C^\*)e^{-b\Delta t}`, with
:math:`b = (Q_s+Q_i)/V + k` and :math:`C^\* = (Q_s C_s + P Q_i C_o + S)/(bV)`.

**Outdoor PM** - log-normal Ornstein-Uhlenbeck process with a diurnal traffic factor plus smoke events,
:math:`C_o = \bar C\,e^{X - \sigma^2/2}\,(1 + a\cos(2\pi(h-h_p)/24)) + \Delta C_{smoke}`.

**Work-plane illuminance** - lumen method for electric light and daylight-flux method for daylight,
:math:`E = E_d\,P_{light}/P_{light,d} + K_v\,U\,\Phi_{sol}/A` with transmitted window solar
:math:`\Phi_{sol}`, luminous efficacy :math:`K_v` and utilisation factor :math:`U`.

**Background sound level** - energetic sum of HVAC (fan-law, 50 log10 of the flow ratio), occupant
speech and a background floor: :math:`L = 10\log_{10}\sum_j 10^{L_j/10}`.

**Occupant feedback** - thermal-sensation votes (app) and hot/cold complaints. Individual votes are
:math:`\mathrm{round}(\mathrm{PMV} + \sigma_i\,\varepsilon)` clipped to [-3, 3]; complaints are Poisson
with rate :math:`N\,r_c\,\mathrm{PPD}/100\cdot w_\pm(\mathrm{PMV})`.

**Weather forecast** - the weather file is the "future"; an hourly-issued forecast adds lead-time
dependent errors :math:`\sigma(h) = \sigma_0 + \sigma_\infty(1 - e^{-h/\tau})` that are AR(1) in issue time.

**Grid signals** - time-of-use tariff, synthetic marginal carbon intensity (diurnal + solar "duck" dip +
AR noise) and demand-response events.
"""
from __future__ import annotations

import datetime as dt
import math
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

MG_H_TO_UG_S = 1000.0 / 3600.0


# ----------------------------------------------------------------------------- configuration
@dataclass
class EnvConfig:
    # outdoor air quality
    pm25_out_mean: float = 8.0           # ug/m3, long-term mean outdoor PM2.5 (US urban)
    pm25_out_sigma: float = 0.5          # log-std of the OU process
    pm25_out_tau_h: float = 18.0         # correlation time [h]
    pm25_out_diurnal: float = 0.2        # relative amplitude of the traffic cycle
    pm25_out_peak_h: float = 8.0
    pm10_pm25_ratio: float = 1.7         # coarse/fine ratio of background aerosol
    tvoc_out: float = 30.0               # ug/m3
    # indoor aerosol / VOC
    filter_merv: int = 8
    penetration_pm25: float = 0.8
    penetration_pm10: float = 0.6
    deposition_pm25_h: float = 0.2       # 1/h
    deposition_pm10_h: float = 1.0       # coarse fraction
    sink_tvoc_h: float = 0.05
    pm25_per_person_mg_h: float = 0.1    # resuspension + personal cloud
    pm10_per_person_mg_h: float = 0.5    # coarse (2.5-10 um) resuspension
    tvoc_per_person_mg_h: float = 3.0    # human bio-effluents
    tvoc_area_mg_m2h: float = 0.1        # building materials and furnishing
    # light
    design_illuminance_lux: float = 500.0
    daylight_efficacy_lm_w: float = 105.0
    daylight_utilisation: float = 0.4
    # sound
    hvac_dba_design: float = 40.0        # diffuser/terminal noise at design flow (~NC-35)
    background_dba: float = 30.0
    speech_dba: float = 45.0             # space-averaged speech level at 1 talker per 100 m2
    talking_fraction: float = 0.15
    # occupant feedback
    vote_rate_h: float = 0.05            # votes per occupant per hour (feedback app)
    vote_individual_std: float = 1.0     # inter-individual spread of thermal sensation
    complaint_rate_h: float = 0.08       # complaints per dissatisfied occupant per hour
    # forecast
    fc_t_sigma0: float = 0.4
    fc_t_sigma_inf: float = 2.2
    fc_t_tau_h: float = 30.0
    fc_rh_sigma_inf: float = 10.0
    fc_ghi_rel0: float = 0.08
    fc_ghi_rel_inf: float = 0.35
    fc_ghi_tau_h: float = 12.0
    fc_issue_tau_h: float = 6.0          # correlation of errors between consecutive issues
    # grid
    tou: dict[str, Any] = field(default_factory=lambda: {
        "off_peak": 0.08, "mid_peak": 0.14, "on_peak": 0.24,
        "on_peak_hours": [12, 18], "mid_peak_hours": [[8, 12], [18, 21]], "weekend": "off_peak"})
    demand_charge_per_kw: float = 15.0
    gas_price_per_kwh: float = 0.035
    carbon_base: float = 0.40            # kgCO2/kWh, marginal grid intensity
    carbon_diurnal: float = 0.12
    carbon_solar_dip: float = 0.30
    carbon_sigma: float = 0.04
    gas_carbon: float = 0.181            # kgCO2/kWh (natural gas, combustion)

    @classmethod
    def from_dict(cls, d: dict[str, Any] | None) -> "EnvConfig":
        c = cls()
        for k, v in (d or {}).items():
            if hasattr(c, k):
                setattr(c, k, v)
        return c


# filter efficiencies (ASHRAE 52.2 composite efficiency for the PM2.5 / PM10 size ranges, typical values)
# (fine PM2.5, coarse PM2.5-10) removal efficiencies
FILTER_EFF = {6: (0.10, 0.50), 8: (0.25, 0.75), 10: (0.40, 0.85), 11: (0.50, 0.88), 13: (0.70, 0.92),
              14: (0.80, 0.96), 15: (0.85, 0.97), 16: (0.90, 0.98)}


def filter_efficiency(merv: int) -> tuple[float, float]:
    keys = sorted(FILTER_EFF)
    m = min(keys, key=lambda k: abs(k - int(merv)))
    return FILTER_EFF[m]


# ----------------------------------------------------------------------------- weather file / forecast
class WeatherFile:
    """Hourly EPW records used as the 'future' for weather forecasts."""

    COLS = {"tdb": 6, "tdp": 7, "rh": 8, "p": 9, "ghi": 13, "dni": 14, "dhi": 15, "wdir": 20, "wspd": 21, "sky": 22}

    def __init__(self, path: str | Path, year: int):
        self.year = year
        rows = []
        with open(path, encoding="latin-1") as f:
            for i, line in enumerate(f):
                if i < 8:
                    continue
                parts = line.strip().split(",")
                if len(parts) < 23:
                    continue
                rows.append([float(parts[c]) for c in self.COLS.values()])
        self.data = np.array(rows)            # row i = hour ending i+1 of the year
        self.n = len(self.data)
        self.idx = {k: j for j, k in enumerate(self.COLS)}

    def at(self, t: dt.datetime, key: str) -> float:
        h = (t - dt.datetime(self.year, 1, 1)).total_seconds() / 3600.0
        x = h - 1.0                           # value of row i belongs to hour i+1
        i0 = int(math.floor(x))
        f = x - i0
        j = self.idx[key]
        a = self.data[i0 % self.n, j]
        b = self.data[(i0 + 1) % self.n, j]
        return float(a + f * (b - a))


class WeatherForecast:
    """Hourly-issued 48 h forecast = weather file + lead-time dependent AR(1) errors (labelled)."""

    LEADS = np.arange(1, 49)

    def __init__(self, wf: WeatherFile, cfg: EnvConfig, rng: np.random.Generator):
        self.wf, self.cfg, self.rng = wf, cfg, rng
        n = len(self.LEADS)
        self.z = {k: rng.normal(size=n) for k in ("tdb", "rh", "ghi")}
        self.issued: dt.datetime | None = None
        self.values: dict[str, np.ndarray] = {}
        self.truth: dict[str, np.ndarray] = {}

    def _sigma(self, s0, sinf, tau):
        return s0 + sinf * (1.0 - np.exp(-self.LEADS / tau))

    def update(self, t: dt.datetime) -> None:
        issue = t.replace(minute=0, second=0, microsecond=0)
        if self.issued == issue:
            return
        steps = 1 if self.issued is None else max(1, int((issue - self.issued).total_seconds() // 3600))
        rho = math.exp(-steps / self.cfg.fc_issue_tau_h)
        for k in self.z:
            self.z[k] = rho * self.z[k] + math.sqrt(1 - rho * rho) * self.rng.normal(size=len(self.LEADS))
        self.issued = issue
        c = self.cfg
        times = [issue + dt.timedelta(hours=int(h)) for h in self.LEADS]
        tr = {k: np.array([self.wf.at(x, k) for x in times]) for k in ("tdb", "rh", "ghi", "wspd", "sky")}
        self.truth = tr
        s_t = self._sigma(c.fc_t_sigma0, c.fc_t_sigma_inf, c.fc_t_tau_h)
        s_rh = self._sigma(1.0, c.fc_rh_sigma_inf, c.fc_t_tau_h)
        s_g = self._sigma(c.fc_ghi_rel0, c.fc_ghi_rel_inf, c.fc_ghi_tau_h)
        self.values = {
            "tdb": tr["tdb"] + s_t * self.z["tdb"],
            "rh": np.clip(tr["rh"] + s_rh * self.z["rh"], 1.0, 100.0),
            "ghi": np.clip(tr["ghi"] * (1.0 + s_g * self.z["ghi"]), 0.0, 1300.0),
            "wspd": tr["wspd"], "sky": tr["sky"]}
        self.times = times

    def lead(self, key: str, h: int, truth: bool = False) -> float:
        arr = (self.truth if truth else self.values).get(key)
        if arr is None:
            return math.nan
        return float(arr[min(len(arr), max(1, h)) - 1])

    def table(self, hours: int = 48) -> list[dict[str, Any]]:
        n = min(hours, len(self.LEADS))
        return [{"time": self.times[i].isoformat(), "lead_h": int(self.LEADS[i]),
                 "oa_t": round(float(self.values["tdb"][i]), 2), "oa_rh": round(float(self.values["rh"][i]), 1),
                 "ghi": round(float(self.values["ghi"][i]), 1), "wind": round(float(self.values["wspd"][i]), 1),
                 "sky_cover": float(self.values["sky"][i])} for i in range(n)]


# ----------------------------------------------------------------------------- grid
def tou_price(cfg: EnvConfig, t: dt.datetime, dow: int, holiday: bool = False) -> tuple[float, int]:
    """Return (price $/kWh, period 0 off / 1 mid / 2 on-peak). ``dow``: 1 = Sunday ... 7 = Saturday."""
    tou = cfg.tou
    h = t.hour + t.minute / 60.0
    if dow in (1, 7) or holiday:
        per = {"off_peak": 0, "mid_peak": 1, "on_peak": 2}.get(tou.get("weekend", "off_peak"), 0)
    else:
        lo, hi = tou.get("on_peak_hours", [12, 18])
        if lo <= h < hi:
            per = 2
        elif any(a <= h < b for a, b in tou.get("mid_peak_hours", [])):
            per = 1
        else:
            per = 0
    return float(tou[["off_peak", "mid_peak", "on_peak"][per]]), per


# ----------------------------------------------------------------------------- zone state
@dataclass
class _Zone:
    zid: str
    name: str
    vav: str | None
    ahu: str | None
    mult: float
    vmax: float
    lights: list[str]
    pm25: float = 6.0
    pm10: float = 4.0            # coarse fraction PM2.5-10 (PM10 = pm25 + pm10)
    tvoc: float = 150.0
    votes: deque = field(default_factory=deque)
    hot_calls: int = 0
    cold_calls: int = 0


class OuterEnvironment:
    """Computes the truth of all environment points not modelled by EnergyPlus (see module doc)."""

    def __init__(self, bas, cfg: dict[str, Any] | None = None):
        self.bas = bas
        self.cat = bas.cat
        self.cfg = EnvConfig.from_dict(cfg)
        seed = bas.seed
        self.rng_out = np.random.default_rng([seed, 3, 1])
        self.rng_occ = np.random.default_rng([seed, 3, 2])
        self.rng_grid = np.random.default_rng([seed, 3, 3])
        self.eta25, self.eta10 = filter_efficiency(self.cfg.filter_merv)
        self.x_pm = 0.0
        self.x_ci = 0.0
        self.zones: dict[str, _Zone] = {}
        topo = bas.b.manifest.topo
        for zid, zname in self.cat.zone_of_equip.items():
            e = self.cat.equipment[zid]
            vav = e.parent if e.parent and e.parent in self.cat.equipment and self.cat.equipment[e.parent].type == "VAV" else None
            self.zones[zid] = _Zone(zid, zname, vav, e.meta.get("ahu"), float(e.meta.get("multiplier", 1) or 1),
                                    self.cat.equipment[vav].meta["vmax_m3s"] if vav else 0.0,
                                    list(topo.zones[zname].lights))
        try:
            self.wf = WeatherFile(bas.b.weather_path, bas.b.year)
            self.forecast = WeatherForecast(self.wf, self.cfg, np.random.default_rng([seed, 3, 4]))
        except Exception:  # noqa: BLE001 - forecasts are optional
            self.wf = None
            self.forecast = None
        self.tot = {"elec_kwh": 0.0, "gas_kwh": 0.0, "water_m3": 0.0}
        self.day = None
        self.day_acc = {"cost": 0.0, "co2": 0.0, "hdd": 0.0, "cdd": 0.0}

    # -------------------------------------------------------------- helpers
    def _iv(self, key: str, default: float = 0.0) -> float:
        return float(self.bas.engine.internal_values.get(key.upper(), default) or default)

    @staticmethod
    def _f(v, default=0.0) -> float:
        return float(v) if v is not None and isinstance(v, (int, float)) and math.isfinite(v) else default

    def zone_area(self, zname: str) -> float:
        return max(1.0, self._iv(f"ZAREA|{zname}", 100.0))

    def zone_volume(self, zname: str) -> float:
        return max(1.0, self._iv(f"ZVOL|{zname}", 300.0))

    # -------------------------------------------------------------- step
    def step(self, t: dt.datetime, dts: float, raw: dict[str, float], truth: dict[str, float], ov, warm: bool,
             dow: int = 2) -> None:
        c = self.cfg
        f = self._f
        hrs = dts / 3600.0
        # ---------------- outdoor air quality
        phi = math.exp(-hrs / c.pm25_out_tau_h)
        self.x_pm = phi * self.x_pm + c.pm25_out_sigma * math.sqrt(1 - phi * phi) * self.rng_out.normal()
        hod = t.hour + t.minute / 60.0
        diurnal = 1.0 + c.pm25_out_diurnal * math.cos(2 * math.pi * (hod - c.pm25_out_peak_h) / 24.0)
        bg = c.pm25_out_mean * math.exp(self.x_pm - 0.5 * c.pm25_out_sigma ** 2) * diurnal
        smoke = getattr(ov, "outdoor_pm_add", 0.0)
        pm25_o = bg + smoke
        pm10_o = bg * (c.pm10_pm25_ratio - 1.0) + 0.1 * smoke     # coarse fraction PM2.5-10
        tvoc_o = c.tvoc_out + 0.2 * smoke
        truth["WX/OA-PM25"], truth["WX/OA-PM10"] = pm25_o, pm25_o + pm10_o

        # ---------------- AHU supply concentrations (return = flow-weighted zone mean of last step)
        sup: dict[str | None, tuple[float, float, float]] = {}
        for a in self.cat.equipment_of_type("AHU"):
            aid = a.id
            sa = f(truth.get(f"{aid}/SA-F"))
            oa = f(truth.get(f"{aid}/OA-F"))
            x = min(1.0, max(0.0, oa / sa)) if sa > 1e-4 else 0.0
            w = [(z, z.mult * f(truth.get(f"{z.vav}/DA-F"))) for z in self.zones.values() if z.ahu == aid and z.vav]
            wsum = sum(q for _, q in w)
            if wsum > 1e-6:
                ret = [sum(getattr(z, s) * q for z, q in w) / wsum for s in ("pm25", "pm10", "tvoc")]
            else:
                ret = [pm25_o, pm10_o, tvoc_o]
            byp = getattr(ov, "filter_bypass", {}).get(aid, 0.0)
            e25, e10 = self.eta25 * (1 - byp), self.eta10 * (1 - byp)
            mix = [x * o + (1 - x) * r for o, r in zip((pm25_o, pm10_o, tvoc_o), ret)]
            sup[aid] = ((1 - e25) * mix[0], (1 - e10) * mix[1], mix[2])
            truth[f"{aid}/SA-PM25"] = sup[aid][0]
            truth[f"{aid}/OA-FRAC"] = 100.0 * x

        # ---------------- zones
        src = getattr(ov, "indoor_src", {})
        for zid, z in self.zones.items():
            zn = z.name
            V, A = self.zone_volume(zn), self.zone_area(zn)
            qs = f(truth.get(f"{z.vav}/DA-F")) if z.vav else 0.0
            qi = f(raw.get(f"INFIL|{zn}".upper()))
            npl = f(truth.get(f"{zid}/OCCUPANTS"))
            cs = sup.get(z.ahu, (pm25_o, pm10_o, tvoc_o)) if qs > 0 else (0.0, 0.0, 0.0)
            ex = src.get(zn, {})
            S = (npl * c.pm25_per_person_mg_h + ex.get("pm25", 0.0),
                 npl * c.pm10_per_person_mg_h + max(0.0, ex.get("pm10", 0.0) - ex.get("pm25", 0.0)),
                 npl * c.tvoc_per_person_mg_h + A * c.tvoc_area_mg_m2h + ex.get("tvoc", 0.0))
            k = (c.deposition_pm25_h / 3600.0, c.deposition_pm10_h / 3600.0, c.sink_tvoc_h / 3600.0)
            P = (c.penetration_pm25, c.penetration_pm10, 1.0)
            Co = (pm25_o, pm10_o, tvoc_o)
            new = []
            for C, Csup, s, kk, pp, co in zip((z.pm25, z.pm10, z.tvoc), cs, S, k, P, Co):
                b = (qs + qi) / V + kk
                cstar = (qs * Csup + pp * qi * co + s * MG_H_TO_UG_S) / (b * V)
                new.append(cstar + (C - cstar) * math.exp(-b * dts))
            z.pm25, z.pm10, z.tvoc = new
            truth[f"{zid}/ZN-PM25"], truth[f"{zid}/ZN-PM10"], truth[f"{zid}/ZN-TVOC"] = new[0], new[0] + new[1], new[2]
            # ---- illuminance
            pl = f(truth.get(f"{zid}/LIGHT-KW")) * 1000.0
            pdes = sum(self._iv(f"LIGHTDES|{li}") for li in z.lights)
            e_el = c.design_illuminance_lux * pl / pdes if pdes > 0 else 0.0
            qwin = f(raw.get(f"ZWINSOL|{zn}".upper()))
            e_dl = c.daylight_efficacy_lm_w * c.daylight_utilisation * qwin / A
            truth[f"{zid}/ZN-LUX"] = e_el + e_dl
            truth[f"{zid}/DAYLIGHT-LUX"] = e_dl
            truth[f"{zid}/LIGHT-LVL"] = 100.0 * pl / pdes if pdes > 0 else 0.0
            # ---- sound
            terms = [c.background_dba]
            if z.vav and qs > 1e-4 and z.vmax > 0:
                terms.append(c.hvac_dba_design + 50.0 * math.log10(max(0.05, qs / z.vmax)))
            talkers = c.talking_fraction * npl * 100.0 / A        # talkers per 100 m2
            if talkers > 0:
                terms.append(c.speech_dba + 10.0 * math.log10(talkers))
            truth[f"{zid}/ZN-DBA"] = 10.0 * math.log10(sum(10 ** (x / 10.0) for x in terms))
            # ---- window / door contact (window_open events)
            truth[f"{zid}/WIN-STS"] = 1.0 if getattr(ov, "infil_add_ach", {}).get(zn, 0.0) > 0 else 0.0
            truth[f"{zid}/OCC-COUNT"] = npl
            # ---- occupant feedback
            pmv = truth.get(f"{zid}/PMV")
            ppd = truth.get(f"{zid}/PPD")
            if self.day is not None and t.date() != self.day:
                z.hot_calls = z.cold_calls = 0
            if not warm and npl > 0 and pmv is not None and math.isfinite(pmv):
                nv = self.rng_occ.poisson(npl * c.vote_rate_h * hrs)
                for _ in range(int(nv)):
                    v = float(np.clip(round(pmv + c.vote_individual_std * self.rng_occ.normal()), -3, 3))
                    z.votes.append((t, v))
                ppd_v = ppd if ppd is not None and math.isfinite(ppd) else 5.0
                lam = npl * c.complaint_rate_h * hrs * ppd_v / 100.0
                w_hot = 1.0 / (1.0 + math.exp(-3.0 * pmv))
                z.hot_calls += int(self.rng_occ.poisson(lam * w_hot))
                z.cold_calls += int(self.rng_occ.poisson(lam * (1 - w_hot)))
            while z.votes and (t - z.votes[0][0]).total_seconds() > 3600.0:
                z.votes.popleft()
            truth[f"{zid}/TS-VOTE"] = (sum(v for _, v in z.votes) / len(z.votes)) if z.votes else math.nan
            truth[f"{zid}/HOT-CALLS"] = float(z.hot_calls)
            truth[f"{zid}/COLD-CALLS"] = float(z.cold_calls)

        # ---------------- weather forecast
        if self.forecast is not None:
            self.forecast.update(t)
            for h in (1, 6, 24):
                truth[f"WX/OA-T-FC{h}H"] = self.forecast.lead("tdb", h)
                truth[f"WX/GHI-FC{h}H"] = self.forecast.lead("ghi", h)

        # ---------------- grid signals
        price, period = tou_price(c, t, dow, getattr(ov, "holiday", False))
        price *= getattr(ov, "price_mult", 1.0)
        phi = math.exp(-hrs / 3.0)
        self.x_ci = phi * self.x_ci + c.carbon_sigma * math.sqrt(1 - phi * phi) * self.rng_grid.normal()
        ghi = f(truth.get("WX/GHI-TRUE", truth.get("WX/SOLAR")))
        ci = c.carbon_base * (1.0 + c.carbon_diurnal * math.cos(2 * math.pi * (hod - 19.0) / 24.0)
                              - c.carbon_solar_dip * min(1.0, ghi / 1000.0)) + self.x_ci + getattr(ov, "grid_ci_add", 0.0)
        ci = max(0.02, ci)
        dr = getattr(ov, "dr_shed_kw", None)
        truth["GRID/PRICE"], truth["GRID/TOU-PERIOD"], truth["GRID/CO2-INT"] = price, float(period), ci
        truth["GRID/DR-EVENT"] = 1.0 if dr is not None else 0.0
        truth["GRID/DR-SHED-KW"] = float(dr or 0.0)

        # ---------------- totalisers, cost and carbon (utility meters)
        if not warm:
            ekw = max(0.0, f(truth.get("MTR/BLDG-ELEC-KW")))
            gkw = max(0.0, f(truth.get("MTR/BLDG-GAS-KW")))
            self.tot["elec_kwh"] += ekw * hrs
            self.tot["gas_kwh"] += gkw * hrs
            self.tot["water_m3"] += max(0.0, f(truth.get("MTR/WATER-F"))) * dts / 1000.0
            if self.day is None or t.date() != self.day:
                self.day_acc = {"cost": 0.0, "co2": 0.0, "hdd": 0.0, "cdd": 0.0}
            self.day_acc["cost"] += ekw * hrs * price + gkw * hrs * c.gas_price_per_kwh
            self.day_acc["co2"] += ekw * hrs * ci + gkw * hrs * c.gas_carbon
        truth["MTR/BLDG-ELEC-KWH"] = self.tot["elec_kwh"]
        truth["MTR/BLDG-GAS-KWH"] = self.tot["gas_kwh"]
        truth["MTR/WATER-M3"] = self.tot["water_m3"]
        truth["GRID/COST-TODAY"] = self.day_acc["cost"]
        truth["GRID/CO2-TODAY"] = self.day_acc["co2"]
        self.day = t.date()

    # -------------------------------------------------------------- API helpers
    def forecast_table(self, hours: int = 48) -> list[dict[str, Any]]:
        if self.forecast is None or self.forecast.issued is None:
            return []
        return self.forecast.table(hours)
