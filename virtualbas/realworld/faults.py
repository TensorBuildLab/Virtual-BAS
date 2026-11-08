r"""Fault and event library of the outer (real-world) space.

Every abnormal or random condition is an :class:`Injection` of a registered :class:`InjectionType`.
An injection has a target, a start time :math:`t_0`, an optional end time :math:`t_1` and a
*severity profile* :math:`s(t) \in [0,1]`:

.. math::

    s(t) = \begin{cases}
        0 & t < t_0 \text{ or } t \ge t_1 \\
        1 & \text{step} \\
        \min\big(1, (t-t_0)/T_r\big) & \text{ramp (incipient fault)} \\
        \mathbb{1}\big[((t-t_0) \bmod P) < D\,P\big] & \text{intermittent}
    \end{cases}

Each type maps the severity to a modification of one model parameter :math:`\theta`,
:math:`\theta(t) = \theta_0 + s(t)\,\Delta\theta`, applied to one of five layers:

* ``sensor``    - the measurement equation (bias, drift, gain, noise, stuck, missing, spikes)
* ``actuator``  - the command-to-action map (stuck damper/valve, failed fan)
* ``equipment`` - the physics inside EnergyPlus (fouling, degradation, trips)
* ``control``   - the BAS software (schedules, set points, tuning, logic)
* ``network``   - data transport (communication loss, historian outage)

and events (non-fault real-world randomness) modify occupancy, weather, internal gains,
infiltration, and outdoor CO2. All injections are logged as ground-truth labels.
"""
from __future__ import annotations

import datetime as dt
import itertools
import math
from dataclasses import asdict, dataclass, field
from typing import Any, Callable

from .sensors import FaultOverlay

_ids = itertools.count(1)


# ----------------------------------------------------------------------------- overlays
@dataclass
class Overlays:
    """Aggregated effect of all active injections at one time step."""
    sensor: dict[str, FaultOverlay] = field(default_factory=dict)
    damper_stuck: dict[str, float] = field(default_factory=dict)        # VAV id -> fraction
    oa_damper_stuck: dict[str, float] = field(default_factory=dict)     # AHU id -> fraction
    reheat_closed: set[str] = field(default_factory=set)                # VAV ids
    reheat_open: set[str] = field(default_factory=set)
    coil_closed: set[str] = field(default_factory=set)                  # "AHU-1:CC" / "AHU-1:HC"
    fan_failed: set[str] = field(default_factory=set)                   # AHU ids
    trips: set[str] = field(default_factory=set)                        # CH/BLR/CT/pump equip ids
    fouling: dict[str, float] = field(default_factory=dict)             # equip id -> capacity/UA ratio
    filter_dp_add: dict[str, float] = field(default_factory=dict)       # AHU -> Pa
    fan_eff_mult: dict[str, float] = field(default_factory=dict)        # AHU -> multiplier
    force_occupied: set[str] = field(default_factory=set)               # AHU ids (schedule fault)
    force_unoccupied: set[str] = field(default_factory=set)
    setpoint_offset: dict[str, float] = field(default_factory=dict)     # zone equip id -> K (both sp)
    gain_mult: dict[str, float] = field(default_factory=dict)           # controller id -> multiplier
    economizer: dict[str, str] = field(default_factory=dict)            # AHU -> "off" | "on"
    sat_fixed: dict[str, float] = field(default_factory=dict)           # AHU -> fixed SAT sp
    frozen: set[str] = field(default_factory=set)                       # controller outputs frozen
    comm_loss: set[str] = field(default_factory=set)                    # equipment ids
    historian_outage: bool = False
    occ_mult: dict[str, float] = field(default_factory=dict)            # zone name or "*" -> multiplier
    occ_add: dict[str, float] = field(default_factory=dict)             # zone name -> people
    plug_mult: dict[str, float] = field(default_factory=dict)
    light_mult: dict[str, float] = field(default_factory=dict)
    infil_add_ach: dict[str, float] = field(default_factory=dict)
    weather_add: dict[str, float] = field(default_factory=dict)         # tdb, rh
    weather_mult: dict[str, float] = field(default_factory=dict)        # solar
    outdoor_co2: float | None = None
    holiday: bool = False

    def sensor_overlay(self, pid: str) -> FaultOverlay:
        if pid not in self.sensor:
            self.sensor[pid] = FaultOverlay()
        return self.sensor[pid]


