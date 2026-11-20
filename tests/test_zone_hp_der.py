"""Zone heat pumps, ERVs, PV, electrical storage and water heaters on a synthetic two-room building.

Discovery / unit tests run without EnergyPlus; the rest need an EnergyPlus (>= 22.1) installation.
"""
import datetime as dt
import json
import math
from pathlib import Path

import pytest

from synthetic_small import build_model, unknown_fields, write_model
from virtualbas.control.sequences import ControlConfig, geb_battery, geb_zone_offsets
from virtualbas.model.topology import discover
from virtualbas.realworld.faults import REGISTRY, Injection, InjectionContext, InjectionManager

ROOT = Path(__file__).resolve().parents[1]
EPW = ROOT / "buildings/large_office/weather.epw"
DAY = "2023-07-10"
NEW_TYPES = ["hp_capacity_degradation", "hp_trip", "erv_fan_failure", "erv_hx_degradation", "pv_soiling",
             "inverter_trip", "battery_soc_sensor_drift", "grid_outage"]

try:
    from virtualbas import eplus
    eplus.energyplus_dir()
    HAVE_EP = True
except Exception:  # noqa: BLE001
    HAVE_EP = False
needs_ep = pytest.mark.skipif(not HAVE_EP, reason="EnergyPlus not installed")


# ============================================================================ no EnergyPlus needed
def test_discovery_zone_equipment_and_der():
    topo = discover(build_model(with_erv_b=False))
    kinds = {n: ze.kind for n, ze in topo.zone_equipment.items()}
    assert kinds == {"ROOM_A_ERV": "erv", "ROOM_A_PTHP": "heat_pump", "ROOM_B_PTHP": "heat_pump"}
    hp = topo.zone_equipment["ROOM_A_PTHP"]
    assert hp.zone == "ROOM_A" and hp.availability_schedule == "ROOM_A_PTHP_Avail"
    assert hp.cooling_coil.type == "Coil:Cooling:DX:SingleSpeed" and hp.heating_coil.type == "Coil:Heating:DX:SingleSpeed"
    assert hp.supp_coil.name == "ROOM_A_HP_SuppCoil" and hp.outlet == "ROOM_A_HP_Out"
    erv = topo.zone_equipment["ROOM_A_ERV"]
    assert erv.extra["hx"] == "ROOM_A_ERV_HX" and erv.extra["supply_fan"] == "ROOM_A_ERV_SupFan"
    assert erv.extra["hx_supply_outlet"] == "ROOM_A_ERV_HXSupOut" and erv.extra["eps_sens_heating"] == 0.75
    assert topo.zones["ROOM_B"].zone_equipment == ["ROOM_B_PTHP"]
    lc = topo.load_centers["Site_Power"]
    assert [g.name for g in lc.generators] == ["PV_Array"] and lc.inverter.extra["efficiency"] == 0.96
    assert lc.storage.type == "ElectricLoadCenter:Storage:Simple" and lc.storage.extra["capacity_j"] == 1.8e7
    assert lc.min_soc == 0.2
    wh = topo.water_heaters["DHW_Heater"]
    assert wh.fuel == "Electricity" and wh.standalone and wh.setpoint_schedule == "DHW_SP"
    # round trip through the manifest representation
    from virtualbas.model.topology import Topology
    t2 = Topology.from_dict(json.loads(json.dumps(topo.to_dict())))
    assert t2.zone_equipment["ROOM_A_PTHP"].cooling_coil.name == "ROOM_A_HP_ClgCoil"
    assert t2.load_centers["Site_Power"].storage.name == "Battery"


