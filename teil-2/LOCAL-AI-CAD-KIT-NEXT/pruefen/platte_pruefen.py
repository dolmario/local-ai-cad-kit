"""How accurate is YOUR printed markerboard + YOUR phone photo? (independent check, no part needed)

The board has a grid of small crosses (20 mm raster). They are NOT used for the registration (only the 12 markers are),
so how far they land from their nominal position in the straightened photo is an honest accuracy test of the board plane.
Parts that stand higher than the plate (a motor, a tall key) look larger from above: measure their height with a caliper.

Run: uv run --project ../foto-mcp python platte_pruefen.py <photo.jpg> [--max-fehler 0.8]
Tip: use a photo with the middle of the plate free, or at least not covering many crosses.
"""
import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "foto-mcp"))
import foto_masse as fm  # noqa: E402

PX = 12  # px per mm
KREUZ_X = [50.0 + 20.0 * i for i in range(6)]
KREUZ_Y = [55.0 + 20.0 * i for i in range(7)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("foto")
    ap.add_argument("--max-fehler", type=float, default=0.8, help="max marker residual in mm (default 0.8)")
    a = ap.parse_args()
    with Image.open(a.foto) as im:
        rgb = np.asarray(ImageOps.exif_transpose(im).convert("RGB"))
    known, size, _ = fm.referenz_laden(HERE.parent / "markerboard" / "markerboard.json")
    H, q = fm.registrieren(cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY), known, a.max_fehler)
    T = np.array([[PX, 0, 0], [0, -PX, size[1] * PX], [0, 0, 1.0]])
    flat = cv2.warpPerspective(rgb, T @ H, (int(size[0] * PX), int(size[1] * PX)), flags=cv2.INTER_CUBIC)
    gray = cv2.GaussianBlur(cv2.cvtColor(flat, cv2.COLOR_RGB2GRAY), (0, 0), 1.0)
    errs = []
    for x in KREUZ_X:
        for y in KREUZ_Y:
            px, py, r = int(x * PX), int((size[1] - y) * PX), 4 * PX
            roi = gray[py - r:py + r, px - r:px + r].astype(float)
            if roi.shape != (2 * r, 2 * r):
                continue
            dark = np.clip(np.median(roi) - roi, 0, None)
            if dark.max() < 30:
                continue  # hidden by a part or too faint
            dark[dark < 0.45 * dark.max()] = 0
            ys, xs = np.nonzero(dark)
            w = dark[ys, xs]
            errs.append(np.hypot((xs * w).sum() / w.sum() - r, (ys * w).sum() / w.sum() - r) / PX)
    if len(errs) < 8:
        print("Too few crosses visible (%d). Photo from straight above, all markers in view, plate empty." % len(errs))
        return 1
    e = np.array(errs)
    out = {"markers_used": q["ids"], "marker_residual_mean_mm": round(q["restfehler_mittel_mm"], 3),
           "crosses_checked": len(e), "cross_error_median_mm": round(float(np.median(e)), 3),
           "cross_error_p75_mm": round(float(np.percentile(e, 75)), 3),
           "note": "Median is the typical error on the plate plane. Single outliers are crosses at the plate edge or in a shadow."}
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
