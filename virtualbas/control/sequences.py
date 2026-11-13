"""BAS control sequences (the *controller* of the outer space).

All controllers act exclusively on **observed** values (BAS present values, possibly wrong,
stale or missing) - never on the EnergyPlus truth. Two profiles are provided:

``baseline``
    Reproduces the native EnergyPlus controls of the source model (fixed SAT, CHWST and HWST
    set points, economizer with differential dry-bulb high limit, night cycle). Used for
    verification against a native EnergyPlus run.
``g36``
    Advanced sequences inspired by ASHRAE Guideline 36: trim-and-respond resets of supply air
    temperature, duct static pressure and chilled-water temperature, outdoor-air reset of
    hot-water temperature and a condenser-water approach set point.
``geb``
    Grid-interactive efficient building: the ``baseline`` sequences plus (i) pre-cooling of the
    zones before the on-peak tariff window and a set-point relaxation during it, (ii) battery
    dispatch from the TOU / demand-response signals through the EnergyPlus storage actuators
    (hold in the hours before on-peak while storing the PV surplus, optional off-peak grid
    charging, native load following down to a reserve otherwise, load following during DR events) and (iii) load shedding on a
    ``demand_response`` event (zone set-point relaxation, optional disabling of listed units).
"""
from __future__ import annotations

import datetime as dt
import math
from dataclasses import dataclass, field
from typing import Any

from .pid import PI, TrimRespond


@dataclass
class ControlConfig:
    profile: str = "baseline"
    schedule_source: str = "native"      # native: schedules/set points read from the source model | config
    # schedule (hours)
    weekday_start: float = 6.0
    weekday_end: float = 22.0
    saturday_start: float = 6.0
    saturday_end: float = 18.0
    sunday_occupied: bool = False
    min_oa_delay_h: float = 1.0          # minimum OA starts 1 h after fan start (source model)
    # zone set points
    htg_occ: float = 21.0
    clg_occ: float = 24.0
    htg_unocc: float = 15.6
    clg_unocc: float = 26.7
    night_cycle_tol: float = 1.0
    night_cycle_min_run_s: float = 1800.0
    # VAV loops
    vav_kp: float = 0.15       # 15 %/K - tuned for 5-min sampling (no limit cycles with ideal sensors)
    vav_ti: float = 1200.0
    heat_dual_max: bool = False
    heat_max_frac: float = 0.5
    # AHU
    sat_fixed: float = 12.8
    sat_min: float = 12.8
    sat_max: float = 18.3
    sat_oat_lo: float = 15.6
    sat_oat_hi: float = 21.1
    fan_heat_k: float = 0.8
    sat_setback_heating: float = 30.0
    econ_high_limit: float = 28.0
    econ_kp: float = 0.01
    econ_ti: float = 1800.0
    econ_mat_margin: float = 0.0
    dsp_design: float = 375.0
    dsp_min: float = 125.0
    dsp_max: float = 375.0
    # plant
    chwst: float = 6.7
    chwst_max: float = 10.0
    hwst: float = 82.2
    hwst_min: float = 65.0
    hw_oat_lo: float = -6.7
    hw_oat_hi: float = 15.6
    cw_offset: float = 0.0
    cw_min: float = 5.0
    cw_max: float = 80.0
    cw_approach_g36: float = 3.9
    # grid-interactive (profile "geb")
    geb_precool_k: float = 1.5           # cooling set point lowered by this before the on-peak window
    geb_precool_h: float = 2.0           # pre-cooling duration before on-peak start [h]
    geb_precool_min_oat: float = 22.0    # pre-cool only if the observed / forecast outdoor temperature exceeds this
    geb_onpeak_offset_k: float = 1.0     # cooling set point raised (heating lowered) during on-peak
    geb_dr_offset_k: float = 2.0         # additional relaxation during a demand-response event
    geb_dr_disable: str = ""             # comma separated zone-equipment ids switched off during DR (e.g. "HP-ZONE1")
    ess_reserve: float = 0.3             # battery backup reserve (fraction); never dispatched below
    ess_offpeak_hold: bool = True        # no discharge in the hours before on-peak (PV surplus is still stored)
    ess_hold_h: float = 6.0              # length of that hold window before the on-peak start [h]
    ess_grid_charge: bool = False        # charge from the grid off-peak up to ess_target_soc
    ess_target_soc: float = 0.95

    @staticmethod
    def from_dict(d: dict[str, Any] | None) -> "ControlConfig":
        c = ControlConfig()
        for k, v in (d or {}).items():
            if hasattr(c, k):
                cur = getattr(c, k)
                setattr(c, k, bool(v) if isinstance(cur, bool) else (str(v) if isinstance(cur, str) else type(cur)(v)))
        return c


