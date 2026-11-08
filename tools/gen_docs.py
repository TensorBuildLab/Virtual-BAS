"""Generate reference documentation (fault catalog, point list) from the code.

    python tools/gen_docs.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from virtualbas.realworld.faults import catalog  # noqa: E402

PIPE = "|"
ESCAPED_PIPE = "\\|"


def fault_md() -> str:
    lines = ["# Fault & event catalog", "",
             "Generated from `virtualbas/realworld/faults.py` (`python tools/gen_docs.py`).", "",
             "Every injection has a severity profile s(t) in [0, 1] (step, ramp or intermittent) and modifies one",
             "model parameter as theta(t) = theta_0 + s(t) * delta_theta. All injections are recorded as ground-truth labels.", ""]
    by_layer: dict = {}
    for f in catalog():
        by_layer.setdefault((f["category"], f["layer"]), []).append(f)
    for (cat, layer), items in sorted(by_layer.items()):
        lines += [f"## {cat.capitalize()}s - {layer} layer", "",
                  "| Type | Target | Description | Equation | Parameters |", "|---|---|---|---|---|"]
        for f in items:
            params = "<br>".join(f"`{k}`={v['default']} {v['unit']} - {v['description']}"
                                 for k, v in f["params"].items()) or "-"
            eq = f["equation"].replace(PIPE, ESCAPED_PIPE)
            target = f["target"].replace(PIPE, " / ")
            lines.append(f"| `{f['name']}` | `{target}` | {f['description']} | ${eq}$ | {params} |")
        lines.append("")
    return "\n".join(lines)


def points_md() -> str:
    from virtualbas.core import Building
    b = Building(ROOT / "buildings/large_office")
    from collections import Counter
    tiers = Counter(p.tier for p in b.catalog.points.values())
    lines = ["# BAS point list - DOE large office", "",
             f"{len(b.catalog.points)} points on {len(b.catalog.equipment)} pieces of equipment "
             "(generated automatically from the EnergyPlus model): "
             + ", ".join(f"{n} {t}" for t, n in tiers.most_common()) + ".", "",
             "Tier: **standard** = found in typical commercial BAS today, **advanced** = well-instrumented BAS, "
             "**next_gen** = rarely installed today but valuable for analytics/AI, **truth** = ground truth only. "
             "Source: energyplus (inner-space physics), model (outer-space physical model), surrogate (engineering "
             "correlation), bas (calculated by the BAS). See [point_taxonomy.md](point_taxonomy.md).", ""]
    for e in b.catalog.equipment.values():
        lines += [f"## {e.id} - {e.type}", "", e.description, "",
                  "| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |",
                  "|---|---|---|---|---|---|---|---|"]
        for pid in e.points:
            p = b.catalog.points[pid]
            sc = p.sensor_class if p.kind in ("sensor", "meter") else ""
            lines.append(f"| `{p.id}` | {p.kind} | {p.tier} | {p.source} | {p.unit} | {sc} | {p.description} | {p.brick} |")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    (ROOT / "docs/fault_catalog.md").write_text(fault_md(), encoding="utf-8")
    (ROOT / "docs/point_list_large_office.md").write_text(points_md(), encoding="utf-8")
    print("docs generated")
