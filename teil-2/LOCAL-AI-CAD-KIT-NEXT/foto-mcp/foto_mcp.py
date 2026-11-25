"""MCP server 'photo-measure': measures a key (or a flat part) on the printed markerboard.

Tools:
  measure_key(photo_path, metal="auto")  -> head diameter, shoulder width/edges, shaft direction (mm, degrees)
  measure_flat_part(photo_path, x0, y0, x1, y1) -> outline box and area of one flat part inside a board region
Every result is a photo estimate. The model must ask the user for caliper values before building.
"""
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from mcp.server.fastmcp import FastMCP  # noqa: E402

import foto_masse as fm  # noqa: E402
import schluessel_bild as sb  # noqa: E402

REFERENZ = HERE.parent / "markerboard" / "markerboard.json"
AUSGABE = HERE.parent / "messungen"

mcp = FastMCP("photo-measure")


def _ordner(name):
    path = AUSGABE / (time.strftime("%Y%m%d-%H%M%S") + "-" + name)
    n = 1
    while path.exists():
        path = AUSGABE / (time.strftime("%Y%m%d-%H%M%S") + f"-{name}-{n}")
        n += 1
    return path


def _foto(photo_path):
    p = Path(photo_path.strip().strip('"')).expanduser()
    if not p.is_file():
        raise ValueError(f"Photo not found: {p}. Give the full path to a JPG or PNG.")
    return p


@mcp.tool()
def measure_key(photo_path: str, metal: str = "auto") -> dict:
    """Measure a key lying flat in the middle of the printed markerboard (all 12 plate markers should be visible).
    metal: 'auto', 'gelb' (brass/yellow) or 'silber' (nickel/silver).
    Returns head diameter, shoulder width, shoulder edges across the shaft and shaft direction in mm/degrees,
    plus 'kontrollbild' (overlay image the user should look at). Photo estimate only: ask the user to confirm
    head diameter, thickness and shoulder width with a caliper before building anything."""
    try:
        if metal not in ("auto", "gelb", "silber"):
            raise ValueError("metal must be 'auto', 'gelb' or 'silber'.")
        return sb.messen(_foto(photo_path), REFERENZ, _ordner("schluessel"), metall=metal)
    except Exception as exc:  # report, never guess
        return {"status": "error", "message": str(exc),
                "hint": "Lay the board flat, light it evenly without hard shadows, keep all markers in the photo, "
                        "shoot from straight above. Do not guess values."}


@mcp.tool()
def measure_flat_part(photo_path: str, x0: float, y0: float, x1: float, y1: float) -> dict:
    """Outline of ONE flat dark part inside the board region x0..x1, y0..y1 (mm, origin bottom left of the plate,
    region must not contain a marker). Returns the rotated bounding box and area. Photo estimate only."""
    try:
        return fm.foto_masse(_foto(photo_path), REFERENZ, _ordner("teil"), roi=(x0, y0, x1, y1))
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@mcp.tool()
def markerboard_info() -> dict:
    """Describe the printed markerboard: size, marker ids and where to put the part."""
    d = json.loads(REFERENZ.read_text("utf-8-sig"))
    plate = sorted(int(k) for k, v in d["marker_3d"].items() if v["teil"] == "PLATTE")
    return {"plate_mm": d["platte_mm"], "plate_marker_ids": plate,
            "free_area_hint": "Put the part in the middle of the plate, away from the black markers.",
            "dictionary": "ArUco DICT_4X4_50"}


if __name__ == "__main__":
    mcp.run()
