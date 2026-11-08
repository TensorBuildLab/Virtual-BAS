"""Tests of the extended environment (IAQ, light, sound, feedback, forecast, grid) and the BAS analytics."""
import datetime as dt
import math
from pathlib import Path

import numpy as np
import pytest

from virtualbas.realworld.environment import EnvConfig, WeatherFile, WeatherForecast, filter_efficiency, tou_price

ROOT = Path(__file__).resolve().parents[1]
EPW = ROOT / "buildings/large_office/weather.epw"


def test_mass_balance_steady_state():
    """Exact integration of V dC/dt = Q Cs + S - (Q + kV) C converges to the analytic steady state."""
    V, Q, k, Cs, S = 300.0, 0.5, 0.2 / 3600, 5.0, 10.0   # m3, m3/s, 1/s, ug/m3, ug/s
    b = Q / V + k
    cstar = (Q * Cs + S) / (b * V)
    C = 0.0
    for _ in range(2000):
        C = cstar + (C - cstar) * math.exp(-b * 300.0)
    assert C == pytest.approx(cstar, rel=1e-9)
    assert cstar == pytest.approx((0.5 * 5 + 10) / (0.5 + 0.2 / 3600 * 300))


def test_filter_efficiency_monotonic():
    e = [filter_efficiency(m) for m in (6, 8, 10, 13, 16)]
    assert all(a[0] < b[0] for a, b in zip(e, e[1:]))
    assert all(fine < coarse for fine, coarse in e)


def test_tou_price_periods():
    c = EnvConfig()
    mon = dt.datetime(2023, 7, 10, 15, 0)            # Monday, on-peak
    assert tou_price(c, mon, dow=2) == (c.tou["on_peak"], 2)
    assert tou_price(c, mon.replace(hour=3), dow=2)[1] == 0
    assert tou_price(c, mon.replace(hour=9), dow=2)[1] == 1
    assert tou_price(c, mon, dow=1)[1] == 0          # Sunday


@pytest.mark.skipif(not EPW.exists(), reason="weather file missing")
def test_forecast_error_grows_with_lead():
    wf = WeatherFile(EPW, 2023)
    assert wf.n == 8760
    errs = {1: [], 24: [], 48: []}
    fc = WeatherForecast(wf, EnvConfig(), np.random.default_rng(0))
    t = dt.datetime(2023, 1, 1)
    for i in range(24 * 120):
        fc.update(t + dt.timedelta(hours=i))
        for h in errs:
            errs[h].append(fc.lead("tdb", h) - fc.lead("tdb", h, truth=True))
    rmse = {h: float(np.sqrt(np.mean(np.square(v)))) for h, v in errs.items()}
    assert rmse[1] < rmse[24] < rmse[48]
    assert 0.2 < rmse[1] < 1.0 and 1.0 < rmse[24] < 3.5


def test_new_injection_types_registered():
    from virtualbas.realworld.faults import REGISTRY, Injection, InjectionContext, InjectionManager
    for name in ("wildfire_smoke", "indoor_pollutant_source", "filter_bypass", "demand_response", "price_spike"):
        assert name in REGISTRY
    m = InjectionManager()
    t0 = dt.datetime(2023, 7, 10)
    m.add(Injection("wildfire_smoke", "building", t0, params={"pm25_add": 100}))
    m.add(Injection("demand_response", "building", t0, params={"shed_kw": 250}))
    m.add(Injection("indoor_pollutant_source", "Core_mid", t0))
    ov, act = m.overlays(t0 + dt.timedelta(hours=1), InjectionContext(time=t0))
    assert ov.outdoor_pm_add == pytest.approx(100.0)
    assert ov.dr_shed_kw == pytest.approx(250.0)
    assert ov.indoor_src["Core_mid"]["tvoc"] > 0
