r"""Stochastic occupancy model (inhomogeneous Markov chain after Page et al., 2008).

For each zone with :math:`N` design occupants and a presence-probability profile :math:`P(t)`
(the zone's EnergyPlus occupancy schedule, scaled by a daily attendance factor
:math:`a_d\sim\mathcal{U}(a_{min}, 1)` and by events), every occupant follows a two-state chain
with transition probabilities

.. math::

    T_{01}(t) &= \frac{\mu-1}{\mu+1}P(t) + P(t+1) \\
    T_{11}(t) &= \frac{P(t)-1}{P(t)}\left[\frac{\mu-1}{\mu+1}P(t) + P(t+1)\right] + \frac{P(t+1)}{P(t)}

(clipped to [0,1]) where the *mobility* :math:`\mu` controls how frequently people move. The
aggregate count is propagated exactly with binomial draws,

.. math::

    n_{k+1} = \mathrm{Bin}(n_k, T_{11}) + \mathrm{Bin}(N - n_k, T_{01}),

whose expectation follows :math:`N\,P(t)`, while individual days differ realistically.
"""
from __future__ import annotations

import datetime as dt
import math

import numpy as np


class ZoneOccupancy:
    def __init__(self, n_design: float, rng: np.random.Generator, mobility: float = 0.3, attendance_min: float = 0.8):
        self.n_design = max(0.0, float(n_design))
        self.rng = rng
        self.mu = mobility
        self.att_min = attendance_min
        self.n = 0
        self.p_prev: float | None = None
        self.day: dt.date | None = None
        self.attendance = 1.0

    def step(self, t: dt.datetime, p_sched: float, mult: float = 1.0, add: float = 0.0) -> float:
        if self.day != t.date():
            self.day = t.date()
            self.attendance = float(self.rng.uniform(self.att_min, 1.0))
        n_cap = int(math.ceil(self.n_design * max(1.0, mult)))
        p_next = min(1.0, max(0.0, p_sched * self.attendance * mult / max(1.0, mult)))  # presence prob. per seat
        p_now = self.p_prev if self.p_prev is not None else p_next
        self.p_prev = p_next
        k = (self.mu - 1.0) / (self.mu + 1.0)
        t01 = min(1.0, max(0.0, k * p_now + p_next))
        if p_now > 1e-9:
            t11 = (p_now - 1.0) / p_now * (k * p_now + p_next) + p_next / p_now
            t11 = min(1.0, max(0.0, t11))
        else:
            t11 = 0.0
        n = min(self.n, n_cap)
        stay = self.rng.binomial(n, t11) if n > 0 else 0
        arrive = self.rng.binomial(n_cap - n, t01) if n_cap - n > 0 else 0
        self.n = stay + arrive
        return float(self.n) + max(0.0, add)


def page_expected(p: float) -> float:
    return p