# ----------------------------------------------------------------------------- types
@dataclass
class Param:
    default: Any
    unit: str = ""
    description: str = ""
    minimum: float | None = None
    maximum: float | None = None


@dataclass
class InjectionType:
    name: str
    category: str          # fault | event
    layer: str             # sensor | actuator | equipment | control | network | occupancy | weather | gains
    target: str            # point:sensor | equip:<Type> | zone | building
    description: str
    equation: str
    params: dict[str, Param]
    apply: Callable[["Injection", float, Overlays, Any], None]

    def schema(self) -> dict[str, Any]:
        return {"name": self.name, "category": self.category, "layer": self.layer, "target": self.target,
                "description": self.description, "equation": self.equation,
                "params": {k: asdict(v) for k, v in self.params.items()}}


REGISTRY: dict[str, InjectionType] = {}


def register(name, category, layer, target, description, equation, params=None):
    def deco(fn):
        REGISTRY[name] = InjectionType(name, category, layer, target, description, equation, params or {}, fn)
        return fn
    return deco


# ----------------------------------------------------------------------------- injection
@dataclass
class Injection:
    type: str
    target: str
    start: dt.datetime
    end: dt.datetime | None = None
    profile: str = "step"          # step | ramp | intermittent
    ramp_s: float = 3600.0
    period_s: float = 3600.0
    duty: float = 0.5
    params: dict[str, Any] = field(default_factory=dict)
    source: str = "human"          # human | ai | scenario | random
    note: str = ""
    id: str = ""
    created: str = ""
    cleared: bool = False

    def __post_init__(self):
        if not self.id:
            self.id = f"inj-{next(_ids):04d}"
        t = REGISTRY.get(self.type)
        if t is None:
            raise ValueError(f"Unknown injection type '{self.type}'. Available: {sorted(REGISTRY)}")
        merged = {k: p.default for k, p in t.params.items()}
        merged.update(self.params or {})
        self.params = merged

    @property
    def kind(self) -> InjectionType:
        return REGISTRY[self.type]

    def severity(self, t: dt.datetime) -> float:
        if self.cleared or t < self.start or (self.end is not None and t >= self.end):
            return 0.0
        el = (t - self.start).total_seconds()
        if self.profile == "ramp":
            return min(1.0, el / max(self.ramp_s, 1.0))
        if self.profile == "intermittent":
            return 1.0 if (el % max(self.period_s, 1.0)) < self.duty * self.period_s else 0.0
        return 1.0

    def p(self, key: str) -> Any:
        return self.params.get(key)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["start"] = self.start.isoformat()
        d["end"] = self.end.isoformat() if self.end else None
        d["category"] = self.kind.category
        d["layer"] = self.kind.layer
        return d


# ============================================================================= SENSOR faults
@register("sensor_bias", "fault", "sensor", "point:sensor",
          "Constant calibration offset (e.g. mis-calibrated thermistor).",
          r"y_k = y_k^{0} + s(t)\,b", {"bias": Param(1.5, "point unit", "offset b")})
def _sensor_bias(inj, s, ov, ctx):
    ov.sensor_overlay(inj.target).bias += s * float(inj.p("bias"))


@register("sensor_drift", "fault", "sensor", "point:sensor",
          "Linear drift accumulating from the onset time, saturating at a maximum magnitude.",
          r"y_k = y_k^{0} + \mathrm{sat}_{\pm d_{max}}\big(r\,(t-t_0)\big)",
          {"rate_per_day": Param(0.25, "unit/day", "drift rate r"), "max_abs": Param(5.0, "point unit", "d_max")})
def _sensor_drift(inj, s, ov, ctx):
    if s <= 0:
        return
    days = (ctx.time - inj.start).total_seconds() / 86400.0
    d = float(inj.p("rate_per_day")) * days
    m = float(inj.p("max_abs"))
    ov.sensor_overlay(inj.target).bias += max(-m, min(m, d))


@register("sensor_gain", "fault", "sensor", "point:sensor",
          "Multiplicative scaling error (e.g. wrong flow-pickup K-factor).",
          r"y_k = (1 + s(t)\,g)\,x_k + \dots", {"gain": Param(0.2, "-", "relative gain error g")})
def _sensor_gain(inj, s, ov, ctx):
    ov.sensor_overlay(inj.target).gain += s * float(inj.p("gain"))


@register("sensor_noise", "fault", "sensor", "point:sensor",
          "Excessive measurement noise (loose wiring, EMI).",
          r"y_k = y_k^{0} + s(t)\,\sigma\,\varepsilon_k,\ \varepsilon_k\sim\mathcal N(0,1)",
          {"std": Param(1.0, "point unit", "noise standard deviation sigma")})
