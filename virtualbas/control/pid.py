r"""Discrete PI controller in velocity form (inherent anti-windup).

.. math::

    u_k = \mathrm{sat}_{[u_{min},u_{max}]}\Big(u_{k-1} + K_p\,(e_k - e_{k-1}) + K_p\frac{\Delta t}{T_i}\,e_k\Big)

with :math:`e_k = \pm(r_k - y_k)` for reverse/direct action. When the measurement is unavailable
(``NaN``) the output is held, which is what a commercial BAS controller does.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class PI:
    kp: float
    ti: float
    lo: float = 0.0
    hi: float = 1.0
    direct: bool = False   # direct acting: output rises when measurement > set point
    u: float = 0.0
    e_prev: float | None = None
    gain_mult: float = 1.0
    positional: bool = False   # positional form u = Kp e + I (no proportional kick memory)
    integ: float = 0.0

    def step(self, setpoint: float, measurement: float, dt: float) -> float:
        if measurement is None or not math.isfinite(measurement) or not math.isfinite(setpoint):
            return self.u
        e = (measurement - setpoint) if self.direct else (setpoint - measurement)
        kp = self.kp * self.gain_mult
        if self.positional:
            self.integ = min(self.hi, max(self.lo, self.integ + kp * dt / self.ti * e))
            self.u = min(self.hi, max(self.lo, kp * e + self.integ))
            self.e_prev = e
            return self.u
        de = 0.0 if self.e_prev is None else e - self.e_prev
        self.u = min(self.hi, max(self.lo, self.u + kp * de + kp * dt / self.ti * e))
        self.e_prev = e
        return self.u

    def reset(self, u: float = 0.0) -> None:
        self.u = u
        self.integ = u
        self.e_prev = None


@dataclass
class TrimRespond:
    """ASHRAE Guideline 36 trim & respond set-point reset."""
    sp: float
    sp_min: float
    sp_max: float
    trim: float
    respond: float
    max_change: float
    ignores: int = 2
    period_s: float = 300.0
    _acc: float = 0.0

    def step(self, requests: int, dt: float) -> float:
        self._acc += dt
        if self._acc + 1e-9 < self.period_s:
            return self.sp
        self._acc = 0.0
        if requests <= self.ignores:
            delta = self.trim
        else:
            delta = self.respond * (requests - self.ignores)
            delta = max(-abs(self.max_change), min(abs(self.max_change), delta))
        self.sp = min(self.sp_max, max(self.sp_min, self.sp + delta))
        return self.sp