def test_new_fault_types_registered_and_overlays():
    for t in NEW_TYPES:
        assert t in REGISTRY
    t0 = dt.datetime(2023, 7, 1)
    m = InjectionManager()
    m.add(Injection("hp_capacity_degradation", "HP-X", t0, profile="ramp", ramp_s=7200,
                    params={"capacity_ratio": 0.5, "cop_ratio": 0.7}))
    m.add(Injection("erv_hx_degradation", "ERV-X", t0, params={"ratio": 0.2}))
    m.add(Injection("erv_fan_failure", "ERV-Y", t0, params={"fan": "exhaust"}))
    m.add(Injection("pv_soiling", "PV", t0, params={"loss": 0.3}))
    m.add(Injection("battery_soc_sensor_drift", "ESS", t0, params={"rate_per_day": 0.1}))
    m.add(Injection("grid_outage", "building", t0, params={"backup": 0}))
    t = t0 + dt.timedelta(hours=1)
    ov, _ = m.overlays(t, InjectionContext(time=t))
    assert ov.hp_degrade["HP-X"] == pytest.approx((0.75, 0.85))      # half-way up the ramp
    assert ov.erv_hx["ERV-X"] == pytest.approx(0.2) and ov.erv_fan_failed["ERV-Y"] == "exhaust"
    assert ov.pv_loss["PV"] == pytest.approx(0.3)
    assert ov.sensor["ESS/SOC"].bias == pytest.approx(0.1 / 24)
    assert ov.grid_outage and not ov.outage_backup


def test_geb_logic():
    c = ControlConfig(profile="geb")
    tou = {"on_peak_hours": [12, 18]}
    tue = 3
    assert geb_zone_offsets(c, dt.datetime(2023, 7, 11, 10, 30), tue, tou, 30.0, False) == (0.0, -1.5, "precool")
    assert geb_zone_offsets(c, dt.datetime(2023, 7, 11, 10, 30), tue, tou, 15.0, False)[1] == 0.0   # mild: no pre-cool
    assert geb_zone_offsets(c, dt.datetime(2023, 7, 11, 13, 0), tue, tou, 30.0, False) == (-1.0, 1.0, "onpeak")
    assert geb_zone_offsets(c, dt.datetime(2023, 7, 11, 13, 0), tue, tou, 30.0, True) == (-3.0, 3.0, "dr")
    assert geb_zone_offsets(c, dt.datetime(2023, 7, 9, 13, 0), 1, tou, 30.0, False)[1] == 0.0      # Sunday
    # hold before on-peak: no discharge, PV surplus stored explicitly
    assert geb_battery(c, 1.0, 0.6, 0.3, False, 1.0, 0.8, True, 2.0, 3.0) == (0.8, 0.0)
    # on-peak above reserve: native scheme (NaN, NaN); at the reserve: no discharge
    chg, dis = geb_battery(c, 2.0, 0.6, 0.3, False, 1.0, 0.0, False, 2.0, 3.0)
    assert math.isnan(chg) and math.isnan(dis)
    assert geb_battery(c, 2.0, 0.29, 0.3, False, 1.0, 0.0, False, 2.0, 3.0) == (0.0, 0.0)
    # demand response: cover the site demand, capped by the inverter / battery limit
    assert geb_battery(c, 2.0, 0.9, 0.3, True, 4.2, 0.0, False, 2.0, 3.0) == (0.0, 3.0)


# ============================================================================ EnergyPlus
@pytest.fixture(scope="module")
def small(tmp_path_factory):
    from virtualbas.model.prepare import PrepareOptions, prepare_model
    d = tmp_path_factory.mktemp("small")
    src = write_model(d / "source" / "source.epJSON")
    out = d / "bldg"
    prepare_model(src, EPW, out, PrepareOptions(timesteps_per_hour=12, begin_month=7, begin_day=10, end_month=7,
                                                end_day=12))
    return {"src": src, "bldg": out, "root": d}


def _run(small, name, sc):
    from virtualbas.bas.historian import load_dataset
    from virtualbas.core import VirtualBAS
    sc = {"start": DAY, "end": DAY, "seed": 1, "realism": 0.0, "occupancy": {"stochastic": False}, **sc}
    out = small["root"] / f"run_{name}"
    v = VirtualBAS(small["bldg"], out_dir=out, scenario=sc, speed="max")
    res = v.run()
    assert res["exit_code"] == 0 and res["error"] is None, res
    d = load_dataset(out)
    return v, res, d


@pytest.fixture(scope="module")
def null_run(small):
    return _run(small, "null", {})


