"""BAS historian: trend log of observed values + ground-truth recorder.

Four synchronised tables are written as Parquet (one row per BAS sample):

``observed.parquet``  what a real BAS trend log would contain (``NaN`` = missing sample)
``truth.parquet``     EnergyPlus physical truth for every sensor point (+ ground-truth-only points)
``commands.parquet``  controller outputs / set points / commands (software points)
``labels.parquet``    per-point sample label bit-mask (see :data:`LABEL_BITS`)

plus ``injections.parquet`` (long table: time, injection id, severity) and JSON metadata.
An in-memory ring buffer serves live trends to the GUI and to AI agents.
"""
from __future__ import annotations

import collections
import json
import math
import threading
from pathlib import Path
from typing import Any

import numpy as np

LABEL_BITS = {"missing": 1, "stuck": 2, "spike": 4, "fault": 8, "comm_loss": 16, "false_binary": 32, "override": 64}


class Historian:
    def __init__(self, out_dir: str | Path | None, obs_cols: list[str], truth_cols: list[str], cmd_cols: list[str],
                 chunk_rows: int = 2016, ring: int = 4032):
        self.out_dir = Path(out_dir) if out_dir else None
        self.obs_cols, self.truth_cols, self.cmd_cols = obs_cols, truth_cols, cmd_cols
        self.chunk_rows = chunk_rows
        self._rows: dict[str, list] = {"observed": [], "truth": [], "commands": [], "labels": []}
        self._times: list[np.datetime64] = []
        self._inj_rows: list[tuple[np.datetime64, str, float]] = []
        self._writers: dict[str, Any] = {}
        self.lock = threading.Lock()
        self.ring_t: collections.deque = collections.deque(maxlen=ring)
        self.ring_obs: collections.deque = collections.deque(maxlen=ring)
        self.ring_truth: collections.deque = collections.deque(maxlen=ring)
        self.ring_cmd: collections.deque = collections.deque(maxlen=ring)
        self.n = 0
        self._oi = {c: i for i, c in enumerate(obs_cols)}
        self._ti = {c: i for i, c in enumerate(truth_cols)}
        self._ci = {c: i for i, c in enumerate(cmd_cols)}
        if self.out_dir:
            self.out_dir.mkdir(parents=True, exist_ok=True)

    def record(self, t, obs: dict[str, float], truth: dict[str, float], cmd: dict[str, float], labels: dict[str, int],
               injections: list[tuple[str, float]], archive: bool = True) -> None:
        o = np.array([obs.get(c, math.nan) for c in self.obs_cols], dtype=np.float32)
        tr = np.array([truth.get(c, math.nan) for c in self.truth_cols], dtype=np.float32)
        cm = np.array([cmd.get(c, math.nan) for c in self.cmd_cols], dtype=np.float32)
        lb = np.array([labels.get(c, 0) for c in self.obs_cols], dtype=np.uint8)
        t64 = np.datetime64(t, "s")
        with self.lock:
            self.ring_t.append(t64)
            self.ring_obs.append(o)
            self.ring_truth.append(tr)
            self.ring_cmd.append(cm)
            self.n += 1
        if not self.out_dir:
            return
        if archive:
            self._times.append(t64)
            self._rows["observed"].append(o)
            self._rows["truth"].append(tr)
            self._rows["commands"].append(cm)
            self._rows["labels"].append(lb)
        for iid, sev in injections:
            self._inj_rows.append((t64, iid, float(sev)))
        if len(self._times) >= self.chunk_rows:
            self.flush()

    # ------------------------------------------------------------------ trends
    def trend(self, pids: list[str], n: int = 288, source: str = "observed") -> dict[str, Any]:
        with self.lock:
            k = min(n, len(self.ring_t))
            times = [str(x) for x in list(self.ring_t)[-k:]]
            out: dict[str, Any] = {"time": times}
            rows = {"observed": self.ring_obs, "truth": self.ring_truth, "commands": self.ring_cmd}
            for pid in pids:
                if source == "truth" and pid in self._ti:
                    idx, ring = self._ti[pid], self.ring_truth
                elif pid in self._oi and source != "truth":
                    idx, ring = self._oi[pid], self.ring_obs
                elif pid in self._ci:
                    idx, ring = self._ci[pid], self.ring_cmd
                elif pid in self._ti:
                    idx, ring = self._ti[pid], self.ring_truth
                else:
                    continue
                vals = [float(r[idx]) for r in list(ring)[-k:]]
                out[pid] = [None if not math.isfinite(v) else round(v, 4) for v in vals]
            return out

    # ------------------------------------------------------------------ files
    def flush(self) -> None:
        if not self.out_dir or not self._times:
            return
        import pyarrow as pa
        import pyarrow.parquet as pq
        times = pa.array(np.array(self._times, dtype="datetime64[s]"))
        specs = {"observed": (self.obs_cols, pa.float32()), "truth": (self.truth_cols, pa.float32()),
                 "commands": (self.cmd_cols, pa.float32()), "labels": (self.obs_cols, pa.uint8())}
        for name, (cols, typ) in specs.items():
            arr = np.vstack(self._rows[name]) if self._rows[name] else np.zeros((0, len(cols)))
            table = pa.table([times] + [pa.array(arr[:, i], type=typ) for i in range(len(cols))], names=["time"] + cols)
            w = self._writers.get(name)
            if w is None:
                w = pq.ParquetWriter(str(self.out_dir / f"{name}.parquet"), table.schema, compression="zstd")
                self._writers[name] = w
            w.write_table(table)
            self._rows[name] = []
        self._times = []
        if self._inj_rows:
            t = pa.table({"time": pa.array(np.array([r[0] for r in self._inj_rows], dtype="datetime64[s]")),
                          "injection_id": pa.array([r[1] for r in self._inj_rows]),
                          "severity": pa.array([r[2] for r in self._inj_rows], type=pa.float32())})
            w = self._writers.get("injections")
            if w is None:
                w = pq.ParquetWriter(str(self.out_dir / "injections.parquet"), t.schema, compression="zstd")
                self._writers["injections"] = w
            w.write_table(t)
            self._inj_rows = []

    def close(self, meta: dict[str, Any] | None = None) -> None:
        self.flush()
        for w in self._writers.values():
            w.close()
        self._writers = {}
        if self.out_dir and meta is not None:
            (self.out_dir / "metadata.json").write_text(json.dumps(meta, indent=1, default=str))


def load_dataset(path: str | Path) -> dict[str, Any]:
    """Load a recorded EmuBAS dataset into pandas DataFrames."""
    import pandas as pd
    p = Path(path)
    out: dict[str, Any] = {}
    for name in ["observed", "truth", "commands", "labels", "injections"]:
        f = p / f"{name}.parquet"
        if f.exists():
            df = pd.read_parquet(f)
            if name != "injections":
                df = df.set_index("time")
            out[name] = df
    for name in ["metadata", "points", "injections_table", "sensors"]:
        f = p / f"{name}.json"
        if f.exists():
            out[name] = json.loads(f.read_text())
    return out
