"""Helpers to read, convert and write EnergyPlus models as epJSON dictionaries."""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Iterator

from .. import eplus

EpJSON = dict[str, dict[str, dict[str, Any]]]


def load_model(path: str | Path) -> EpJSON:
    """Load an ``.idf`` or ``.epJSON`` file into a dictionary.

    IDF files are converted with EnergyPlus' own ``ConvertInputFormat`` tool so that the
    result is exactly what EnergyPlus would read.
    """
    path = Path(path)
    if path.suffix.lower() == ".epjson":
        return json.loads(path.read_text())
    if path.suffix.lower() != ".idf":
        raise ValueError(f"Unsupported model format: {path}")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "model.idf"
        shutil.copy(path, tmp)
        exe = eplus.convert_input_format_exe()
        proc = subprocess.run([str(exe), str(tmp)], cwd=td, capture_output=True, text=True)
        out = Path(td) / "model.epJSON"
        if not out.exists():
            raise RuntimeError(f"ConvertInputFormat failed for {path}:\n{proc.stdout}\n{proc.stderr}")
        return json.loads(out.read_text())


def save_model(model: EpJSON, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(model, indent=1))
    return path


def objects(model: EpJSON, obj_type: str) -> dict[str, dict[str, Any]]:
    return model.get(obj_type, {})


def iter_objects(model: EpJSON, prefix: str) -> Iterator[tuple[str, str, dict[str, Any]]]:
    for t, objs in model.items():
        if t.startswith(prefix):
            for n, o in objs.items():
                yield t, n, o


def find_object(model: EpJSON, obj_type: str, name: str) -> dict[str, Any] | None:
    """Case-insensitive lookup (EnergyPlus names are case-insensitive)."""
    objs = model.get(obj_type, {})
    if name in objs:
        return objs[name]
    up = name.upper()
    for k, v in objs.items():
        if k.upper() == up:
            return v
    return None


def add_object(model: EpJSON, obj_type: str, name: str, fields: dict[str, Any]) -> None:
    model.setdefault(obj_type, {})[name] = fields


def node_list(model: EpJSON, name_or_list: str) -> list[str]:
    """Expand a node name that may refer to a NodeList."""
    nl = find_object(model, "NodeList", name_or_list)
    if nl is None:
        return [name_or_list]
    return [n["node_name"] for n in nl.get("nodes", [])]


def add_schedule_constant(model: EpJSON, name: str, value: float, type_limits: str | None = None) -> str:
    fields: dict[str, Any] = {"hourly_value": value}
    if type_limits:
        fields["schedule_type_limits_name"] = type_limits
    add_object(model, "Schedule:Constant", name, fields)
    return name