def _sensor_noise(inj, s, ov, ctx):
    o = ov.sensor_overlay(inj.target)
    o.noise_std = math.hypot(o.noise_std, s * float(inj.p("std")))


@register("sensor_stuck", "fault", "sensor", "point:sensor",
          "Sensor output frozen at its last value (or a given value).",
          r"y_k = y_{k_0}\ \ \forall k \ge k_0", {"value": Param(None, "point unit", "frozen value (None = last value)")})
def _sensor_stuck(inj, s, ov, ctx):
    if s > 0:
        o = ov.sensor_overlay(inj.target)
        o.stuck = True
        o.stuck_value = inj.p("value")


@register("sensor_spikes", "fault", "sensor", "point:sensor",
          "Random outlier spikes.", r"y_k = y_k^{0} + B_k\,\sigma_s\,\eta_k,\ B_k\sim\mathrm{Bern}(p)",
          {"prob": Param(0.05, "-", "spike probability p per sample"), "std": Param(5.0, "point unit", "sigma_s")})
def _sensor_spikes(inj, s, ov, ctx):
    o = ov.sensor_overlay(inj.target)
    o.spike_prob += s * float(inj.p("prob"))
    o.spike_std = max(o.spike_std, float(inj.p("std")))


@register("sensor_dropout", "fault", "sensor", "point:sensor",
          "Intermittent or complete loss of samples (failing transmitter).",
          r"P(\text{missing}_k)=s(t)\,p", {"prob": Param(1.0, "-", "loss probability p (1 = offline)")})
def _sensor_dropout(inj, s, ov, ctx):
    p = s * float(inj.p("prob"))
    o = ov.sensor_overlay(inj.target)
    if p >= 1.0:
        o.missing = True
    else:
        o.p_gb += p


@register("sensor_override", "fault", "sensor", "point:sensor",
          "Spoofed / overwritten value (cyber-physical attack or wiring swap).",
          r"y_k = v", {"value": Param(20.0, "point unit", "reported value v")})
def _sensor_override(inj, s, ov, ctx):
    if s > 0:
        ov.sensor_overlay(inj.target).override = float(inj.p("value"))


# ============================================================================= ACTUATOR faults
@register("vav_damper_stuck", "fault", "actuator", "equip:VAV",
          "VAV damper stuck at a fixed position regardless of the command.",
          r"\phi^{real}_k = \phi_{stuck}", {"position": Param(30.0, "%", "stuck damper position")})
def _vav_stuck(inj, s, ov, ctx):
    if s > 0:
        ov.damper_stuck[inj.target] = float(inj.p("position")) / 100.0


@register("reheat_valve_stuck_closed", "fault", "actuator", "equip:VAV",
          "VAV reheat valve stuck closed (no reheat available).", r"\dot m_{w,rh} = 0", {})
def _rh_closed(inj, s, ov, ctx):
    if s > 0:
        ov.reheat_closed.add(inj.target)


@register("reheat_valve_stuck_open", "fault", "actuator", "equip:VAV",
          "VAV reheat valve stuck open / leaking: unbounded reheat until the zone reaches the forced temperature.",
          r"T^{E+}_{htg} = T_{force}", {"force_temp": Param(26.0, "degC", "temperature reached with full reheat")})
def _rh_open(inj, s, ov, ctx):
    if s > 0:
        ov.reheat_open.add(inj.target)
        ctx.extra.setdefault("reheat_force", {})[inj.target] = float(inj.p("force_temp"))


@register("oa_damper_stuck", "fault", "actuator", "equip:AHU",
          "Outdoor-air damper stuck (common economizer fault).",
          r"f^{real}_{OA} = f_{stuck}", {"position": Param(100.0, "%", "stuck OA fraction")})
def _oad_stuck(inj, s, ov, ctx):
    if s > 0:
        ov.oa_damper_stuck[inj.target] = float(inj.p("position")) / 100.0


@register("cooling_coil_valve_stuck_closed", "fault", "actuator", "equip:AHU",
          "AHU chilled-water valve stuck closed.", r"\dot m_{w,cc}=0", {})
def _cc_closed(inj, s, ov, ctx):
    if s > 0:
        ov.coil_closed.add(f"{inj.target}:CC")


