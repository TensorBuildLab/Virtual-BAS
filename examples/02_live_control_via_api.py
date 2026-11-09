"""Example 2 - interact with a running EmuBAS over REST (human or AI client).

Start the server first:
    vbas serve --building buildings/large_office --scenario scenarios/demo_summer.yaml
then run:
    python examples/02_live_control_via_api.py
"""
import time

from virtualbas.ai.client import VBASClient

bas = VBASClient("http://127.0.0.1:8000")
print(bas.info())
bas.set_speed("360x")
print(bas.read(["WX/OA-T", "AHU-2/SA-T", "AHU-2/SA-T-SP", "ZN-Core_mid/ZN-T", "CH-1/KW"]))

# AI-style supervisory action: raise the supply-air set point of AHU-2 for two hours (priority 10)
bas.write("AHU-2/SA-T-SP", 14.5, priority=10, duration_s=7200)

# inject a fault exactly as a person would in the GUI - but labelled as coming from an AI agent
inj = bas.inject("oa_damper_stuck", "AHU-2", params={"position": 100}, duration="6h", source="ai",
                 note="test whether the FDD agent notices a stuck-open economizer damper")
print("injected", inj["id"])
time.sleep(5)
print(bas.trend(["AHU-2/OAD-POS", "AHU-2/OAD-CMD", "AHU-2/MA-T"], n=12))
print("active alarms:", bas.alarms()["active"])
