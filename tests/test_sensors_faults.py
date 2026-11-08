"""Unit tests of the outer-space mathematics (no EnergyPlus needed)."""
import datetime as dt
import math

import numpy as np
import pytest

from virtualbas.control.pid import PI, TrimRespond
from virtualbas.realworld.faults import REGISTRY, Injection, InjectionContext, InjectionManager
from virtualbas.realworld.occupancy import ZoneOccupancy
from virtualbas.realworld.sensors import FaultOverlay, Sensor, SensorSpec

T0 = dt.datetime(2023, 7, 1)


def test_ideal_sensor_is_identity():
    s = Sensor("p", SensorSpec(), np.random.default_rng(0))
    for x in [0.0, 21.3, -5.5]:
        y, lab = s.measure(x, 300)
        assert y == pytest.approx(x)
        assert not lab


def test_noise_statistics():
    s = Sensor("p", SensorSpec(noise_std=0.5), np.random.default_rng(1))
    ys = np.array([s.measure(20.0, 300)[0] for _ in range(20000)])
    assert ys.mean() == pytest.approx(20.0, abs=0.02)
    assert ys.std() == pytest.approx(0.5, rel=0.05)


def test_bias_gain_and_quantisation():
    s = Sensor("p", SensorSpec(resolution=0.5), np.random.default_rng(2))
    y, _ = s.measure(20.1, 300, FaultOverlay(bias=1.0, gain=0.1))
    assert y == pytest.approx(0.5 * round((1.1 * 20.1 + 1.0) / 0.5))


def test_first_order_lag():
    s = Sensor("p", SensorSpec(tau_s=300), np.random.default_rng(3))
    s.measure(0.0, 300)
    y, _ = s.measure(10.0, 300)
    assert y == pytest.approx(5.0)   # dt/(tau+dt) = 0.5


def test_stuck_freezes_last_value():
    s = Sensor("p", SensorSpec(), np.random.default_rng(4))
    s.measure(20.0, 300)
    y, lab = s.measure(25.0, 300, FaultOverlay(stuck=True))
    assert y == 20.0 and lab["stuck"]


def test_missing_rate_gilbert_elliott():
    spec = SensorSpec(p_gb=0.01, p_bg=0.2)
    s = Sensor("p", spec, np.random.default_rng(5))
    miss = np.mean([math.isnan(s.measure(1.0, 300)[0]) for _ in range(100000)])
    assert miss == pytest.approx(0.01 / (0.01 + 0.2), rel=0.15)


def test_severity_profiles():
    i = Injection("sensor_bias", "x", T0, T0 + dt.timedelta(hours=10), profile="ramp", ramp_s=3600)
    assert i.severity(T0 - dt.timedelta(seconds=1)) == 0
    assert i.severity(T0 + dt.timedelta(minutes=30)) == pytest.approx(0.5)
    assert i.severity(T0 + dt.timedelta(hours=2)) == 1
    assert i.severity(T0 + dt.timedelta(hours=10)) == 0
    j = Injection("sensor_bias", "x", T0, profile="intermittent", period_s=3600, duty=0.25)
    assert j.severity(T0 + dt.timedelta(minutes=10)) == 1
    assert j.severity(T0 + dt.timedelta(minutes=20)) == 0


def test_drift_fault_accumulates_and_saturates():
    m = InjectionManager()
    m.add(Injection("sensor_drift", "A/T", T0, params={"rate_per_day": 1.0, "max_abs": 2.5}))
    ov, _ = m.overlays(T0 + dt.timedelta(days=1), InjectionContext(T0 + dt.timedelta(days=1)))
    assert ov.sensor["A/T"].bias == pytest.approx(1.0)
    ov, _ = m.overlays(T0 + dt.timedelta(days=5), InjectionContext(T0 + dt.timedelta(days=5)))
    assert ov.sensor["A/T"].bias == pytest.approx(2.5)


def test_every_registered_type_applies():
    for name, t in REGISTRY.items():
        inj = Injection(name, "AHU-1" if "equip" in t.target else "Core_mid", T0)
        m = InjectionManager()
        m.add(inj)
        m.overlays(T0 + dt.timedelta(hours=1), InjectionContext(T0 + dt.timedelta(hours=1)))
        assert t.equation and t.description


def test_unknown_type_rejected():
    with pytest.raises(ValueError):
        Injection("does_not_exist", "x", T0)


def test_pi_reaches_setpoint_on_first_order_plant():
    pi = PI(kp=0.5, ti=600, lo=0, hi=1, direct=True)   # cooling: output up -> temperature down
    T = 26.0
    for _ in range(300):
        u = pi.step(24.0, T, 60)
        T += 60 / 1800 * ((30.0 - 8.0 * u) - T)
    assert T == pytest.approx(24.0, abs=0.05)


def test_trim_respond_bounds():
    tr = TrimRespond(sp=12.8, sp_min=12.8, sp_max=18.3, trim=0.1, respond=-0.2, max_change=0.6, ignores=2, period_s=300)
    for _ in range(100):
        tr.step(0, 300)
    assert tr.sp == pytest.approx(18.3)
    for _ in range(100):
        tr.step(10, 300)
    assert tr.sp == pytest.approx(12.8)


def test_occupancy_expectation_matches_profile():
    rng = np.random.default_rng(7)
    occ = ZoneOccupancy(100, rng, mobility=0.3, attendance_min=1.0)
    t = T0
    vals = []
    for k in range(2000):
        vals.append(occ.step(t, 0.6))
        t += dt.timedelta(minutes=5)
    assert np.mean(vals[100:]) == pytest.approx(60, rel=0.05)