@register("heating_coil_valve_stuck_closed", "fault", "actuator", "equip:AHU",
          "AHU preheat hot-water valve stuck closed.", r"\dot m_{w,hc}=0", {})
def _hc_closed(inj, s, ov, ctx):
    if s > 0:
        ov.coil_closed.add(f"{inj.target}:HC")


@register("supply_fan_failure", "fault", "actuator", "equip:AHU",
          "Supply fan trips (VFD fault / belt failure).", r"\dot V_{SA}=0", {})
def _fan_fail(inj, s, ov, ctx):
    if s > 0:
        ov.fan_failed.add(inj.target)


# ============================================================================= EQUIPMENT faults
@register("chiller_fouling", "fault", "equipment", "equip:Chiller",
          "Condenser/evaporator fouling reducing nominal capacity and COP (EnergyPlus FaultModel:Fouling:Chiller).",
          r"Q_{ref}^{f} = \big(1 - s(t)(1-r)\big) Q_{ref},\ COP^{f}_{ref} = \big(1 - s(t)(1-r)\big) COP_{ref}",
          {"ratio": Param(0.7, "-", "capacity ratio r at full severity", 0.05, 1.0)})
def _ch_foul(inj, s, ov, ctx):
    ov.fouling[inj.target] = min(ov.fouling.get(inj.target, 1.0), 1.0 - s * (1.0 - float(inj.p("ratio"))))


@register("boiler_fouling", "fault", "equipment", "equip:Boiler",
          "Boiler heat-exchanger fouling reducing nominal capacity (EnergyPlus FaultModel:Fouling:Boiler).",
          r"Q^{f}_{nom} = \big(1 - s(t)(1-r)\big) Q_{nom}", {"ratio": Param(0.7, "-", "capacity ratio r", 0.05, 1.0)})
def _blr_foul(inj, s, ov, ctx):
    ov.fouling[inj.target] = min(ov.fouling.get(inj.target, 1.0), 1.0 - s * (1.0 - float(inj.p("ratio"))))


@register("tower_fouling", "fault", "equipment", "equip:CoolingTower",
          "Cooling tower fill fouling reducing UA (EnergyPlus FaultModel:Fouling:CoolingTower).",
          r"UA^{f} = \big(1 - s(t)(1-r)\big) UA", {"ratio": Param(0.6, "-", "UA ratio r", 0.05, 1.0)})
def _ct_foul(inj, s, ov, ctx):
    ov.fouling[inj.target] = min(ov.fouling.get(inj.target, 1.0), 1.0 - s * (1.0 - float(inj.p("ratio"))))


@register("filter_fouling", "fault", "equipment", "equip:AHU",
          "Air filter loading: additional pressure drop raises fan pressure rise and power.",
          r"\Delta p_{fan} = \Delta p_{fan,0} + s(t)\,\Delta p_{add};\ \Delta p_{flt} = (\Delta p_{clean}+s\Delta p_{add})(\dot V/\dot V_d)^2",
          {"dp_add": Param(250.0, "Pa", "additional filter pressure drop at design flow")})
def _flt(inj, s, ov, ctx):
    ov.filter_dp_add[inj.target] = ov.filter_dp_add.get(inj.target, 0.0) + s * float(inj.p("dp_add"))


@register("fan_degradation", "fault", "equipment", "equip:AHU",
          "Fan/motor efficiency degradation (bearing wear, belt slip).",
          r"\eta_{fan} = \eta_{fan,0}\,(1 - s(t)\,\ell)", {"loss": Param(0.25, "-", "relative efficiency loss l", 0, 0.9)})
def _fan_deg(inj, s, ov, ctx):
    ov.fan_eff_mult[inj.target] = ov.fan_eff_mult.get(inj.target, 1.0) * (1.0 - s * float(inj.p("loss")))


@register("equipment_trip", "fault", "equipment", "equip:Chiller|Boiler|CoolingTower|Pump",
          "Primary plant equipment trip (safety lock-out).", r"\text{available}=0", {})
def _trip(inj, s, ov, ctx):
    if s > 0:
        ov.trips.add(inj.target)


# ============================================================================= CONTROL faults
@register("schedule_error_always_on", "fault", "control", "equip:AHU",
          "Occupancy schedule overridden - AHU runs 24/7 (forgotten manual override).", r"\text{mode}=\text{occupied}", {})
def _sched_on(inj, s, ov, ctx):
    if s > 0:
        ov.force_occupied.add(inj.target)