def _native(src: Path, out: Path, names: list[tuple[str, str]]):
    """Native EnergyPlus run of the source model (same period / time step), values read like EmuBAS reads them."""
    import pandas as pd
    m = json.loads(src.read_text())
    m["RunPeriod"] = {"rp": {"begin_month": 7, "begin_day_of_month": 10, "end_month": 7, "end_day_of_month": 10,
                             "begin_year": 2023, "end_year": 2023}}
    out.mkdir(parents=True, exist_ok=True)
    p = out / "native.epJSON"
    p.write_text(json.dumps(m))
    api = eplus.api()
    ex, rt = api.exchange, api.runtime
    st = api.state_manager.new_state()
    for n, k in names:
        ex.request_variable(st, n, k)
    h, rows = {}, []

    def cb(s):
        if not ex.api_data_fully_ready(s) or ex.warmup_flag(s) or ex.kind_of_sim(s) != 3:
            return
        if not h:
            h.update({nk: ex.get_variable_handle(s, *nk) for nk in names})
        t = dt.datetime(2023, ex.month(s), ex.day_of_month(s)) + dt.timedelta(hours=ex.hour(s), minutes=ex.minutes(s) - 5)
        rows.append({"time": t, **{f"{n}|{k}": ex.get_variable_value(s, hh) for (n, k), hh in h.items()}})
    rt.callback_begin_system_timestep_before_predictor(st, cb)
    rt.set_console_output_status(st, False)
    assert rt.run_energyplus(st, ["-w", str(EPW), "-d", str(out), str(p)]) == 0
    api.state_manager.delete_state(st)
    return pd.DataFrame(rows).set_index("time")


@needs_ep
def test_prepare_bindings_and_hooks(small):
    from virtualbas.model.prepare import Manifest
    man = Manifest.load(small["bldg"] / "manifest.json")
    model = json.loads((small["bldg"] / "model.epJSON").read_text())
    for u in ("ROOM_A_PTHP", "ROOM_B_PTHP", "ROOM_A_ERV", "ROOM_B_ERV"):
        c = man.commands[f"{u} ENABLE"]
        assert c["kind"] == "zone_equipment_enable" and c["default"] == 1.0
        t = "ZoneHVAC:PackagedTerminalHeatPump" if u.endswith("PTHP") else "ZoneHVAC:EnergyRecoveryVentilator"
        assert model[t][u]["availability_schedule_name"] == c["schedule"]
    assert man.native["zone_equipment"]["ROOM_A_PTHP"]["avail_schedule"] == "ROOM_A_PTHP_Avail"
    assert man.commands["DHW_Heater SP"]["default"] == 50.0
    assert {"ROOM_A_PTHP DEGRADE", "ROOM_B_PTHP DEGRADE", "ROOM_A_ERV HX", "ROOM_B_ERV HX", "Site_Power PV LOSS"} <= set(man.faults)
    # DX coils use per-coil curve copies overridden by EMS
    assert model["Coil:Cooling:DX:SingleSpeed"]["ROOM_A_HP_ClgCoil"]["total_cooling_capacity_function_of_temperature_curve_name"] \
        == "VBAS ROOM_A_HP_ClgCoil CAPFT"
    assert model["HeatExchanger:AirToAir:SensibleAndLatent"]["ROOM_A_ERV_HX"]["supply_air_outlet_temperature_control"] == "Yes"
    assert model["ElectricEquipment"]["VBAS PV LOSS Site_Power"]["fraction_lost"] == 1.0
    assert "VBAS Fault Hooks" in model["EnergyManagementSystem:ProgramCallingManager"]
    # no field EnergyPlus would silently ignore
    schema = json.loads((eplus.energyplus_dir() / "Energy+.schema.epJSON").read_text())
    assert unknown_fields(model, schema) == []


