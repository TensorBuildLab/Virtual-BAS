"""Model Context Protocol (MCP) server exposing a running Virtual BAS to LLM agents.

Start the BAS (``vbas serve ...``), then register this server in an MCP-capable client
(e.g. Claude Desktop / Claude Code)::

    {"mcpServers": {"virtual-bas": {"command": "python", "args": ["-m", "virtualbas.ai.mcp_server",
                     "--url", "http://127.0.0.1:8000"]}}}

The agent can then explore the point list, read live values and trends, write set points with
priority, and inject or clear faults/events - i.e. act as an *ambient AI* operator or as an
adversarial fault injector. Requires ``pip install "mcp<2"``.
"""
from __future__ import annotations

import argparse
import json

from .client import VBASClient


def build_server(url: str):
    from mcp.server.fastmcp import FastMCP

    bas = VBASClient(url)
    mcp = FastMCP("virtual-bas")

    @mcp.tool()
    def building_info() -> str:
        """Building, simulation clock, speed, KPIs and active alarms/injections."""
        info = bas.info()
        st = bas.status()
        return json.dumps({"info": info, "status": st}, indent=1)

    @mcp.tool()
    def list_equipment() -> str:
        """Equipment hierarchy (AHUs, VAV boxes, zones, chillers, boiler, tower, pumps) with ids and relations."""
        eq = bas.equipment()
        return json.dumps([{k: e[k] for k in ("id", "type", "description", "parent")} for e in eq], indent=1)

    @mcp.tool()
    def list_points(equip: str = "", kind: str = "") -> str:
        """BAS points (optionally filtered by equipment id and kind: sensor|setpoint|command|meter|status|virtual)."""
        pts = bas.points(equip or None, kind or None)
        return json.dumps([{k: p[k] for k in ("id", "kind", "unit", "description", "tags")} for p in pts], indent=1)

    @mcp.tool()
    def read_points(points: list[str]) -> str:
        """Read present values (as the BAS sees them) of the given point ids."""
        return json.dumps(bas.read(points), indent=1)

    @mcp.tool()
    def get_trend(points: list[str], hours: float = 24.0) -> str:
        """Trend log of points for the last `hours` simulated hours (5-min samples)."""
        n = int(hours * 12)
        return json.dumps(bas.trend(points, n=n))

    @mcp.tool()
    def get_alarms() -> str:
        """Active alarms and recent alarm history."""
        return json.dumps(bas.alarms(), indent=1)

    @mcp.tool()
    def write_point(point: str, value: float, priority: int = 10, duration_hours: float = 0.0) -> str:
        """Override a set point/command (BACnet-like priority 1..16). duration_hours=0 means until released."""
        return json.dumps(bas.write(point, value, priority, duration_hours * 3600 or None))

    @mcp.tool()
    def release_point(point: str, priority: int = 10) -> str:
        """Release an override at a given priority."""
        return json.dumps(bas.write(point, None, priority))

    @mcp.tool()
    def fault_catalog() -> str:
        """All injectable fault/event types with target type, parameters (defaults, units) and defining equation."""
        return json.dumps(bas.fault_catalog(), indent=1)

    @mcp.tool()
    def inject(type: str, target: str, params: dict | None = None, duration: str = "6h", start: str = "now",
               profile: str = "step", note: str = "") -> str:
        """Inject a fault or event (labelled with source='ai'). duration like '30m', '6h', '2d'."""
        return json.dumps(bas.inject(type, target, params or {}, start=start, duration=duration, profile=profile,
                                     source="ai", note=note), indent=1)

    @mcp.tool()
    def clear_injection(injection_id: str) -> str:
        """End an injection now."""
        return json.dumps(bas.clear(injection_id))

    @mcp.tool()
    def list_injections() -> str:
        """All injections so far (ground-truth labels incl. severity)."""
        return json.dumps(bas.injections(), indent=1)

    @mcp.tool()
    def simulation_control(action: str, value: str = "") -> str:
        """pause | resume | step (value = number of 5-min steps) | speed (value = 1x, 10x, 60x, 360x, max)."""
        v = int(value) if action == "step" and value else (value or None)
        return json.dumps(bas.control(action, v))

    return mcp


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8000")
    a = ap.parse_args()
    build_server(a.url).run()


if __name__ == "__main__":
    main()
