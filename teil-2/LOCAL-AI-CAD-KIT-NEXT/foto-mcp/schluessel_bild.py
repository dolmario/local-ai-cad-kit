"""Key head diameter, shoulder width and shaft direction from a photo on the printed markerboard.

Based on the measuring code used in our video. Added for the kit: a mode for silver/nickel keys
(darker than the light board) next to the original mode for brass/yellow keys.
All values are photo estimates. The caliper always wins.
"""
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

import foto_masse as fm

SCALE = 10  # pixels per mm in the rectified image


def kontur_messen(mask, px_mm=SCALE):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    choices = [c for c in contours if 100 < cv2.contourArea(c) / px_mm**2 < 1800]
    if len(choices) > 1:
        valid = []
        for candidate in choices:
            isolated = np.zeros_like(mask)
            cv2.drawContours(isolated, [candidate], -1, 255, -1)
            try:
                valid.append(kontur_messen(isolated, px_mm))
            except ValueError:
                pass
        if len(valid) == 1:
            return valid[0]
        raise ValueError(f"{len(valid)} plausible keys found. Put exactly one key in the middle of the board.")
    if len(choices) != 1:
        raise ValueError(f"{len(choices)} possible keys found. Check light, shadows and contrast.")
    contour = choices[0]
    solid = np.zeros_like(mask)
    cv2.drawContours(solid, [contour], -1, 255, -1)
    distance = cv2.distanceTransform(solid, cv2.DIST_L2, cv2.DIST_MASK_PRECISE)
    _, radius, _, centre = cv2.minMaxLoc(distance)
    centre = np.array(centre, dtype=float)
    points = contour[:, 0, :].astype(float)
    if not 6 < radius / px_mm < 18:
        raise ValueError("No plausible round key head found (head diameter 12 to 36 mm expected).")
    far = points[np.linalg.norm(points - centre, axis=1) > radius * 1.7]
    if len(far) < 10:
        raise ValueError("The shaft is not visible enough.")
    axis = far.mean(0) - centre
    axis /= np.linalg.norm(axis)
    for _ in range(3):
        delta = points - centre
        use = (delta @ axis < radius * .35) & (np.linalg.norm(delta, axis=1) < radius * 1.45)
        arc = points[use]
        if len(arc) < 30:
            raise ValueError("Too little of the head circle is visible.")
        rng = np.random.default_rng(1234)
        best = None
        for _trial in range(200):
            sample = arc[rng.choice(len(arc), 3, replace=False)]
            a = np.c_[2 * sample, np.ones(3)]
            if np.linalg.cond(a) > 1e8:
                continue
            fit = np.linalg.solve(a, (sample**2).sum(1))
            r2 = fit[2] + fit[:2] @ fit[:2]
            if not (6 * px_mm)**2 < r2 < (18 * px_mm)**2:
                continue
            residual = np.abs(np.linalg.norm(arc - fit[:2], axis=1) - np.sqrt(r2))
            inliers = residual < .35 * px_mm
            if best is None or inliers.sum() > best.sum():
                best = inliers
        if best is None or best.mean() < .55:
            raise ValueError("Head circle not robustly identifiable (round head expected).")
        arc = arc[best]
        coef = np.linalg.lstsq(np.c_[2 * arc, np.ones(len(arc))], (arc**2).sum(1), rcond=None)[0]
        centre = coef[:2]
        radius = np.sqrt(coef[2] + centre @ centre)
        far = points[np.linalg.norm(points - centre, axis=1) > radius * 1.7]
        axis = far.mean(0) - centre
        axis /= np.linalg.norm(axis)
    normal = np.array([-axis[1], axis[0]])
    ys, xs = np.nonzero(solid)
    delta = np.c_[xs, ys] - centre
    along, across = delta @ axis / px_mm, delta @ normal / px_mm
    widths, edges = [], []
    for t in np.arange(radius / px_mm + .5, radius / px_mm + 3, .25):
        section = across[np.abs(along - t) < .2]
        if len(section) > 5:
            widths.append(float(np.ptp(section)))
            edges.append((float(section.min()), float(section.max())))
    if len(widths) < 5:
        raise ValueError("Shoulder next to the head cannot be measured completely.")
    width = float(np.percentile(widths, 90))
    if not 2 < width < radius / px_mm * 1.4:
        raise ValueError("Shoulder contour implausible.")
    residual = np.abs(np.linalg.norm(arc - centre, axis=1) - radius) / px_mm
    if np.percentile(residual, 90) > .8:
        raise ValueError("Head circle too irregular; check edge, reflections and shadow.")
    lo = float(np.percentile([e[0] for e in edges], 10))
    hi = float(np.percentile([e[1] for e in edges], 90))
    return {"kopf_mitte_px": centre.tolist(), "kopf_radius_px": float(radius),
            "kopf_durchmesser_mm": float(2 * radius / px_mm),
            "schulterbreite_mm": width,
            # Image y points down: flip sign so the angle is counter-clockwise from +X on the board.
            "schulter_quer_min_mm": -hi, "schulter_quer_max_mm": -lo,
            "schaft_richtung_grad": float(np.degrees(np.arctan2(-axis[1], axis[0])) % 360),
            "kreis_p90_rest_mm": float(np.percentile(residual, 90)),
            "messdefinition": ("shoulder width = 90th percentile of the cross-section width 0.5 to 3 mm outside the head circle; "
                               "schulter_quer_min/max = shoulder edges across the shaft axis through the head centre, "
                               "positive = left side when looking from the head along the shaft"),
            "kontur": contour, "maske": solid}