def _ok(x: float | None) -> bool:
    return x is not None and math.isfinite(x)


# ----------------------------------------------------------------------------- scheduler
def occupied(cfg: ControlConfig, t: dt.datetime, dow: int, holiday: bool = False) -> bool:
    """EnergyPlus day of week convention: 1 = Sunday ... 7 = Saturday."""
    if holiday:
        return False
    h = t.hour + t.minute / 60.0
    if dow == 1:
        return cfg.sunday_occupied and cfg.weekday_start <= h < cfg.weekday_end
    if dow == 7:
        return cfg.saturday_start <= h < cfg.saturday_end
    return cfg.weekday_start <= h < cfg.weekday_end


# ----------------------------------------------------------------------------- VAV
@dataclass
class VAVController:
    vav_id: str
    zone_id: str
    vmax: float
    vmin_frac: float
    cfg: ControlConfig
    clg: PI = field(init=False)
    htg: PI = field(init=False)
    out: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        self.clg = PI(self.cfg.vav_kp, self.cfg.vav_ti, direct=True)
        self.htg = PI(self.cfg.vav_kp, self.cfg.vav_ti, direct=False)

    def step(self, t_zone: float, htg_sp: float, clg_sp: float, fan_on: bool, dt_s: float,
             gain_mult: float = 1.0, frozen: bool = False) -> dict[str, float]:
        if frozen and self.out:
            return self.out
        self.clg.gain_mult = self.htg.gain_mult = gain_mult
        if not fan_on:
            self.clg.reset(0.0)
            self.htg.reset(0.0)
        c = self.clg.step(clg_sp, t_zone, dt_s)
        h = self.htg.step(htg_sp, t_zone, dt_s)
        vmin = self.vmin_frac * self.vmax
        if c > 0 and c >= h:
            flow = vmin + c * (self.vmax - vmin)
        elif self.cfg.heat_dual_max and h > 0.5:
            flow = vmin + (h - 0.5) / 0.5 * max(0.0, self.cfg.heat_max_frac * self.vmax - vmin)
        else:
            flow = vmin
        self.out = {"CLG-LOOP": 100 * c, "HTG-LOOP": 100 * h, "DA-F-SP": flow,
                    "DMPR-CMD": 100.0 * flow / self.vmax if self.vmax > 0 else 0.0}
        return self.out


