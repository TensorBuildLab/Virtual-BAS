"""FastAPI server: BAS web GUI + REST/WebSocket API for humans and AI agents.

Run with ``vbas serve --building buildings/large_office``. Interactive API documentation is
available at ``/docs`` (OpenAPI), which makes every function discoverable for LLM agents.
"""
from __future__ import annotations

import asyncio
import datetime as dt
import json
import math
import threading
from pathlib import Path
from typing import Any, Optional

from fastapi import Body, FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from ..core import Building, VirtualBAS, parse_speed
from ..realworld.faults import catalog as fault_catalog

STATIC = Path(__file__).parent / "static"


class InjectionIn(BaseModel):
    type: str = Field(..., description="Injection type name, see GET /api/faults/catalog")
    target: str = Field("building", description="Point id, equipment id, zone name or 'building'")
    start: Optional[str] = Field("now", description="'now', ISO time, or relative '+2h'")
    end: Optional[str] = Field(None, description="ISO time or relative to start, e.g. '+6h'")
    duration: Optional[str] = Field(None, description="Alternative to end, e.g. '6h', '2d'")
    profile: str = Field("step", description="step | ramp | intermittent")
    ramp_s: float = 3600.0
    period_s: float = 3600.0
    duty: float = 0.5
    params: dict[str, Any] = Field(default_factory=dict)
    source: str = Field("human", description="human | ai | scenario")
    note: str = ""


class WriteIn(BaseModel):
    point: str
    value: Optional[float] = Field(None, description="None relinquishes the priority slot")
    priority: int = Field(8, ge=1, le=16, description="BACnet-style priority (1 highest)")
    duration_s: Optional[float] = None
    source: str = "operator"


class ControlIn(BaseModel):
    action: str = Field(..., description="pause | resume | step | speed | stop")
    value: Optional[Any] = None


class SessionIn(BaseModel):
    scenario: dict[str, Any] = Field(default_factory=dict)
    speed: Any = "60x"


def _clean(o: Any) -> Any:
    if isinstance(o, float):
        return None if not math.isfinite(o) else o
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, (dt.datetime, dt.date)):
        return o.isoformat()
    return o


class Session:
    """Holds the running VirtualBAS instance (one simulation per server)."""

    def __init__(self, building_dir: str, out_root: str | None, scenario: dict[str, Any], speed: Any):
        self.building = Building(building_dir)
        self.out_root = Path(out_root) if out_root else None
        self.vbas: VirtualBAS | None = None
        self.lock = threading.Lock()
        self.start(scenario, speed)

    def start(self, scenario: dict[str, Any], speed: Any) -> VirtualBAS:
        with self.lock:
            if self.vbas is not None and not self.vbas.engine.finished.is_set():
                self.vbas.stop()
                self.vbas.engine.finished.wait(timeout=30)
                self.vbas.finish()
            out = None
            if self.out_root:
                out = self.out_root / dt.datetime.now().strftime("session_%Y%m%d_%H%M%S")
            self.vbas = VirtualBAS(self.building, out_dir=out, scenario=scenario, speed=speed)
            self.vbas.start()
            return self.vbas