@needs_ep
def test_catalog_points(small):
    from virtualbas.core import Building
    b = Building(small["bldg"])
    cat = b.catalog
    types = {e.type for e in cat.equipment.values()}
    assert {"HeatPump", "ERV", "PVSystem", "PVArray", "Battery", "WaterHeater", "Grid"} <= types
    expected = ["HP-ROOM_A/ENABLE", "HP-ROOM_A/STS", "HP-ROOM_A/ELEC-PWR", "HP-ROOM_A/HTG-Q", "HP-ROOM_A/CLG-Q",
                "HP-ROOM_A/SA-T", "HP-ROOM_A/FAN-PWR", "HP-ROOM_A/DEFROST", "HP-ROOM_A/SUPP-PWR", "HP-ROOM_A/ALM",
                "ERV-ROOM_A/ENABLE", "ERV-ROOM_A/SA-F", "ERV-ROOM_A/EA-F", "ERV-ROOM_A/SF-PWR", "ERV-ROOM_A/EF-PWR",
                "ERV-ROOM_A/HX-EFF", "PV/DC-PWR", "PV/AC-PWR", "PVA-PV_Array/DC-PWR", "ESS/SOC", "ESS/CHG-PWR",
                "ESS/DCHG-PWR", "ESS/CHG-CMD", "ESS/DCHG-CMD", "ESS/RESERVE-SP", "GRID/IMPORT-PWR", "GRID/EXPORT-PWR",
                "GRID/OUTAGE", "DHW-1/TANK-T", "DHW-1/ELEC-PWR", "DHW-1/TANK-SP"]
    missing = [p for p in expected if p not in cat.points]
    assert not missing, missing
    assert cat.points["ESS/SOC"].brick == "Battery_State_Of_Charge_Sensor" and cat.points["ESS/SOC"].unit == "-"
    assert cat.points["HP-ROOM_A/ENABLE"].writable and cat.points["HP-ROOM_A/ENABLE"].kind == "command"
    assert cat.points["GRID/IMPORT-PWR"].tags == ["elec", "grid", "power", "sensor"]
    assert cat.equipment["ZN-ROOM_A"].parent == "HP-ROOM_A"
    assert ("Electrical Storage", "Power Draw Rate", "SITE_POWER") in cat.actuators.values()
    assert ("Fan", "Fan Air Mass Flow Rate", "ROOM_B_ERV_SUPFAN") in cat.actuators.values()


@needs_ep
def test_null_run_reproduces_native_energyplus(small, null_run):
    v, res, d = null_run
    assert res["steps"] == 288
    new = [m for m in res["missing"] if not m.startswith("meter:") and any(k in m for k in ("Packaged Terminal", "Storage", "Inverter", "Generator",
                                                             "Fan ", "Water Heater", "Facility", "Exterior Equipment",
                                                             "Electrical Storage", "Curve", "Schedule"))]
    assert not new, new
    nat = _native(small["src"], small["root"] / "native", [
        ("Zone Air Temperature", "ROOM_A"), ("Zone Air Temperature", "ROOM_B"),
        ("Zone Packaged Terminal Heat Pump Electricity Rate", "ROOM_A_PTHP"),
        ("Electric Storage Simple Charge State", "Battery"),
        ("Facility Total Purchased Electricity Rate", "Whole Building"),
        ("System Node Temperature", "ROOM_A_ERV_SupOut")])
    tr = d["truth"]
    idx = nat.index.intersection(tr.index)
    assert len(idx) == 288
    for pid, col, sc in [("ZN-ROOM_A/ZN-T", "Zone Air Temperature|ROOM_A", 1.0),
                         ("ZN-ROOM_B/ZN-T", "Zone Air Temperature|ROOM_B", 1.0),
                         ("HP-ROOM_A/ELEC-PWR", "Zone Packaged Terminal Heat Pump Electricity Rate|ROOM_A_PTHP", 1e-3),
                         ("ESS/SOC-KWH", "Electric Storage Simple Charge State|Battery", 1 / 3.6e6),
                         ("GRID/IMPORT-PWR", "Facility Total Purchased Electricity Rate|Whole Building", 1e-3),
                         ("ERV-ROOM_A/SA-T", "System Node Temperature|ROOM_A_ERV_SupOut", 1.0)]:
        diff = (tr.loc[idx, pid].astype(float) - nat.loc[idx, col] * sc).abs().max()
        assert diff < 2e-3, (pid, diff)
    # ERV-ventilated zones: the IAQ model sees the ERV outdoor air
    assert tr["ZN-ROOM_A/ZN-TVOC"].iloc[60:].max() < 500.0
    assert tr["ESS/SOC"].between(0.0, 1.0).all()