# ----------------------------------------------------------------------------- AHU
@dataclass
class AHUController:
    ahu_id: str
    design_flow: float
    min_oa: float
    cfg: ControlConfig
    out: dict[str, float] = field(default_factory=dict)
    run_timer: float = 0.0
    on_time: float = 0.0
    mode: int = 0
    heating_demand: bool = False

    def __post_init__(self):
        c = self.cfg
        self.econ = PI(c.econ_kp, c.econ_ti, lo=0.0, hi=1.0, direct=True, positional=True)
        self.sat_tr = TrimRespond(sp=c.sat_min, sp_min=c.sat_min, sp_max=c.sat_max, trim=0.1, respond=-0.2,
                                  max_change=0.6, ignores=2, period_s=300)
        self.dsp_tr = TrimRespond(sp=c.dsp_max, sp_min=c.dsp_min, sp_max=c.dsp_max, trim=-12.0, respond=15.0,
                                  max_change=32.0, ignores=2, period_s=300)

    def step(self, t: dt.datetime, dow: int, pv: dict[str, float], zone_temps: list[float], vav_out: list[dict[str, float]],
             dt_s: float, *, holiday=False, force_occ=False, force_unocc=False, econ_mode: str | None = None,
             sat_fixed: float | None = None, gain_mult: float = 1.0, frozen: bool = False,
             occ_native: bool | None = None, min_oa_on: bool | None = None) -> dict[str, float]:
        """zone_temps: list of (T, heating set point, cooling set point) of the served zones."""
        c = self.cfg
        if frozen and self.out:
            return self.out
        sched_occ = occupied(c, t, dow, holiday) if occ_native is None else (occ_native and not holiday)
        occ = (sched_occ or force_occ) and not force_unocc
        # ---- operating mode & night cycle (CycleOnAny)
        if occ:
            self.mode = 2
            self.run_timer = 0.0
        else:
            zt3 = [z if isinstance(z, tuple) else (z, c.htg_unocc, c.clg_unocc) for z in zone_temps]
            cold = any(_ok(T) and T < h - c.night_cycle_tol / 2 for T, h, _ in zt3)
            hot = any(_ok(T) and T > k + c.night_cycle_tol / 2 for T, _, k in zt3)
            need = cold or hot
            if self.mode != 1 and need:
                self.heating_demand = cold and not hot
            if self.mode == 1:
                self.run_timer += dt_s
                if self.run_timer >= c.night_cycle_min_run_s and not need:
                    self.mode = 0
            elif need and not force_unocc:
                self.mode = 1
                self.run_timer = 0.0
            else:
                self.mode = 0
        fan_on = self.mode > 0
        if fan_on:
            self.on_time += dt_s
        else:
            self.on_time = 0.0
        # ---- supply air temperature set point
        oat = pv.get("OA-T", math.nan)
        if c.profile == "g36":
            req = sum(1 for v in vav_out if v.get("CLG-LOOP", 0) > 95)
            tmax = self.sat_tr.step(req, dt_s) if fan_on else self.sat_tr.sp
            if _ok(oat):
                x = min(1.0, max(0.0, (oat - c.sat_oat_lo) / (c.sat_oat_hi - c.sat_oat_lo)))
                sat = tmax - x * (tmax - c.sat_min)
            else:
                sat = c.sat_min
        else:
            sat = c.sat_fixed
        if c.profile == "g36" and self.mode == 1 and self.heating_demand:
            sat = c.sat_setback_heating
        if sat_fixed is not None:
            sat = sat_fixed
        # ---- duct static pressure set point
        if c.profile == "g36":
            req = sum(1 for v in vav_out if v.get("DMPR-CMD", 0) > 95)
            dsp = self.dsp_tr.step(req, dt_s) if fan_on else self.dsp_tr.sp
        else:
            dsp = c.dsp_design
        # ---- economizer / minimum outdoor air
        # fan heat estimated from observed fan power and air flow: dT = P / (rho V cp)
        sa_flow = pv.get("SA-F", math.nan)
        fan_kw = pv.get("SF-KW", math.nan)
        if _ok(sa_flow) and _ok(fan_kw) and sa_flow > 0.05 * self.design_flow:
            dtf = min(3.0, max(0.0, fan_kw / (1.204 * sa_flow * 1.006)))
            self._fan_dt = 0.7 * getattr(self, "_fan_dt", dtf) + 0.3 * dtf
        mat_sp = sat - getattr(self, "_fan_dt", c.fan_heat_k) - c.econ_mat_margin
        rat = pv.get("RA-T", math.nan)
        if self.on_time <= dt_s + 1e-6:
            # first step after start: the return-air sensor still reads stagnant duct air
            zt = [(z[0] if isinstance(z, tuple) else z) for z in zone_temps]
            zt = [T for T in zt if _ok(T)]
            if zt:
                rat = sum(zt) / len(zt)
        # baseline: economizer active whenever the fan runs (EnergyPlus native behaviour, incl. night cycle)
        # g36: economizer only in occupied mode
        econ_mode_ok = (self.mode == 2) if c.profile == "g36" else fan_on
        econ_en = fan_on and econ_mode_ok and _ok(oat) and _ok(rat) and oat < rat and oat < c.econ_high_limit
        if econ_mode == "off":
            econ_en = False
        elif econ_mode == "on":
            econ_en = fan_on
        if min_oa_on is None:
            min_oa_active = self.mode == 2 and self.on_time >= c.min_oa_delay_h * 3600.0 - 1e-6
        else:
            min_oa_active = self.mode == 2 and min_oa_on
        min_frac = 0.0
        if min_oa_active:
            # supply flow = sum of the terminal air-flow set points (known to the BAS, cf. ASHRAE G36)
            vsum = sum(v.get("DA-F-SP", 0.0) for v in vav_out)
            denom = vsum if vsum > 0.05 * self.design_flow else (
                sa_flow if _ok(sa_flow) and sa_flow > 0.05 * self.design_flow else self.design_flow)
            min_frac = min(1.0, self.min_oa / denom)
        self.econ.gain_mult = gain_mult
        if econ_en:
            # mixing-equation feed-forward on observed RAT/OAT + PI trim on observed MAT
            ff = 1.0 if abs(rat - oat) < 0.2 else min(1.0, max(0.0, (rat - mat_sp) / (rat - oat)))
            self.econ.lo, self.econ.hi = -0.3, 0.3
            trim = self.econ.step(mat_sp, pv.get("MA-T", math.nan), dt_s)
            u = min(1.0, max(0.0, ff + trim))
            if min_frac > u:
                # anti-windup tracking: the minimum-OA selector is active
                self.econ.integ = min(self.econ.hi, max(self.econ.lo, min_frac - ff))
        else:
            self.econ.reset(0.0)
            u = 0.0
        oa_frac = max(min_frac, u) if fan_on else 0.0
        self.out = {"SF-CMD": 1.0 if fan_on else 0.0, "OCC-MODE": float(self.mode), "SA-T-SP": sat, "DSP-SP": dsp,
                    "MA-T-SP": mat_sp, "OAD-CMD": 100.0 * oa_frac, "ECON-EN": 1.0 if econ_en else 0.0}
        return self.out


