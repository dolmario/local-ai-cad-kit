"""Synthetic self-test of the photo measurement (no real photo needed).

Draws the markerboard with a key of known size, warps it like a phone photo, measures it again.
Run: uv run --project ../foto-mcp python synthetischer_test.py
"""
import json
import math
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "foto-mcp"))
import schluessel_bild as sb  # noqa: E402

REF = HERE.parent / "markerboard" / "markerboard.json"
S = 10  # px per mm on the flat board image


def board_image(key_colour, angle_deg, head_d=20.6, shoulder=9.1, offset=1.0, shaft=6.0):
    d = json.loads(REF.read_text("utf-8-sig"))
    size = d["platte_mm"][:2]
    img = np.full((int(size[1] * S), int(size[0] * S), 3), (232, 228, 218), np.uint8)
    dic = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    for mid, v in d["marker_3d"].items():
        if v["teil"] != "PLATTE":
            continue
        pts = np.array(v["ecken_mm"])[:, :2]
        x0, y1 = pts[:, 0].min(), pts[:, 1].max()
        side = int(round((pts[:, 0].max() - x0) * S))
        m = cv2.aruco.generateImageMarker(dic, int(mid), side)
        r0, c0 = int(round((size[1] - y1) * S)), int(round(x0 * S))
        img[r0:r0 + side, c0:c0 + side] = np.dstack([m] * 3)
    th = math.radians(angle_deg)
    u = np.array([math.cos(th), math.sin(th)])
    n = np.array([-math.sin(th), math.cos(th)])  # left of the shaft
    c = np.array([100.0, 100.0])
    r = head_d / 2

    def px(p):
        return [int(round(p[0] * S)), int(round((size[1] - p[1]) * S))]

    def rect(a0, a1, q0, q1):
        return np.array([px(c + u * a + n * q) for a, q in ((a0, q0), (a1, q0), (a1, q1), (a0, q1))], np.int32)

    cv2.circle(img, px(c), int(round(r * S)), key_colour, -1, lineType=cv2.LINE_AA)
    cv2.fillPoly(img, [rect(0, r + 4.0, offset - shoulder / 2, offset + shoulder / 2)], key_colour, lineType=cv2.LINE_AA)
    cv2.fillPoly(img, [rect(0, r + 45.0, -shaft / 2, shaft / 2)], key_colour, lineType=cv2.LINE_AA)
    cv2.circle(img, px(c - u * 5), int(2.75 * S), (232, 228, 218), -1, lineType=cv2.LINE_AA)  # key ring hole
    return img, size


def as_photo(flat, seed):
    h, w = flat.shape[:2]
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    dst = np.float32([[420, 260], [2560, 330], [2700, 2250], [300, 2150]])
    hm = cv2.getPerspectiveTransform(src, dst)
    photo = cv2.warpPerspective(flat, hm, (3000, 2400), borderValue=(90, 80, 70))
    photo = cv2.GaussianBlur(photo, (0, 0), 1.0)
    rng = np.random.default_rng(seed)
    return np.clip(photo.astype(np.int16) + rng.normal(0, 3, photo.shape).astype(np.int16), 0, 255).astype(np.uint8)


def main():
    faelle = [("gelb", (200, 160, 70), 30.0), ("silber", (150, 150, 156), 200.0), ("auto", (150, 150, 156), 95.0)]
    ok = True
    with tempfile.TemporaryDirectory() as tmp:
        for i, (mode, colour, angle) in enumerate(faelle):
            flat, _ = board_image(colour, angle)
            path = Path(tmp) / f"foto-{i}.jpg"
            cv2.imwrite(str(path), cv2.cvtColor(as_photo(flat, i), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 92])
            try:
                r = sb.messen(path, REF, Path(tmp) / f"out-{i}", metall=mode)
            except ValueError as exc:
                print(f"FALL {i} {mode}: FEHLER {exc}"); ok = False; continue
            d_ang = (r["schaft_richtung_grad"] - angle + 180) % 360 - 180
            # Known bias of this edge threshold: widths come out up to ~0.3 mm per side too large
            # (blur/JPEG fringe). Accept -0.2..+0.6 mm on widths; the caliper value always wins.
            def band(v, soll):
                return -0.2 <= v - soll <= 0.6
            checks = {"kopf": band(r["kopf_durchmesser_mm"], 20.6),
                      "schulter": band(r["schulterbreite_mm"], 9.1),
                      "richtung": abs(d_ang) < 1.5,
                      "mitte_quer": abs((r["schulter_quer_min_mm"] + r["schulter_quer_max_mm"]) / 2 - 1.0) < 0.2}
            ok &= all(checks.values())
            print(f"FALL {i} {mode}/{r['metall_modus']}: Kopf {r['kopf_durchmesser_mm']:.2f}  Schulter {r['schulterbreite_mm']:.2f}"
                  f"  Kanten {r['schulter_quer_min_mm']:.2f}/{r['schulter_quer_max_mm']:.2f}  Richtung {r['schaft_richtung_grad']:.2f}"
                  f" (Soll {angle})  -> {'OK' if all(checks.values()) else checks}")
    print("BESTANDEN" if ok else "NICHT BESTANDEN")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