@needs_ep
def test_hp_trip_twin_drifts(small, null_run):
    v, res, d = _run(small, "trip", {"injections": [{"type": "hp_trip", "target": "HP-ROOM_B", "start": f"{DAY}T09:00:00"}]})
    tr, o = d["truth"], d["observed"]
    m = (tr.index.hour >= 12) & (tr.index.hour < 18)
    assert (tr.loc[m, "ZN-ROOM_B/ZN-T"] - tr.loc[m, "ZN-ROOM_A/ZN-T"]).mean() > 1.5
    assert tr.loc[m, "ZN-ROOM_A/ZN-T"].max() < 24.6                       # the healthy twin holds its set point
    assert tr.loc[m, "HP-ROOM_B/ELEC-PWR"].max() == pytest.approx(0.0, abs=1e-6)
    assert o.loc[m, "HP-ROOM_B/ALM"].min() == 1.0 and o.loc[m, "HP-ROOM_A/ALM"].max() == 0.0
    assert any(a["id"] == "HP-ROOM_B:ALARM" for a in v.alarms.history)


@needs_ep
def test_hp_capacity_degradation(small, null_run):
    v, res, d = _run(small, "deg", {"injections": [{"type": "hp_capacity_degradation", "target": "HP-ROOM_B",
                                                    "start": f"{DAY}T00:00:00",
                                                    "params": {"capacity_ratio": 0.4, "cop_ratio": 0.6}}]})
    tr = d["truth"]
    m = (tr.index.hour >= 11) & (tr.index.hour < 18)
    cop_a, cop_b = tr.loc[m, "HP-ROOM_A/COP"].median(), tr.loc[m, "HP-ROOM_B/COP"].median()
    assert cop_b < 0.8 * cop_a
    assert tr.loc[m, "HP-ROOM_B/COMP-PLR"].mean() > 1.5 * tr.loc[m, "HP-ROOM_A/COMP-PLR"].mean()
    # healthy twin identical to the null run (the hook is local to the faulted unit)
    t0 = null_run[2]["truth"]
    assert (tr["ZN-ROOM_A/ZN-T"] - t0["ZN-ROOM_A/ZN-T"]).abs().max() < 0.05


@needs_ep
def test_erv_faults_and_soc_drift(small, null_run):
    v, res, d = _run(small, "erv", {"injections": [
        {"type": "erv_fan_failure", "target": "ERV-ROOM_B", "start": f"{DAY}T06:00:00", "params": {"fan": "supply"}},
        {"type": "erv_hx_degradation", "target": "ERV-ROOM_A", "start": f"{DAY}T00:00:00", "params": {"ratio": 0.2}},
        {"type": "battery_soc_sensor_drift", "target": "ESS", "start": f"{DAY}T00:00:00", "params": {"rate_per_day": 0.2}}]})
    tr, o = d["truth"], d["observed"]
    m = tr.index.hour >= 8
    assert tr.loc[m, "ERV-ROOM_B/SA-F"].max() < 1e-4 and tr.loc[m, "ERV-ROOM_B/EA-F"].min() > 0.015
    assert o.loc[m, "ERV-ROOM_B/ALM"].min() == 1.0
    assert tr.loc[m, "ZN-ROOM_B/ZN-TVOC"].iloc[-1] > 2 * tr.loc[m, "ZN-ROOM_A/ZN-TVOC"].iloc[-1]
    eff_a = tr["ERV-ROOM_A/HX-EFF"].dropna()
    eff_0 = null_run[2]["truth"]["ERV-ROOM_A/HX-EFF"].dropna()
    assert eff_0.median() == pytest.approx(0.75, abs=0.03)
    assert eff_a.median() == pytest.approx(0.2 * 0.75, abs=0.04)
    err = o["ESS/SOC"] - tr["ESS/SOC"]
    assert err.iloc[-1] == pytest.approx(0.2 * 23.917 / 24, abs=0.01)


