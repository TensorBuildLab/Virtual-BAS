"""Example 5 - convert ANY EnergyPlus model into a virtual BAS (here: DOE medium office).

Equivalent CLI:  vbas prepare --model my.idf --weather my.epw --out buildings/my_building
"""
from virtualbas import eplus
from virtualbas.core import VirtualBAS
from virtualbas.model.prepare import PrepareOptions, prepare_model

model = eplus.example_file("RefBldgMediumOfficeNew2004_Chicago.idf")
weather = eplus.weather_file("USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw")
_, manifest = prepare_model(model, weather, "buildings/medium_office", PrepareOptions(timesteps_per_hour=12))
topo = manifest.topo
print(f"zones={len(topo.zones)} VAV={len(topo.terminals)} AHU={len(topo.air_loops)} plant={len(topo.plant_loops)}")

bas = VirtualBAS("buildings/medium_office", out_dir="results/medium_office_week",
                 scenario={"start": "2023-07-10", "end": "2023-07-16"}, speed="max")
print(bas.run()["kpi"])