@register("schedule_error_off", "fault", "control", "equip:AHU",
          "AHU never starts (schedule deleted / wrong calendar).", r"\text{mode}=\text{unoccupied}", {})
def _sched_off(inj, s, ov, ctx):
    if s > 0:
        ov.force_unoccupied.add(inj.target)


@register("pid_mistuning", "fault", "control", "equip:VAV|AHU",
          "Controller gains multiplied by a factor (aggressive tuning leading to oscillation).",
          r"K_p' = m\,K_p,\ K_i' = m\,K_i", {"multiplier": Param(6.0, "-", "gain multiplier m")})
def _pid(inj, s, ov, ctx):
    if s > 0:
        ov.gain_mult[inj.target] = float(inj.p("multiplier"))


@register("economizer_disabled", "fault", "control", "equip:AHU",
          "Economizer logic disabled (minimum OA only).", r"f_{OA}=f_{OA,min}", {})
def _econ_off(inj, s, ov, ctx):
    if s > 0:
        ov.economizer[inj.target] = "off"


@register("economizer_always_on", "fault", "control", "equip:AHU",
          "Economizer high-limit lock-out failure - economizer enabled in hot weather.", r"\text{econ}=1", {})
def _econ_on(inj, s, ov, ctx):
    if s > 0:
        ov.economizer[inj.target] = "on"


@register("sat_reset_disabled", "fault", "control", "equip:AHU",
          "Supply-air temperature reset disabled; fixed set point.", r"T_{SA,sp}=T_{fixed}",
          {"setpoint": Param(12.8, "degC", "fixed SAT set point")})
def _sat_fix(inj, s, ov, ctx):
    if s > 0:
        ov.sat_fixed[inj.target] = float(inj.p("setpoint"))


@register("controller_frozen", "fault", "control", "equip:VAV|AHU",
          "Controller software hang - outputs frozen at last values.", r"u_k = u_{k_0}", {})
def _frozen(inj, s, ov, ctx):
    if s > 0:
        ov.frozen.add(inj.target)


@register("setpoint_override", "event", "control", "equip:Zone",
          "Occupant/operator changes zone set points (e.g. space heater complaint, demand response).",
          r"T_{sp}' = T_{sp} + s(t)\,\Delta T", {"delta": Param(2.0, "K", "set point shift")})
def _sp_override(inj, s, ov, ctx):
    ov.setpoint_offset[inj.target] = ov.setpoint_offset.get(inj.target, 0.0) + s * float(inj.p("delta"))


# ============================================================================= NETWORK faults
@register("comm_loss", "fault", "network", "equip:*",
          "Controller off-line: all points of the equipment are missing; the BAS holds last values.",
          r"y_k=\text{NaN}\ \forall\ \text{points of equipment}", {})
def _comm(inj, s, ov, ctx):
    if s > 0:
        ov.comm_loss.add(inj.target)


@register("historian_outage", "fault", "network", "building",
          "Trend-log server outage: data are not archived (control unaffected).", r"\text{log}_k=\emptyset", {})
def _hist(inj, s, ov, ctx):
    if s > 0:
        ov.historian_outage = True


# ============================================================================= EVENTS
@register("occupancy_surge", "event", "occupancy", "zone|building",
          "Sudden change of occupancy (conference, evacuation drill, holiday).",
          r"P'(t) = \min\big(1, m^{s(t)} P(t)\big),\ N' = \lceil m N \rceil",
          {"multiplier": Param(1.8, "-", "occupancy multiplier m (0 = vacant)")})
def _occ(inj, s, ov, ctx):
    if s > 0:
        key = inj.target if inj.target not in ("building", "*", "") else "*"
        ov.occ_mult[key] = ov.occ_mult.get(key, 1.0) * float(inj.p("multiplier")) ** s


@register("meeting", "event", "occupancy", "zone",
          "Additional people gathering in a zone.", r"N'(t) = N(t) + s(t)\,n", {"people": Param(25, "people", "extra occupants n")})
def _meeting(inj, s, ov, ctx):
    ov.occ_add[inj.target] = ov.occ_add.get(inj.target, 0.0) + s * float(inj.p("people"))


@register("weather_change", "event", "weather", "building",
          "Weather perturbation added to the weather file (heat wave, cold snap, cloud cover).",
          r"T_{db}' = T_{db} + s\,\Delta T,\ \phi' = \phi + s\,\Delta\phi,\ I' = (1 - s(1-m_I)) I",
          {"delta_t": Param(5.0, "K", "dry-bulb offset"), "delta_rh": Param(0.0, "%", "RH offset"),
           "solar_mult": Param(1.0, "-", "solar multiplier m_I")})
