"""Regenerate the GUI screenshots used in the README and the paper (requires Playwright + Microsoft Edge).

    python tools/make_screenshots.py            # raw screenshots -> paper/figures/gui_*.png (+ gui_boxes.json)
    python tools/make_gui_figures.py            # annotated composites -> paper/figures/fig_gui_*.pdf/png

A private server (port 8011, never the default 8000) simulates the DOE large office from Mon 10 July 2023 at 3600x.
A realistic, ground-truth-labelled state is staged through the same REST API an AI agent would use:
    - sensor_drift on the Core_mid thermostat (0.8 K/day from Monday 00:00)  -> VAV / trends pages (Experiment 2 story)
    - chiller fouling ramp, stuck VAV damper, AHU-1 SAT sensor bias, AHU-3 filter loading
    - wildfire smoke (Thu 18:00 - Sat), meeting, controller comm loss, demand response + price spike, AHU-4 fan trip
    - an operator priority-8 override of a zone cooling set point
The run is paused on Fri 14 July 2023 ~15:00 and every page is captured at device scale factor 2.
Bounding boxes of the elements used for figure callouts are written to paper/figures/gui_boxes.json.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from virtualbas.ai.client import VBASClient  # noqa: E402

PORT = 8011
OUT = ROOT / "paper/figures"
BASE = f"http://127.0.0.1:{PORT}/"
STOP_AT = "2023-07-14T15:00:00"
OVR_POINT = "ZN-Perimeter_top_ZN_1/OCC-CLG-SP"

# name, route, viewport width and height (CSS px), extra action.
# Equipment graphics (scalable SVG) are captured in a wide window; list/form/chart pages in a narrower window
# (~1080 px, a laptop-sized BAS workstation) so that the whole page body fits a printed column without
# shrinking the UI text.
W, N = 1440, 1080
SHOTS = [
    ("gui_overview", "#overview?truth=1", W, 1000, None),
    ("gui_ahu", "#ahu/AHU-1?truth=1", W, 1000, None),
    ("gui_vav", "#vav/VAV-Core_mid?truth=1", W, 1000, None),
    ("gui_plant", "#plant?truth=1", W, 1000, None),
    ("gui_trends", "#trends?p=ZN-Core_mid/ZN-T,ZN-Core_mid/CLG-SP,ZN-Core_mid/PMV&w=7d&truth=1", W, 760, None),
    ("gui_zone", "#zone/ZN-Core_mid?m=pm25&truth=1", N, 1700, None),
    ("gui_weather", "#weather?truth=1", N, 2000, None),
    ("gui_faults", "#faults?type=sensor_drift&target=ZN-Core_mid/ZN-T&truth=1", N, 1800, "expand_inj"),
    ("gui_alarms", "#alarms?truth=1", N, 1250, None),
    ("gui_points", "#points?equip=ZN-Core_mid&tier=next_gen&truth=1", W, 1000, None),
    ("gui_points_tiers", "#points?equip=ZN-Core_mid&tier=next_gen&truth=1", N, 700, None),
    ("gui_point_dialog", "#points?equip=ZN-Perimeter_top_ZN_1&truth=1", N, 900, "dialog"),
]

# elements whose boxes are recorded for callouts (first match per selector)
SELECTORS = ["#h-clock", "#h-state", "#h-speed", "#h-pause", "#h-step", ".truth-switch", "#h-banner", "#h-nalarm",
             "#h-ninj", ".truth-banner", "#h-session", "#side", "#main", ".page-head", "#tr-chart", "#tr-chips", "#tr-win",
             ".picker", "#inj-form", ".inj-tbl", ".catalog", ".api-hint", "#al-active", "#al-hist", ".tier-sum",
             "#pt-tier", ".pt-tbl", "#dlg-point", "#pt-prio", "#pt-write", "#pt-chart", ".pt-big", ".hm-card", "#zn-chart",
             ".fault-grid", ".chaos", "#if-target"]

JS_BOXES = """(sels) => {
  const r = (el) => { const b = el.getBoundingClientRect(); return [b.x, b.y, b.width, b.height]; };
  const out = {sel: {}, pid: {}, cls: {}};
  for (const s of sels) { const el = document.querySelector(s); if (el && el.getClientRects().length) out.sel[s] = r(el); }
  for (const el of document.querySelectorAll('[data-pid]')) {
    const b = el.getBoundingClientRect();
    if (!b.width || b.bottom < 0 || b.top > innerHeight || b.right < 0 || b.left > innerWidth) continue;
    (out.pid[el.dataset.pid] ||= []).push(r(el));
  }
  for (const el of document.querySelectorAll('.dbadge, .card, .card-h, section, .kpi, h1')) {
    const b = el.getBoundingClientRect();
    if (!b.width || b.bottom < 0 || b.top > innerHeight) continue;
    const key = el.className + '|' + (el.textContent || '').trim().slice(0, 40);
    (out.cls[key] ||= []).push(r(el));
  }
  out.rows = [];
  for (const el of document.querySelectorAll('tbody tr, .fcard, #inj-form label, #inj-form fieldset, #inj-form code')) {
    const b = el.getBoundingClientRect();
    if (!b.width || !b.height) continue;
    out.rows.push({t: (el.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 80), b: r(el),
                   cells: Array.from(el.children).map(r)});
  }
  out.vw = innerWidth; out.vh = innerHeight;
  return out;
}"""


def wait_until(bas, iso, poll=0.5):
    while True:
        st = bas.status()
        if st["time"] >= iso or st.get("finished"):
            return st
        time.sleep(poll)


def stage(bas):
    """Inject the labelled faults and events (same REST API an AI agent uses). Absolute start times keep the
    staged state (and hence the page layouts the figure crops rely on) identical from run to run."""
    bas.inject("sensor_drift", "ZN-Core_mid/ZN-T", params={"rate_per_day": 0.8, "max_abs": 5},
               start="2023-07-10T00:00:00", source="human", note="thermostat drift")
    bas.inject("chiller_fouling", "CH-1", params={"ratio": 0.7}, start="2023-07-10T00:00:00", profile="ramp",
               ramp_s=2 * 86400, source="scenario")
    bas.inject("vav_damper_stuck", "VAV-Perimeter_mid_ZN_2", params={"position": 15}, start="2023-07-11T00:00:00",
               source="random")
    bas.inject("filter_fouling", "AHU-3", params={"dp_add": 300}, start="2023-07-11T00:00:00", profile="ramp",
               ramp_s=86400, source="scenario")
    bas.inject("sensor_bias", "AHU-1/SA-T", params={"bias": 2.5}, start="2023-07-12T00:00:00", source="ai",
               note="AI red-team test")
    bas.inject("wildfire_smoke", "building", params={"pm25_add": 150}, start="2023-07-13T18:00:00", duration="2d",
               source="scenario")
    bas.inject("comm_loss", "VAV-Perimeter_bot_ZN_2", start="2023-07-14T08:00:00", duration="12h", source="random")
    bas.inject("meeting", "Core_bottom", params={"people": 40}, start="2023-07-14T13:00:00", duration="3h",
               source="human")
    bas.inject("demand_response", "building", params={"shed_kw": 300}, start="2023-07-14T14:00:00", duration="4h",
               source="scenario")
    bas.inject("price_spike", "building", params={"multiplier": 4.0}, start="2023-07-14T14:00:00", duration="4h",
               source="scenario")
    bas.inject("supply_fan_failure", "AHU-4", start="2023-07-14T13:40:00", duration="4h", source="random")


def capture(shots):
    from playwright.sync_api import sync_playwright
    boxes = {}
    with sync_playwright() as p:
        br = p.chromium.launch(channel="msedge")
        for name, route, w, h, action in shots:
            ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=2)
            page = ctx.new_page()
            page.goto(BASE + route)
            page.wait_for_function("() => document.querySelector('#h-clock')?.textContent !== '--:--' && "
                                   "!document.querySelector('#main .loading')", timeout=60000)
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(4500)
            if action == "expand_inj":   # show every injection row (the table normally scrolls)
                page.add_style_tag(content=".inj-wrap { max-height: none !important; }")
                page.wait_for_timeout(500)
            if action == "dialog":
                page.click(f'tr[data-pid="{OVR_POINT}"] td:nth-child(2)')
                page.wait_for_timeout(3500)
            page.screenshot(path=str(OUT / f"{name}.png"))
            boxes[name] = page.evaluate(JS_BOXES, SELECTORS)
            print("screenshot", name, flush=True)
            ctx.close()
        br.close()
    return boxes


def main():
    py = sys.executable
    srv = subprocess.Popen([py, "-m", "virtualbas.cli", "serve", "--building", str(ROOT / "buildings/large_office"),
                            "--start", "2023-07-10", "--end", "2023-07-31", "--speed", "3600x", "--port", str(PORT)],
                           cwd=str(ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    bas = VBASClient(f"http://127.0.0.1:{PORT}")
    try:
        for _ in range(240):
            try:
                st = bas.status()
                if not st.get("warmup") and st.get("step", 0) > 0:
                    break
            except Exception:  # noqa: BLE001
                pass
            time.sleep(1)
        stage(bas)
        wait_until(bas, "2023-07-14T13:30:00")
        bas.set_speed("360x")
        bas.write(OVR_POINT, 23.0, priority=8, source="operator")
        wait_until(bas, STOP_AT, poll=0.2)
        bas.pause()
        time.sleep(2)
        boxes = capture(SHOTS)
        (OUT / "gui_boxes.json").write_text(json.dumps(boxes, indent=0))
    finally:
        try:
            bas.control("stop")
        except Exception:  # noqa: BLE001
            pass
        time.sleep(2)
        srv.terminate()
        try:
            srv.wait(10)
        except subprocess.TimeoutExpired:
            srv.kill()


if __name__ == "__main__":
    main()
