"""Command line interface: ``vbas <command>``.

    vbas doctor                                   check EnergyPlus installation
    vbas prepare  --model M.idf --weather W.epw --out buildings/my_building
    vbas serve    --building buildings/large_office [--scenario s.yaml] [--speed 60x]
    vbas run      --building buildings/large_office --scenario s.yaml --out results/run1 [--speed max]
    vbas faults                                   list injectable faults/events
    vbas points   --building buildings/large_office
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _load_scenario(path: str | None) -> dict:
    if not path:
        return {}
    import yaml
    return yaml.safe_load(Path(path).read_text()) or {}


def cmd_doctor(a) -> int:
    from . import eplus
    try:
        d = eplus.energyplus_dir()
        print(f"EnergyPlus found: {d}  (version {eplus.version_string()})")
        eplus.api()
        print("pyenergyplus API: OK")
        return 0
    except Exception as e:  # noqa: BLE001
        print("ERROR:", e)
        return 1


def cmd_prepare(a) -> int:
    from .bas.catalog import build_catalog
    from .model.prepare import PrepareOptions, prepare_model
    opts = PrepareOptions(timesteps_per_hour=a.timesteps, year=a.year, enable_co2=not a.no_co2)
    _, man = prepare_model(a.model, a.weather, a.out, opts)
    cat = build_catalog(man)
    topo = man.topo
    print(f"Prepared {a.model} -> {a.out}")
    print(f"  zones={len(topo.zones)} terminals={len(topo.terminals)} air_loops={len(topo.air_loops)} "
          f"plant_loops={len(topo.plant_loops)}")
    print(f"  BAS points: {cat.summary()}  equipment: {len(cat.equipment)}")
    cfg = Path(a.out) / "building.yaml"
    if not cfg.exists():
        cfg.write_text(f"name: {Path(a.out).name}\ncontrol:\n  profile: baseline\n")
    return 0


def cmd_run(a) -> int:
    from .core import VirtualBAS
    sc = _load_scenario(a.scenario)
    if a.start:
        sc["start"] = a.start
    if a.end:
        sc["end"] = a.end
    if a.seed is not None:
        sc["seed"] = a.seed
    if a.realism is not None:
        sc["realism"] = a.realism
    v = VirtualBAS(a.building, out_dir=a.out, scenario=sc, speed=a.speed)
    res = v.run()
    print(json.dumps(res, indent=1, default=str))
    return 0 if res.get("exit_code") == 0 else 1


def cmd_serve(a) -> int:
    from .server.app import serve
    sc = _load_scenario(a.scenario)
    if a.start:
        sc["start"] = a.start
    if a.end:
        sc["end"] = a.end
    serve(a.building, sc, a.speed, a.host, a.port, a.out)
    return 0


def cmd_faults(a) -> int:
    from .realworld.faults import catalog
    for f in catalog():
        params = ", ".join(f"{k}={v['default']}" for k, v in f["params"].items())
        print(f"{f['name']:<34} {f['category']:<6} {f['layer']:<10} target={f['target']:<28} {params}")
    return 0


def cmd_points(a) -> int:
    from .core import Building
    b = Building(a.building)
    for p in b.catalog.points.values():
        print(f"{p.id:<42} {p.kind:<9} {p.unit:<7} {p.description}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="vbas", description="EmuBAS - real-world-like BAS emulator on EnergyPlus")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("doctor", help="check the EnergyPlus installation")
    s.set_defaults(fn=cmd_doctor)
    s = sub.add_parser("prepare", help="convert an EnergyPlus model into a BAS-ready building")
    s.add_argument("--model", required=True)
    s.add_argument("--weather", required=True)
    s.add_argument("--out", required=True)
    s.add_argument("--timesteps", type=int, default=12, help="time steps per hour (BAS sampling)")
    s.add_argument("--year", type=int, default=2023)
    s.add_argument("--no-co2", action="store_true")
    s.set_defaults(fn=cmd_prepare)
    for name, fn in [("run", cmd_run), ("serve", cmd_serve)]:
        s = sub.add_parser(name, help="run headless (dataset generation)" if name == "run" else "start the BAS GUI + API")
        s.add_argument("--building", required=True)
        s.add_argument("--scenario")
        s.add_argument("--start")
        s.add_argument("--end")
        s.add_argument("--speed", default="max" if name == "run" else "60x")
        s.add_argument("--out", default=None if name == "serve" else "results/run")
        if name == "run":
            s.add_argument("--seed", type=int)
            s.add_argument("--realism", type=float)
        else:
            s.add_argument("--host", default="127.0.0.1")
            s.add_argument("--port", type=int, default=8000)
        s.set_defaults(fn=fn)
    s = sub.add_parser("faults", help="list fault & event types")
    s.set_defaults(fn=cmd_faults)
    s = sub.add_parser("points", help="list BAS points of a building")
    s.add_argument("--building", required=True)
    s.set_defaults(fn=cmd_points)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