# ----------------------------------------------------------------------------- plant
@dataclass
class PlantController:
    cfg: ControlConfig
    out: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        c = self.cfg
        self.chw_tr = TrimRespond(sp=c.chwst, sp_min=c.chwst, sp_max=c.chwst_max, trim=0.1, respond=-0.2,
                                  max_change=0.6, ignores=1, period_s=600)

    def step(self, pv: dict[str, float], ccv_positions: list[float], dt_s: float) -> dict[str, float]:
        c = self.cfg
        oat = pv.get("WX/OA-T", math.nan)
        wb = pv.get("WX/OA-WB", math.nan)
        if c.profile == "g36":
            req = sum(1 for v in ccv_positions if _ok(v) and v > 95)
            chw = self.chw_tr.step(req, dt_s)
            if _ok(oat):
                x = min(1.0, max(0.0, (oat - c.hw_oat_lo) / (c.hw_oat_hi - c.hw_oat_lo)))
                hw = c.hwst - x * (c.hwst - c.hwst_min)
            else:
                hw = c.hwst
            cw = min(29.4, max(18.3, wb + c.cw_approach_g36)) if _ok(wb) else 29.4
        else:
            chw, hw = c.chwst, c.hwst
            cw = min(c.cw_max, max(c.cw_min, wb + c.cw_offset)) if _ok(wb) else self.out.get("CW-ST-SP", 25.0)
        self.out = {"CHW-ST-SP": chw, "HW-ST-SP": hw, "CW-ST-SP": cw}
        return self.out


# ----------------------------------------------------------------------------- grid-interactive building
def onpeak_window(tou: dict[str, Any], t: dt.datetime, dow: int, holiday: bool = False) -> tuple[float, float] | None:
    """(start, end) hour of today's on-peak window, or None (weekend / holiday tariff). ``dow``: 1 = Sunday."""
    if dow in (1, 7) or holiday:
        return None
    lo, hi = tou.get("on_peak_hours", [12, 18])
    return float(lo), float(hi)


def geb_zone_offsets(cfg: ControlConfig, t: dt.datetime, dow: int, tou: dict[str, Any], oat: float, dr: bool,
                     holiday: bool = False) -> tuple[float, float, str]:
    """Heating / cooling set-point offsets [K] of the GEB profile and the active strategy label."""
    dh = dc = 0.0
    mode = ""
    win = onpeak_window(tou, t, dow, holiday)
    h = t.hour + t.minute / 60.0
    if win is not None:
        lo, hi = win
        warm = _ok(oat) and oat >= cfg.geb_precool_min_oat
        if lo - cfg.geb_precool_h <= h < lo and warm:
            dc -= cfg.geb_precool_k
            mode = "precool"
        elif lo <= h < hi:
            dc += cfg.geb_onpeak_offset_k
            dh -= cfg.geb_onpeak_offset_k
            mode = "onpeak"
    if dr:
        dc += cfg.geb_dr_offset_k
        dh -= cfg.geb_dr_offset_k
        mode = "dr"
    return dh, dc, mode


def geb_battery(cfg: ControlConfig, period: float, soc: float, reserve: float, dr: bool, need_kw: float,
                surplus_kw: float, before_onpeak: bool, max_charge_kw: float, max_discharge_kw: float) -> tuple[float, float]:
    """Battery commands (charge kW, discharge kW); NaN = leave EnergyPlus' native storage scheme in charge.

    ``period``: tariff period (0 off, 1 mid, 2 on-peak); ``soc``: *observed* state of charge; ``need_kw``: observed
    site demand the battery could cover (grid import + present discharge); ``surplus_kw``: observed PV surplus that
    could be stored (grid export + present charge - grid import). EnergyPlus zeroes the native charge as soon as one
    storage actuator is set, so a held battery is charged explicitly from the surplus (self-consumption).
    """
    nan = float("nan")
    above = _ok(soc) and soc > reserve
    store = min(max_charge_kw, max(0.0, surplus_kw)) if _ok(surplus_kw) else 0.0
    if dr:
        dis = min(max_discharge_kw, max(0.0, need_kw)) if above and _ok(need_kw) else 0.0
        return (0.0 if dis > 0 else store), dis
    if _ok(period) and period >= 1.5:          # on-peak: native load following, protect the reserve
        return (nan, nan) if above else (store, 0.0)
    if before_onpeak and cfg.ess_offpeak_hold:  # TOU arbitrage: keep the energy for the on-peak window
        if cfg.ess_grid_charge and _ok(period) and period < 0.5 and _ok(soc) and soc < cfg.ess_target_soc:
            return max_charge_kw, 0.0
        return store, 0.0
    return (nan, nan) if above else (store, 0.0)
