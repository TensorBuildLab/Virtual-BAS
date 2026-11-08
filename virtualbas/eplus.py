"""Locate an EnergyPlus installation and import its Python API (pyenergyplus).

Search order:
1. ``ENERGYPLUS_DIR`` environment variable
2. Common install locations for Windows, Linux and macOS (newest version first)
"""
from __future__ import annotations

import glob
import os
import platform
import sys
from functools import lru_cache
from pathlib import Path

SUPPORTED_MIN = (22, 1)


def _candidates() -> list[Path]:
    pats = []
    system = platform.system()
    if system == "Windows":
        pats = [r"C:\EnergyPlusV*", r"C:\Program Files\EnergyPlusV*"]
    elif system == "Darwin":
        pats = ["/Applications/EnergyPlus-*"]
    else:
        pats = ["/usr/local/EnergyPlus-*", "/opt/EnergyPlus-*", os.path.expanduser("~/EnergyPlus-*")]
    found = []
    for p in pats:
        found.extend(glob.glob(p))
    paths = [Path(f) for f in found if (Path(f) / "pyenergyplus").is_dir()]

    def version_key(p: Path):
        digits = [int(s) for s in p.name.replace("V", "-").replace("-", " ").split() if s.isdigit()]
        return digits
    return sorted(paths, key=version_key, reverse=True)


@lru_cache(maxsize=1)
def energyplus_dir() -> Path:
    env = os.environ.get("ENERGYPLUS_DIR")
    if env:
        p = Path(env)
        if not (p / "pyenergyplus").is_dir():
            raise RuntimeError(f"ENERGYPLUS_DIR={env} does not contain pyenergyplus/")
        return p
    cands = _candidates()
    if not cands:
        raise RuntimeError(
            "EnergyPlus (>=22.1, recommended 23.2) was not found. Install it from "
            "https://github.com/NREL/EnergyPlus/releases and/or set ENERGYPLUS_DIR."
        )
    return cands[0]


def energyplus_exe() -> Path:
    d = energyplus_dir()
    exe = d / ("energyplus.exe" if platform.system() == "Windows" else "energyplus")
    return exe


def convert_input_format_exe() -> Path:
    d = energyplus_dir()
    exe = d / ("ConvertInputFormat.exe" if platform.system() == "Windows" else "ConvertInputFormat")
    return exe


@lru_cache(maxsize=1)
def api():
    """Return a cached ``pyenergyplus.api.EnergyPlusAPI`` instance."""
    d = str(energyplus_dir())
    if d not in sys.path:
        sys.path.insert(0, d)
    from pyenergyplus.api import EnergyPlusAPI  # type: ignore

    return EnergyPlusAPI()


def version_string() -> str:
    d = energyplus_dir()
    idd = d / "Energy+.idd"
    if idd.exists():
        with open(idd, "r", errors="ignore") as f:
            first = f.readline()
        if "IDD_Version" in first:
            return first.split("IDD_Version")[-1].strip()
    return d.name


def example_file(name: str) -> Path:
    return energyplus_dir() / "ExampleFiles" / name


def weather_file(name: str) -> Path:
    return energyplus_dir() / "WeatherData" / name