@needs_ep
def test_pv_soiling_and_grid_outage(small, null_run):
    t0, k0 = null_run[2]["truth"], null_run[1]["kpi"]
    v, res, d = _run(small, "soil", {"injections": [{"type": "pv_soiling", "target": "PV", "start": f"{DAY}T00:00:00",
                                                     "params": {"loss": 0.5}}]})
    tr, k = d["truth"], res["kpi"]
    assert tr["PV/DC-PWR"].sum() == pytest.approx(0.5 * t0["PV/DC-PWR"].sum(), rel=0.05)
    assert tr["PV/LOSS-KW"].sum() > 0 and k["grid_import_kwh"] >= k0["grid_import_kwh"]
    # building load is unaffected by the compensating loss load
    assert k["elec_kwh"] == pytest.approx(k0["elec_kwh"], rel=0.02)
    # outage without backup: everything drops, PV stops (anti-islanding), only the residual import is unserved
    v, res, d = _run(small, "outage", {"injections": [{"type": "grid_outage", "target": "building", "start": f"{DAY}T12:00:00",
                                                       "end": f"{DAY}T17:00:00", "params": {"backup": 0}}]})
    tr = d["truth"]
    m = (tr.index.hour >= 13) & (tr.index.hour < 17)
    assert tr.loc[m, "GRID/OUTAGE"].min() == 1.0
    assert tr.loc[m, "PV/AC-PWR"].mean() < 0.05
    assert tr.loc[m, "HP-ROOM_A/ELEC-PWR"].max() == pytest.approx(0.0, abs=1e-6)
    assert tr.loc[m, "ZN-ROOM_A/ZN-T"].mean() > t0.loc[m, "ZN-ROOM_A/ZN-T"].mean() + 0.5
    assert tr.loc[m, "GRID/UNSERVED-KW"].mean() < 0.2


@needs_ep
def test_geb_profile(small, null_run):
    dr = [{"type": "demand_response", "target": "building", "start": f"{DAY}T15:00:00", "end": f"{DAY}T17:00:00",
           "params": {"shed_kw": 1.0}}]
    v, res, d = _run(small, "geb", {"injections": dr, "control": {"profile": "geb", "geb_precool_min_oat": 0.0,
                                                                   "geb_dr_disable": "HP-ROOM_B"}})
    c, c0 = d["commands"], null_run[2]["commands"]
    h = c.index.hour
    assert (c0["ZN-ROOM_A/CLG-SP"] - c["ZN-ROOM_A/CLG-SP"])[(h >= 10) & (h < 12)].min() == pytest.approx(1.5)   # pre-cool
    assert (c["ZN-ROOM_A/CLG-SP"] - c0["ZN-ROOM_A/CLG-SP"])[(h >= 12) & (h < 15)].min() == pytest.approx(1.0)  # on-peak
    assert (c["ZN-ROOM_A/CLG-SP"] - c0["ZN-ROOM_A/CLG-SP"])[(h >= 15) & (h < 17)].min() == pytest.approx(3.0)  # DR
    assert c["HP-ROOM_B/ENABLE"][(h >= 15) & (h < 17)].max() == 0.0
    assert c["ESS/DCHG-CMD"][(h >= 7) & (h < 12)].max() == 0.0 and c["ESS/MODE"][(h >= 7) & (h < 12)].min() == 1.0
    assert c0["ESS/MODE"].max() == 0.0          # baseline profile: native storage scheme


@needs_ep
def test_rest_cors(small):
    from fastapi.testclient import TestClient
    from virtualbas.server.app import create_app
    origin = "http://127.0.0.1:8765"
    app = create_app(str(small["bldg"]), {"start": DAY, "end": DAY}, speed="max", cors_origins=origin)
    try:
        c = TestClient(app)
        r = c.get("/api/read", params={"points": "ZN-ROOM_A/ZN-T,ESS/SOC"}, headers={"Origin": origin})
        assert r.status_code == 200 and r.headers.get("access-control-allow-origin") == origin
        assert set(r.json()["values"]) == {"ZN-ROOM_A/ZN-T", "ESS/SOC"} and "time" in r.json()
        pre = c.options("/api/snapshot", headers={"Origin": origin, "Access-Control-Request-Method": "GET"})
        assert pre.status_code == 200
    finally:
        app.state.session.vbas.stop()
        app.state.session.vbas.engine.finished.wait(timeout=60)
