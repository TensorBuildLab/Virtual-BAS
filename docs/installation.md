# Installation

Virtual BAS needs **Python ≥ 3.9** and **EnergyPlus ≥ 22.1** (tested with **23.2.0**, recommended).
Everything else is installed with `pip`.

## 1. Install EnergyPlus 23.2

Download the installer for your OS from the
[EnergyPlus 23.2.0 release page](https://github.com/NREL/EnergyPlus/releases/tag/v23.2.0) and install it to the default
location:

| OS | Default location searched automatically |
|---|---|
| Windows | `C:\EnergyPlusV23-2-0` |
| Linux | `/usr/local/EnergyPlus-23-2-0` |
| macOS | `/Applications/EnergyPlus-23-2-0` |

If you install it elsewhere (or have several versions), point Virtual BAS to it:

```bash
# Linux / macOS
export ENERGYPLUS_DIR=/opt/EnergyPlus-23-2-0
# Windows (PowerShell)
$env:ENERGYPLUS_DIR = "D:\EnergyPlusV23-2-0"
```

Virtual BAS uses the official EnergyPlus Python API (`pyenergyplus`) that ships with EnergyPlus; nothing else from
EnergyPlus needs to be configured. The DOE large-office model shipped in `buildings/large_office/source/` was written
for EnergyPlus 23.2. For other versions, transition the IDF with EnergyPlus' *IDFVersionUpdater* and re-run
`vbas prepare`.

## 2. Install Virtual BAS

```bash
git clone https://github.com/TensorBuildLab/Virtual-BAS.git
cd Virtual-BAS
python -m venv .venv
# Windows: .venv\Scripts\activate      Linux/macOS: source .venv/bin/activate
pip install -e ".[all]"
```

Optional extras: `.[ai]` (Gymnasium, scikit-learn), `.[analysis]` (matplotlib, pyarrow), `.[dev]` (pytest).
For the MCP server (LLM agents) also run `pip install "mcp<2"`.

## 3. Check the installation

```bash
vbas doctor
pytest -q            # unit tests + integration tests (integration tests need EnergyPlus)
```

`vbas doctor` prints the EnergyPlus location and verifies that the Python API can be loaded.

## Troubleshooting

* **`EnergyPlus ... was not found`** - set `ENERGYPLUS_DIR` (see above).
* **`OSError: ... energyplusapi`** on Linux - install the `.tar.gz` or `.sh` release (not only the CLI) and make sure
  the directory contains `pyenergyplus/` and `libenergyplusapi.so`.
* **Port 8000 busy** - `vbas serve ... --port 8010`.
* **Slow runs** - use `--speed max` for dataset generation; one simulated year of the large office (105,120 five-minute
  BAS samples, ~450 points) takes about 3-4 minutes on a laptop.