def create_app(building_dir: str, scenario: dict[str, Any] | None = None, speed: Any = "60x",
               out_root: str | None = None) -> FastAPI:
    app = FastAPI(title="Virtual BAS", version="0.1.0",
                  description="Real-world-like Building Automation System emulator driven by EnergyPlus. "
                              "Read points, trends and alarms; write set points; inject faults and events.")
    sess = Session(building_dir, out_root, scenario or {}, speed)
    app.state.session = sess

    def V() -> VirtualBAS:
        if sess.vbas is None:
            raise HTTPException(503, "no simulation running")
        return sess.vbas

    # ------------------------------------------------------------------ static GUI
    if STATIC.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")

    @app.middleware("http")
    async def no_cache_static(request, call_next):
        resp = await call_next(request)
        if request.url.path.startswith("/static") or request.url.path == "/":
            resp.headers["Cache-Control"] = "no-cache"
        return resp

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(STATIC / "index.html")

    # ------------------------------------------------------------------ metadata
    @app.get("/api/info", summary="Building and simulation information")
    def info():
        v = V()
        man = v.b.manifest
        return _clean({"building": v.b.name, "energyplus": man.energyplus_version, "start": v.start_date,
                       "end": v.end_date, "timestep_s": 3600 / man.options.get("timesteps_per_hour", 12),
                       "control_profile": v.ccfg.profile, "realism": v.realism, "seed": v.seed,
                       "n_points": len(v.cat.points), "n_equipment": len(v.cat.equipment)})

    @app.get("/api/points", summary="BAS point list with semantic tags (Haystack) and Brick classes")
    def points(equip: Optional[str] = None, kind: Optional[str] = None):
        v = V()
        out = [p.to_dict() for p in v.cat.points.values()
               if (equip is None or p.equip == equip) and (kind is None or p.kind == kind)]
        return out

    @app.get("/api/equipment", summary="Equipment hierarchy")
    def equipment():
        v = V()
        return _clean([{"id": e.id, "type": e.type, "eplus_name": e.eplus_name, "description": e.description,
                        "parent": e.parent, "meta": e.meta, "points": e.points} for e in v.cat.equipment.values()])

    # ------------------------------------------------------------------ live data
    @app.get("/api/status", summary="Simulation clock, KPIs, alarms and injections (no point values)")
    def status():
        s = V().snapshot()
        s.pop("points", None)
        return _clean(s)

    @app.get("/api/snapshot", summary="Present values of all points")
    def snapshot(truth: bool = Query(False, description="Include EnergyPlus ground truth (inner space)")):
        return _clean(V().snapshot(include_truth=truth))

    @app.get("/api/read", summary="Read selected points")
    def read(points: str = Query(..., description="Comma separated point ids"), truth: bool = False):
        v = V()
        snap = v.snapshot(include_truth=truth)
        ids = [p.strip() for p in points.split(",") if p.strip()]
        out = {"time": snap["time"], "values": {i: snap["points"].get(i, [None, True])[0] for i in ids}}
        if truth:
            out["truth"] = {i: snap.get("truth", {}).get(i) for i in ids}
        return _clean(out)

    @app.get("/api/trend", summary="Recent trend of points from the historian ring buffer")
    def trend(points: str, n: int = 288, source: str = "observed"):
        ids = [p.strip() for p in points.split(",") if p.strip()]
        return _clean(V().hist.trend(ids, n=n, source=source))

    @app.get("/api/alarms", summary="Active alarms and alarm history")
    def alarms():
        v = V()
        return _clean({"active": v.alarms.active(), "history": v.alarms.history[-500:]})

    # ------------------------------------------------------------------ control
    @app.post("/api/control", summary="pause | resume | step (value = n) | speed (value = '1x','10x','max', number) | stop")
    def control(c: ControlIn):
        v = V()
        a = c.action.lower()
        if a == "pause":
            v.pause()
        elif a == "resume":
            v.resume()
        elif a == "step":
            v.pause()
            v.step(int(c.value or 1))
        elif a == "speed":
            v.set_speed(c.value)
        elif a == "stop":
            v.stop()
        else:
            raise HTTPException(400, f"unknown action {c.action}")
        return {"ok": True, "speed": v.speed if math.isfinite(v.speed) else "max", "paused": v.paused}

    @app.post("/api/session", summary="Restart the simulation with a new scenario")
    def new_session(s: SessionIn):
        v = sess.start(s.scenario, s.speed)
        return _clean({"ok": True, "start": v.start_date, "end": v.end_date})

    @app.post("/api/write", summary="Priority-array write to a software point (set point / command)")
    def write(w: WriteIn):
        try:
            V().write(w.point, w.value, priority=w.priority, source=w.source, duration_s=w.duration_s)
        except ValueError as e:
            raise HTTPException(400, str(e))
        return {"ok": True}

    # ------------------------------------------------------------------ faults & events
    @app.get("/api/faults/catalog", summary="All injectable fault and event types with parameters and equations")
    def faults():
        return _clean(fault_catalog())

    @app.get("/api/injections", summary="All injections (ground-truth labels)")
    def injections():
        v = V()
        return _clean([dict(i.to_dict(), severity=i.severity(v.t) if v.t else 0.0) for i in v.inj.injections.values()])

    @app.post("/api/injections", summary="Inject a fault or event")
    def inject(i: InjectionIn):
        try:
            inj = V().inject(i.model_dump(), source=i.source)
        except (ValueError, KeyError) as e:
            raise HTTPException(400, str(e))
        return _clean(inj.to_dict())

    @app.delete("/api/injections/{inj_id}", summary="Clear (end) an injection now")
    def clear(inj_id: str):
        if not V().clear(inj_id):
            raise HTTPException(404, "not found")
        return {"ok": True}

    @app.post("/api/random", summary="Enable/disable the random fault generator (rate per week)")
    def random_faults(rate_per_week: float = Body(..., embed=True), seed: Optional[int] = Body(None, embed=True)):
        V().set_random_rate(rate_per_week, seed)
        return {"ok": True}

    # ------------------------------------------------------------------ websocket
    @app.websocket("/ws")
    async def ws(socket: WebSocket):
        await socket.accept()
        truth = socket.query_params.get("truth", "0") == "1"
        try:
            while True:
                v = sess.vbas
                if v is not None:
                    await socket.send_text(json.dumps(_clean(v.snapshot(include_truth=truth))))
                await asyncio.sleep(1.0)
        except (WebSocketDisconnect, RuntimeError):
            return

    return app


def serve(building_dir: str, scenario: dict[str, Any] | None = None, speed: Any = "60x", host: str = "127.0.0.1",
          port: int = 8000, out_root: str | None = None) -> None:
    import uvicorn
    app = create_app(building_dir, scenario, speed, out_root)
    print(f"Virtual BAS GUI: http://{host}:{port}   API docs: http://{host}:{port}/docs")
    uvicorn.run(app, host=host, port=port, log_level="warning")
