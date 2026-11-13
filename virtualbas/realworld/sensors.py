r"""Mathematical sensor model of the outer (real-world) space.

For a physical quantity :math:`x_k` (the EnergyPlus *truth*) at step :math:`k` with sampling
interval :math:`\Delta t`, the value recorded by the BAS is

.. math::

    \tilde{x}_k &= \tilde{x}_{k-1} + \frac{\Delta t}{\tau + \Delta t}\,(x_k - \tilde{x}_{k-1})
        &\text{(first-order sensor dynamics)}\\
    d_k &= d_{k-1} + r\,\Delta t + \theta\,(\mu_d - d_{k-1})\,\Delta t + \sigma_d \sqrt{\Delta t}\,\xi_k
        &\text{(drift: linear + Ornstein-Uhlenbeck)}\\
    z_k &= (1 + g)\,\tilde{x}_k + b + d_k + \sigma_n \varepsilon_k + s_k
        &\text{(gain, bias, drift, white noise, spikes)}\\
    y_k &= \mathrm{clip}\big(\delta\,\mathrm{round}(z_k/\delta),\; y_{min},\; y_{max}\big)
        &\text{(quantisation and range)}

with :math:`\xi_k,\varepsilon_k \sim \mathcal{N}(0,1)` and spikes :math:`s_k = B_k\,\sigma_s\,\eta_k`,
:math:`B_k \sim \mathrm{Bernoulli}(p_s)`. Two failure modes override the output: a *stuck*
sensor returns :math:`y_k = y_{k_s}` (value frozen at the stuck instant :math:`k_s`), and a
*missing* sample returns ``NaN``. Missing data follows a two-state Gilbert-Elliott Markov chain
(good/bad) with transition probabilities :math:`p_{gb}` and :math:`p_{bg}` so that losses occur
in realistic bursts; the stationary loss rate is :math:`p_{gb}/(p_{gb}+p_{bg})`.

Every term is recorded so that the *error decomposition* :math:`y_k - x_k` is available as a
ground-truth label.
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np


@dataclass
class SensorSpec:
    """Static characteristics of a sensor class (data-sheet values)."""
    noise_std: float = 0.0          # sigma_n
    bias_std: float = 0.0           # std of the installation bias b ~ N(0, bias_std)
    gain_std: float = 0.0           # std of installation gain error g
    drift_rate_std: float = 0.0     # std of linear drift rate r [unit/day]
    drift_ou_sigma: float = 0.0     # sigma_d [unit/sqrt(day)]
    drift_ou_theta: float = 0.0     # theta [1/day]
    resolution: float = 0.0         # delta (0 = no quantisation)
    tau_s: float = 0.0              # first-order time constant [s]
    lo: float = -math.inf
    hi: float = math.inf
    spike_prob: float = 0.0
    spike_std: float = 0.0
    p_gb: float = 0.0               # good -> bad (missing) transition probability per sample
    p_bg: float = 1.0               # bad -> good transition probability per sample
    binary: bool = False            # binary sensors (status, occupancy) use flip probabilities
    p_false_on: float = 0.0
    p_false_off: float = 0.0


# Typical BAS sensor classes (values representative of commercial-grade BAS hardware)
SENSOR_CLASSES: dict[str, SensorSpec] = {
    "zone_temperature": SensorSpec(noise_std=0.05, bias_std=0.2, resolution=0.1, tau_s=120, lo=-10, hi=50,
                                   drift_rate_std=0.0005, p_gb=0.0005, p_bg=0.3),
    "air_temperature": SensorSpec(noise_std=0.08, bias_std=0.25, resolution=0.1, tau_s=30, lo=-40, hi=90,
                                  drift_rate_std=0.0005, p_gb=0.0005, p_bg=0.3),
    "outdoor_temperature": SensorSpec(noise_std=0.1, bias_std=0.3, resolution=0.1, tau_s=60, lo=-50, hi=60,
                                      drift_rate_std=0.001, p_gb=0.0005, p_bg=0.3),
    "water_temperature": SensorSpec(noise_std=0.05, bias_std=0.15, resolution=0.1, tau_s=20, lo=-5, hi=120,
                                    drift_rate_std=0.0003, p_gb=0.0005, p_bg=0.3),
    "humidity": SensorSpec(noise_std=0.5, bias_std=1.5, resolution=0.1, tau_s=60, lo=0, hi=100,
                           drift_rate_std=0.003, p_gb=0.0005, p_bg=0.3),
    "co2": SensorSpec(noise_std=8.0, bias_std=20.0, resolution=1.0, tau_s=60, lo=0, hi=5000,
                      drift_rate_std=0.1, gain_std=0.01, p_gb=0.0005, p_bg=0.3),
    "air_flow": SensorSpec(noise_std=0.01, bias_std=0.0, gain_std=0.03, resolution=0.001, tau_s=5, lo=0, hi=1e9,
                           spike_prob=0.001, spike_std=0.05, p_gb=0.0005, p_bg=0.3),
    "water_flow": SensorSpec(noise_std=0.0005, gain_std=0.02, resolution=0.0001, tau_s=5, lo=0, hi=1e9,
                             p_gb=0.0005, p_bg=0.3),
    "power": SensorSpec(noise_std=0.2, gain_std=0.01, resolution=0.1, lo=0, hi=1e9, p_gb=0.0005, p_bg=0.3),
    "pressure": SensorSpec(noise_std=3.0, bias_std=5.0, resolution=1.0, tau_s=5, lo=-50, hi=5000,
                           drift_rate_std=0.05, p_gb=0.0005, p_bg=0.3),
    "position": SensorSpec(noise_std=0.2, resolution=0.1, lo=0, hi=100, p_gb=0.0005, p_bg=0.3),
    "percent": SensorSpec(resolution=0.1, lo=0, hi=100, p_gb=0.0005, p_bg=0.3),
    "solar": SensorSpec(noise_std=3.0, gain_std=0.02, resolution=1.0, tau_s=10, lo=0, hi=1500, p_gb=0.0005, p_bg=0.3),
    "speed": SensorSpec(noise_std=0.05, resolution=0.1, lo=0, hi=30, p_gb=0.0005, p_bg=0.3),
    "binary": SensorSpec(binary=True, p_false_on=0.0, p_false_off=0.0, p_gb=0.0005, p_bg=0.3),
    "occupancy": SensorSpec(binary=True, p_false_on=0.01, p_false_off=0.05, p_gb=0.0005, p_bg=0.3),
    "energy": SensorSpec(gain_std=0.005, resolution=0.01, lo=0, hi=1e12, p_gb=0.0002, p_bg=0.5),
    "ideal": SensorSpec(),
    # small-building electrical points (kW-scale CT / revenue meters, BMS state of charge)
    "power_small": SensorSpec(noise_std=0.003, gain_std=0.01, resolution=0.001, lo=0, hi=1e9, p_gb=0.0005, p_bg=0.3),
    "thermal_power_small": SensorSpec(noise_std=0.01, gain_std=0.03, resolution=0.001, tau_s=20, lo=0, hi=1e9,
                                      p_gb=0.0005, p_bg=0.3),
    "soc": SensorSpec(noise_std=0.002, bias_std=0.01, resolution=0.001, lo=0, hi=1, p_gb=0.0005, p_bg=0.3),
    # ---- extended instrumentation (data-sheet values, see docs/point_taxonomy.md for sources)
    # outdoor T/RH transmitter +/-2-3 %RH, drift ~1 %RH/yr
    "outdoor_humidity": SensorSpec(noise_std=0.8, bias_std=2.5, resolution=0.1, tau_s=60, lo=0, hi=100,
                                   drift_rate_std=0.003, p_gb=0.0005, p_bg=0.3),
    "enthalpy": SensorSpec(noise_std=0.3, bias_std=1.0, resolution=0.1, tau_s=60, lo=-50, hi=200, p_gb=0.0005, p_bg=0.3),
    "humidity_ratio": SensorSpec(noise_std=0.1, bias_std=0.3, resolution=0.01, tau_s=60, lo=0, hi=50, p_gb=0.0005, p_bg=0.3),
    # barometer +/-0.5-1 hPa
    "barometric": SensorSpec(noise_std=0.02, bias_std=0.05, resolution=0.01, lo=50, hi=120, p_gb=0.0005, p_bg=0.3),
    # wind vane +/-3 deg
    "wind_direction": SensorSpec(noise_std=3.0, bias_std=3.0, resolution=1.0, lo=0, hi=360, p_gb=0.0005, p_bg=0.3),
    # photosensor +/-10 % (ceiling sensor-to-work-plane ratio dominates)
    "illuminance": SensorSpec(noise_std=5.0, gain_std=0.10, resolution=1.0, tau_s=5, lo=0, hi=200000, p_gb=0.0005, p_bg=0.3),
    # low-cost optical particle counter: +/-(5 ug/m3 + 5-15 %), multiplicative error dominates
    "pm_sensor": SensorSpec(noise_std=1.0, bias_std=1.5, gain_std=0.15, resolution=0.1, tau_s=60, lo=0, hi=1000,
                            drift_rate_std=0.005, p_gb=0.001, p_bg=0.3),
    # metal-oxide TVOC: relative accuracy only, large gain error and baseline drift
    "tvoc_sensor": SensorSpec(noise_std=5.0, bias_std=10.0, gain_std=0.25, resolution=1.0, tau_s=120, lo=0, hi=20000,
                              drift_ou_sigma=5.0, drift_ou_theta=0.05, p_gb=0.001, p_bg=0.3),
    # camera / thermopile people counter: ~+/-1 person or +/-10 %
    "people_count": SensorSpec(noise_std=0.6, gain_std=0.05, resolution=1.0, lo=0, hi=10000, p_gb=0.0005, p_bg=0.3),
    # globe thermometer (ISO 7726: 150 mm globe, time constant ~20 min)
    "radiant_temperature": SensorSpec(noise_std=0.1, bias_std=0.3, resolution=0.1, tau_s=1200, lo=-10, hi=60,
                                      p_gb=0.0005, p_bg=0.3),
    "comfort_index": SensorSpec(noise_std=0.05, bias_std=0.1, resolution=0.01, tau_s=300, lo=-3, hi=3, p_gb=0.0005, p_bg=0.3),
    "comfort_ppd": SensorSpec(noise_std=1.0, bias_std=1.0, resolution=0.1, tau_s=300, lo=5, hi=100, p_gb=0.0005, p_bg=0.3),
    # IEC 61672 class-2 sound level meter +/-1.4 dB
    "sound": SensorSpec(noise_std=1.0, bias_std=0.7, resolution=0.1, lo=0, hi=140, p_gb=0.0005, p_bg=0.3),
    # BTU meter, EN 1434 class 2-3 (+/-3-5 %)
    "thermal_power": SensorSpec(noise_std=0.5, gain_std=0.03, resolution=0.1, tau_s=20, lo=0, hi=1e9, p_gb=0.0005, p_bg=0.3),
    "frequency": SensorSpec(noise_std=0.05, resolution=0.1, lo=0, hi=120, p_gb=0.0005, p_bg=0.3),
    "current": SensorSpec(noise_std=0.2, gain_std=0.02, resolution=0.1, lo=0, hi=1e6, p_gb=0.0005, p_bg=0.3),
    # ISO 10816 velocity transducer
    "vibration": SensorSpec(noise_std=0.1, gain_std=0.05, resolution=0.01, tau_s=10, lo=0, hi=100, p_gb=0.0005, p_bg=0.3),
    # water-side differential pressure transmitter [kPa], +/-1 % of a 250 kPa span
    "water_dp": SensorSpec(noise_std=0.3, bias_std=1.0, resolution=0.1, tau_s=5, lo=-5, hi=1000, p_gb=0.0005, p_bg=0.3),
    "refrigerant_pressure": SensorSpec(noise_std=2.0, bias_std=5.0, gain_std=0.005, resolution=1.0, tau_s=5, lo=0, hi=5000,
                                       p_gb=0.0005, p_bg=0.3),
}


@dataclass
class SensorState:
    lag: float | None = None
    drift: float = 0.0
    bad: bool = False
    stuck_value: float | None = None
    last_output: float = math.nan


@dataclass
class FaultOverlay:
    """Time-varying additional error terms applied by active faults (outer space)."""
    bias: float = 0.0
    gain: float = 0.0
    noise_std: float = 0.0
    stuck: bool = False
    stuck_value: float | None = None
    missing: bool = False
    spike_prob: float = 0.0
    spike_std: float = 0.0
    p_gb: float = 0.0
    override: float | None = None     # spoofed / overwritten value (cyber or wiring fault)


_NO_OVERLAY = FaultOverlay()


class Sensor:
    """A single installed sensor: data-sheet class + installation draw + run-time state."""

    def __init__(self, point_id: str, spec: SensorSpec, rng: np.random.Generator, realism: float = 1.0):
        self.point_id = point_id
        self.spec = spec
        self.realism = realism
        self.rng = rng
        # installation characteristics drawn once (labelled)
        self.bias = float(rng.normal(0.0, spec.bias_std)) * realism if spec.bias_std else 0.0
        self.gain = float(rng.normal(0.0, spec.gain_std)) * realism if spec.gain_std else 0.0
        self.drift_rate = float(rng.normal(0.0, spec.drift_rate_std)) * realism if spec.drift_rate_std else 0.0
        self.state = SensorState()

    def install_info(self) -> dict[str, float]:
        return {"bias": self.bias, "gain": self.gain, "drift_rate_per_day": self.drift_rate}

    def deterministic_error(self, x: float, overlay: FaultOverlay | None = None) -> float:
        """Bias + gain + drift (+ fault bias/gain) - used by local-loop emulation."""
        ov = overlay or _NO_OVERLAY
        return (self.gain + ov.gain) * x + self.bias + ov.bias + self.state.drift

    def measure(self, x: float, dt_s: float, overlay: FaultOverlay | None = None) -> tuple[float, dict[str, Any]]:
        """Return the observed value and a label dictionary describing this sample."""
        sp, st, ov = self.spec, self.state, overlay or _NO_OVERLAY
        r = self.realism
        lab: dict[str, Any] = {}
        if x is None or not math.isfinite(x):
            return math.nan, {"missing": True}
        if sp.binary:
            on = x > 0.5
            if on and self.rng.random() < sp.p_false_off * r:
                on = False
                lab["false_off"] = True
            elif not on and self.rng.random() < sp.p_false_on * r:
                on = True
                lab["false_on"] = True
            y = 1.0 if on else 0.0
        else:
            # first-order lag
            if st.lag is None or sp.tau_s <= 0:
                st.lag = x
            else:
                st.lag += dt_s / (sp.tau_s + dt_s) * (x - st.lag)
            # drift (per day units)
            ddays = dt_s / 86400.0
            st.drift += self.drift_rate * ddays
            if sp.drift_ou_sigma or sp.drift_ou_theta:
                st.drift += sp.drift_ou_theta * (0.0 - st.drift) * ddays + sp.drift_ou_sigma * r * math.sqrt(ddays) * self.rng.normal()
            z = (1.0 + self.gain + ov.gain) * st.lag + self.bias + ov.bias + st.drift
            ns = math.hypot(sp.noise_std * r, ov.noise_std)
            if ns > 0:
                z += ns * self.rng.normal()
            p_s = sp.spike_prob * r + ov.spike_prob
            if p_s > 0 and self.rng.random() < p_s:
                z += math.hypot(sp.spike_std, ov.spike_std) * self.rng.normal()
                lab["spike"] = True
            if sp.resolution > 0:
                z = sp.resolution * round(z / sp.resolution)
            y = min(max(z, sp.lo), sp.hi)
        if ov.override is not None:
            y = float(ov.override)
            lab["override"] = True
        # stuck
        if ov.stuck:
            if st.stuck_value is None:
                st.stuck_value = ov.stuck_value if ov.stuck_value is not None else (
                    st.last_output if math.isfinite(st.last_output) else y)
            y = st.stuck_value
            lab["stuck"] = True
        else:
            st.stuck_value = None
        # missing data (bursty Gilbert-Elliott chain + forced outages)
        p_gb = sp.p_gb * r + ov.p_gb
        if st.bad:
            if self.rng.random() < sp.p_bg:
                st.bad = False
        elif p_gb > 0 and self.rng.random() < p_gb:
            st.bad = True
        if st.bad or ov.missing:
            lab["missing"] = True
            return math.nan, lab
        st.last_output = y
        return y, lab


def spec_dict(spec: SensorSpec) -> dict[str, Any]:
    return asdict(spec)