def _wx(inj, s, ov, ctx):
    ov.weather_add["tdb"] = ov.weather_add.get("tdb", 0.0) + s * float(inj.p("delta_t"))
    ov.weather_add["rh"] = ov.weather_add.get("rh", 0.0) + s * float(inj.p("delta_rh"))
    ov.weather_mult["solar"] = ov.weather_mult.get("solar", 1.0) * (1 - s * (1 - float(inj.p("solar_mult"))))


@register("window_open", "event", "gains", "zone",
          "Operable window/door left open - additional infiltration.",
          r"\dot V_{inf}' = \dot V_{inf} + s(t)\,ACH\,V_z/3600", {"ach": Param(2.0, "1/h", "additional air changes")})
def _win(inj, s, ov, ctx):
    ov.infil_add_ach[inj.target] = ov.infil_add_ach.get(inj.target, 0.0) + s * float(inj.p("ach"))


@register("plug_load_change", "event", "gains", "zone|building",
          "Plug/process load change (server room, new equipment, after-hours use).",
          r"P_{plug}' = (1 + s(m-1)) P_{plug}", {"multiplier": Param(1.5, "-", "multiplier m")})
def _plug(inj, s, ov, ctx):
    key = inj.target if inj.target not in ("building", "*", "") else "*"
    ov.plug_mult[key] = ov.plug_mult.get(key, 1.0) * (1 + s * (float(inj.p("multiplier")) - 1))


@register("lighting_change", "event", "gains", "zone|building",
          "Lighting left on / turned off.", r"P_{light}' = (1 + s(m-1)) P_{light}", {"multiplier": Param(1.5, "-", "multiplier m")})
def _light(inj, s, ov, ctx):
    key = inj.target if inj.target not in ("building", "*", "") else "*"
    ov.light_mult[key] = ov.light_mult.get(key, 1.0) * (1 + s * (float(inj.p("multiplier")) - 1))


@register("outdoor_co2_change", "event", "weather", "building",
          "Change of ambient CO2 concentration (traffic, wildfire).", r"C_{out}' = C_{out}+s\,\Delta C",
          {"delta_ppm": Param(150.0, "ppm", "offset")})
def _co2(inj, s, ov, ctx):
    base = ov.outdoor_co2 if ov.outdoor_co2 is not None else ctx.outdoor_co2_base
    ov.outdoor_co2 = base + s * float(inj.p("delta_ppm"))


@register("holiday", "event", "occupancy", "building",
          "Unscheduled holiday: building unoccupied and BAS in unoccupied mode.", r"P(t)=0,\ \text{mode}=\text{unocc}", {})
def _holiday(inj, s, ov, ctx):
    if s > 0:
        ov.holiday = True
        ov.occ_mult["*"] = 0.0


# ----------------------------------------------------------------------------- manager
@dataclass
class InjectionContext:
    time: dt.datetime
    outdoor_co2_base: float = 420.0
    extra: dict[str, Any] = field(default_factory=dict)


class InjectionManager:
    def __init__(self):
        self.injections: dict[str, Injection] = {}
        self.log: list[dict[str, Any]] = []

    def add(self, inj: Injection) -> Injection:
        self.injections[inj.id] = inj
        self.log.append({"action": "add", **inj.to_dict()})
        return inj

    def clear(self, inj_id: str, when: dt.datetime) -> bool:
        inj = self.injections.get(inj_id)
        if inj is None:
            return False
        if inj.end is None or inj.end > when:
            inj.end = when
        self.log.append({"action": "clear", "id": inj_id, "time": when.isoformat()})
        return True

    def active(self, t: dt.datetime) -> list[tuple[Injection, float]]:
        out = []
        for inj in self.injections.values():
            s = inj.severity(t)
            if s > 0:
                out.append((inj, s))
        return out

    def overlays(self, t: dt.datetime, ctx: InjectionContext) -> tuple[Overlays, list[tuple[Injection, float]]]:
        ov = Overlays()
        act = self.active(t)
        for inj, s in act:
            inj.kind.apply(inj, s, ov, ctx)
        return ov, act

    def table(self) -> list[dict[str, Any]]:
        return [i.to_dict() for i in self.injections.values()]


def catalog() -> list[dict[str, Any]]:
    return [t.schema() for t in REGISTRY.values()]
