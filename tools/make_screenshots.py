"""Regenerate the GUI screenshots used in the README and the paper (requires Microsoft Edge or Chrome).

    python tools/make_screenshots.py
"""
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from virtualbas.ai.client import VBASClient  # noqa: E402

PORT = 8011
BROWSERS = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe", "/usr/bin/google-chrome", "/usr/bin/chromium"]
SHOTS = {"gui_overview": "#overview?truth=1", "gui_ahu": "#ahu/AHU-2?truth=1", "gui_vav": "#vav/VAV-Core_mid?truth=1",
         "gui_plant": "#plant?truth=1", "gui_faults": "#faults?type=sensor_drift&target=ZN-Core_mid/ZN-T&truth=1",
         "gui_trends": "#trends?p=ZN-Core_mid/ZN-T,VAV-Core_mid/DA-F,VAV-Core_mid/DA-F-SP&w=3d&truth=1",
         "gui_zone": "#zone/ZN-Perimeter_mid_ZN_1?truth=1", "gui_weather": "#weather?truth=1"}


def main():
    browser = next((b for b in BROWSERS if os.path.exists(b)), None)
    if browser is None:
        sys.exit("no Edge/Chrome found")
    py = sys.executable
    srv = subprocess.Popen([py, "-m", "virtualbas.cli", "serve", "--building", str(ROOT / "buildings/large_office"),
                            "--start", "2023-07-10", "--end", "2023-07-31", "--speed", "3600x", "--port", str(PORT)],
                           cwd=str(ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    bas = VBASClient(f"http://127.0.0.1:{PORT}")
    try:
        for _ in range(120):
            try:
                st = bas.status()
                if not st.get("warmup") and st.get("step", 0) > 0:
                    break
            except Exception:  # noqa: BLE001
                pass
            time.sleep(1)
        bas.inject("sensor_drift", "ZN-Core_mid/ZN-T", params={"rate_per_day": 1.0, "max_abs": 4}, source="human",
                   note="thermostat drift (screenshot demo)")
        bas.inject("vav_damper_stuck", "VAV-Perimeter_mid_ZN_2", params={"position": 20}, start="+1d", source="random")
        bas.inject("chiller_fouling", "CH-1", params={"ratio": 0.7}, profile="ramp", ramp_s=2 * 86400, source="scenario")
        bas.inject("sensor_bias", "AHU-1/SA-T", params={"bias": 1.5}, start="+2d", source="ai", note="AI red-team test")
        bas.inject("meeting", "Core_bottom", params={"people": 40}, start="2023-07-13T13:00:00", duration="3h")
        bas.inject("comm_loss", "VAV-Perimeter_bot_ZN_2", start="2023-07-13T08:00:00", duration="12h", source="random")
        while True:
            st = bas.status()
            if st["time"] >= "2023-07-13T14:00:00":
                break
            time.sleep(0.5)
        bas.set_speed("360x")
        bas.inject("supply_fan_failure", "AHU-4", duration="4h", source="random")
        while bas.status()["time"] < "2023-07-13T15:00:00":
            time.sleep(0.5)
        bas.pause()
        time.sleep(2)
        out = ROOT / "paper/figures"
        for name, route in SHOTS.items():
            prof = tempfile.mkdtemp()
            subprocess.run([browser, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--user-data-dir={prof}",
                            "--window-size=1600,1000", "--virtual-time-budget=10000",
                            f"--screenshot={out / (name + '.png')}", f"http://127.0.0.1:{PORT}/{route}"],
                           check=False, capture_output=True, timeout=120)
            shutil.rmtree(prof, ignore_errors=True)
            print("screenshot", name)
    finally:
        try:
            bas.control("stop")
        except Exception:  # noqa: BLE001
            pass
        time.sleep(2)
        srv.terminate()


if __name__ == "__main__":
    main()