def _marken_ausblenden(mask, known, size_y, rand_mm=3.0):
    for pts in known.values():
        x0, y0 = pts.min(0) - rand_mm
        x1, y1 = pts.max(0) + rand_mm
        a, b = size_y - y1, size_y - y0
        mask[max(0, round(a * SCALE)):round(b * SCALE), max(0, round(x0 * SCALE)):round(x1 * SCALE)] = 0
    return mask


def masken(rectified, known, size, metall):
    """Candidate masks (three thresholds each) for the requested key colour."""
    out = []
    if metall in ("gelb", "auto"):
        hsv = cv2.cvtColor(rectified, cv2.COLOR_RGB2HSV)
        group = []
        for saturation in (35, 40, 45):
            m = cv2.inRange(hsv, (8, saturation, 35), (48, 255, 255))
            group.append(m)
        out.append(("gelb", group))
    if metall in ("silber", "auto"):
        gray = cv2.cvtColor(rectified, cv2.COLOR_RGB2GRAY)
        # Board background: a large grey-level closing removes everything darker that is smaller than ~40 mm.
        background = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (401, 401)))
        diff = _marken_ausblenden(cv2.subtract(background, gray), known, size[1])
        # Otsu only on the board area without markers, otherwise the black markers dominate the threshold.
        otsu, _ = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        group = []
        for factor in (0.85, 1.0, 1.15):
            _, m = cv2.threshold(diff, max(12, otsu * factor), 255, cv2.THRESH_BINARY)
            group.append(m)
        out.append(("silber", group))
    cleaned = []
    for name, group in out:
        g2 = []
        for m in group:
            m = _marken_ausblenden(m.copy(), known, size[1])
            m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
            m = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
            g2.append(m)
        cleaned.append((name, g2))
    return cleaned


def messen(foto, referenz, ausgabe, metall="auto", max_error=.5):
    ausgabe = Path(ausgabe)
    ausgabe.mkdir(parents=True, exist_ok=True)
    with Image.open(foto) as image:
        rgb = np.asarray(ImageOps.exif_transpose(image).convert("RGB"))
    known, size, axes = fm.referenz_laden(referenz)
    matrix, quality = fm.registrieren(cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY), known, max_error)
    if "nach oben" not in axes:
        raise ValueError("This mode needs the printed markerboard.")
    target = np.array([[SCALE, 0, 0], [0, -SCALE, size[1] * SCALE], [0, 0, 1]])
    rectified = cv2.warpPerspective(rgb, target @ matrix, (round(size[0] * SCALE), round(size[1] * SCALE)),
                                    borderValue=(255, 255, 255))
    fehler = []
    for name, group in masken(rectified, known, size, metall):
        try:
            candidates = [kontur_messen(m) for m in group]
        except ValueError as exc:
            fehler.append(f"{name}: {exc}")
            continue
        widths = [r["schulterbreite_mm"] for r in candidates]
        angles = np.unwrap(np.radians([r["schaft_richtung_grad"] for r in candidates]))
        if np.ptp(widths) > .5 or np.degrees(np.ptp(angles)) > 5:
            fehler.append(f"{name}: unstable, widths {np.round(widths, 2).tolist()}")
            continue
        result = candidates[1]
        result["metall_modus"] = name
        result["segmentierungs_breiten_mm"] = widths
        break
    else:
        raise ValueError("No stable measurement. " + " | ".join(fehler))
    contour = result.pop("kontur")
    mask = result.pop("maske")
    for other in candidates:
        other.pop("kontur", None); other.pop("maske", None)
    overlay = rectified.copy()
    cv2.drawContours(overlay, [contour], -1, (0, 170, 255), 2)
    centre = np.array(result["kopf_mitte_px"])
    angle = np.radians(result["schaft_richtung_grad"])
    end = centre + 230 * np.array([np.cos(angle), -np.sin(angle)])
    cv2.circle(overlay, tuple(centre.astype(int)), round(result["kopf_radius_px"]), (0, 200, 0), 2)
    cv2.arrowedLine(overlay, tuple(centre.astype(int)), tuple(end.astype(int)), (220, 40, 40), 3)
    result.update({"foto_sha256": hashlib.sha256(Path(foto).read_bytes()).hexdigest(),
                   "marken": {k: quality[k] for k in ("ids", "restfehler_mittel_mm", "restfehler_maximum_mm", "referenzabdeckung")},
                   "einheit": "mm", "koordinaten": "board: X right, Y up; angle counter-clockwise from +X",
                   "status": "photo_measurement_stable", "caliper_confirmed": False,
                   "kontrollbild": str((ausgabe / "kontrolle.png").resolve()),
                   "warnungen": ["Photo estimate. Measure head diameter, thickness and shoulder width with a caliper.",
                                 "Lens distortion, shadows and parallax are not calibrated."]})
    Image.fromarray(overlay).save(ausgabe / "kontrolle.png")
    Image.fromarray(mask).save(ausgabe / "maske.png")
    (ausgabe / "masse.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result
