"""Integration tests: require an EnergyPlus (>= 22.1) installation; skipped otherwise."""
import json
import math
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

try:
    from virtualbas import eplus
    eplus.energyplus_dir()
    HAVE_EP = True
except Exception:  # noqa: BLE001
    HAVE_EP = False

pytestmark = pytest.mark.skipif(not HAVE_EP, reason="EnergyPlus not installed")


@pytest.fixture(scope="session")
def building(tmp_path_factory):
    from virtualbas.model.prepare import PrepareOptions, prepare_model
    out = tmp_path_factory.mktemp("bldg")
    src = ROOT / "buildings/large_office/source"
    prepare_model(src / "RefBldgLargeOfficeNew2004_Chicago.idf", src / "USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw",
                  out, PrepareOptions(timesteps_per_hour=12, begin_month=7, begin_day=10, end_month=7, end_day=11))
    return out


def test_topology_and_catalog(building):
    from virtualbas.core import Building
    b = Building(building)
    topo = b.manifest.topo
    assert len(topo.terminals) == 16
    assert len(topo.air_loops) == 4
    kinds = sorted(p.kind for p in topo.plant_loops.values())
    assert "chilled_water" in kinds and "hot_water" in kinds and "condenser" in kinds
    types = {e.type for e in b.catalog.equipment.values()}
    assert {"AHU", "VAV", "Zone", "Chiller", "Boiler", "CoolingTower", "Pump"} <= types
    assert "AHU-1/SA-T" in b.catalog.points and "CH-1/KW" in b.catalog.points


def test_one_day_run_with_faults(building, tmp_path):
    from virtualbas.bas.historian import load_dataset
    from virtualbas.core import VirtualBAS
    sc = {"start": "2023-07-10", "end": "2023-07-10", "seed": 1,
          "injections": [{"type": "sensor_bias", "target": "ZN-Core_mid/ZN-T", "start": "2023-07-10T00:00:00",
                          "params": {"bias": 2.0}},
                         {"type": "vav_damper_stuck", "target": "VAV-Core_bottom", "start": "2023-07-10T00:00:00",
                          "params": {"position": 100}}]}
    v = VirtualBAS(building, out_dir=tmp_path / "run", scenario=sc, speed="max")
    res = v.run()
    assert res["exit_code"] == 0 and res["error"] is None
    assert not res["missing"], res["missing"]
    assert res["steps"] == 288
    d = load_dataset(tmp_path / "run")
    o, tr = d["observed"], d["truth"]
    occ = d["commands"]["ZN-Core_mid/OCC-MODE"] > 0.5
    # biased thermostat: the BAS holds the *observed* value near set point, the truth is ~2 K lower
    err = (o["ZN-Core_mid/ZN-T"] - tr["ZN-Core_mid/ZN-T"])[occ].median()
    assert err == pytest.approx(2.0, abs=0.4)
    # stuck-open damper: delivered flow ~ box maximum while the fan runs
    vmax = v.cat.equipment["VAV-Core_bottom"].meta["vmax_m3s"]
    fan = d["commands"]["AHU-1/SF-CMD"] > 0.5
    assert tr["VAV-Core_bottom/DA-F"][fan].median() == pytest.approx(vmax, rel=0.1)
    assert (Path(tmp_path / "run") / "injections_table.json").exists()


def test_rest_api(building):
    from fastapi.testclient import TestClient
    from virtualbas.server.app import create_app
    app = create_app(str(building), {"start": "2023-07-10", "end": "2023-07-11"}, speed="max")
    c = TestClient(app)
    v = app.state.session.vbas
    t0 = time.time()
    while v.step_count < 10 and time.time() - t0 < 120:
        time.sleep(0.2)
    assert c.get("/api/info").status_code == 200
    assert len(c.get("/api/faults/catalog").json()) > 30
    r = c.post("/api/injections", json={"type": "sensor_drift", "target": "AHU-1/SA-T", "duration": "6h"})
    assert r.status_code == 200
    assert c.post("/api/injections", json={"type": "nope", "target": "x"}).status_code == 400
    assert c.post("/api/write", json={"point": "AHU-1/SA-T-SP", "value": 14.0}).json()["ok"]
    snap = c.get("/api/snapshot", params={"truth": True}).json()
    assert "AHU-1/SA-T" in snap["points"] and "truth" in snap
    c.post("/api/control", json={"action": "stop"})
    v.engine.finished.wait(60)


def test_extended_points_physics(building):
    """Equipment-level, IEQ, weather and grid points are populated with physically consistent values."""
    from virtualbas.core import VirtualBAS
    sc = {"start": "2023-07-10", "end": "2023-07-11", "seed": 3,
          "injections": [{"type": "wildfire_smoke", "start": "2023-07-11T06:00:00", "duration": "8h",
                          "params": {"pm25_add": 150}},
                         {"type": "demand_response", "start": "2023-07-11T13:00:00", "duration": "3h"}]}
    v = VirtualBAS(building, scenario=sc)
    seen = {}

    def hook(b, t):
        if t.hour == 11 and t.minute == 0:
            seen[t.day] = dict(b.truth), dict(b.cmd)
        if t.hour == 14 and t.minute == 0 and t.day == 11:
            seen["dr"] = dict(b.truth)
    v.step_hooks.append(hook)
    r = v.run()
    assert r["error"] is None
    cat = v.cat
    tiers = {p.tier for p in cat.points.values()}
    assert {"standard", "advanced", "next_gen", "truth"} <= tiers
    tr10, cmd10 = seen[10]
    tr11, _ = seen[11]
    for z in [e.id for e in cat.equipment_of_type("Zone")]:
        assert tr10[f"{z}/ZN-PM10"] >= tr10[f"{z}/ZN-PM25"] >= 0
        assert tr10[f"{z}/ZN-TVOC"] > 0
        assert 20 < tr10[f"{z}/ZN-DBA"] < 80
        assert tr11[f"{z}/ZN-PM25"] > 3 * tr10[f"{z}/ZN-PM25"]       # smoke enters the building
    per = "ZN-Perimeter_mid_ZN_1"
    assert tr10[f"{per}/DAYLIGHT-LUX"] > 50 and tr10[f"{per}/ZN-LUX"] > tr10[f"{per}/DAYLIGHT-LUX"]
    assert 0 <= tr10["WX/SOLAR"] < 1200 and tr10["WX/OA-LUX"] > 1000
    assert 200 < tr10["CH-1/EVAP-P"] < tr10["CH-1/COND-P"] < 1500
    assert tr10["CH-1/EVAP-SAT-T"] < tr10["CH-1/CHW-LWT"] + 1e-6
    assert seen["dr"]["GRID/DR-EVENT"] == 1.0 and tr10["GRID/DR-EVENT"] == 0.0
    assert 0.05 < tr10["GRID/PRICE"] < 1.0
    # BAS analytics from present values
    assert 0.2 < cmd10["CH-1/KW-TON"] < 1.5
    assert cmd10["AHU-1/SF-RUNHRS"] > 0 and cmd10["MTR/BLDG-DMD-15"] > 100
    assert r["kpi"]["pm25_over_15_h"] > 0 and r["kpi"]["cost_usd"] > 0
