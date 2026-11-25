"""CPU registration of phone photos against the paper sheet or markerboard v3."""
import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

HERE = Path(__file__).resolve().parent


def referenz_laden(path):
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if "marker_3d" in data:
        markers = {int(k): np.array(v["ecken_mm"], np.float32)[:, :2]
                   for k, v in data["marker_3d"].items() if v["teil"] == "PLATTE"}
        size = data["platte_mm"][:2]
        return markers, size, "x rechts, y nach oben; Plattenoberseite z=3 mm"
    edge = data["markenkante_mm"]
    markers = {int(k): np.array([(x, y), (x + edge, y),
                                (x + edge, y + edge), (x, y + edge)], np.float32)
               for k, (x, y) in data["blatt_marken_oben_links"].items()}
    return markers, [210, 297], data["ursprung"]


def erkennen(gray, known):
    params = cv2.aruco.DetectorParameters()
    params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
    detector = cv2.aruco.ArucoDetector(
        cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50), params)
    found = {}
    scales = sorted({1.0, min(1.0, 2000 / max(gray.shape)),
                     min(1.0, 1400 / max(gray.shape))}, reverse=True)
    duplicates = set()
    for scale in scales:
        small = cv2.resize(gray, None, fx=scale, fy=scale,
                           interpolation=cv2.INTER_AREA) if scale < 1 else gray
        corners, ids, _ = detector.detectMarkers(small)
        if ids is None:
            continue
        seen = set()
        for corner, mid in zip(corners, ids.flatten()):
            mid = int(mid)
            if mid not in known:
                continue
            if mid in seen:
                duplicates.add(mid)
            seen.add(mid)
            if mid not in found:
                points = (corner / scale).astype(np.float32).reshape(4, 1, 2)
                cv2.cornerSubPix(gray, points, (5, 5), (-1, -1),
                                 (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, .01))
                found[mid] = points.reshape(4, 2)
    if duplicates:
        raise ValueError(f"Marken-ID mehrfach im Bild: {sorted(duplicates)}. Nur eine Schablone verwenden.")
    if len(found) < 4:
        raise ValueError(f"Nur {len(found)} Bodenmarken erkannt ({sorted(found)}). Mindestens vier gut verteilte Marken fotografieren.")
    return found


def registrieren(gray, known, max_error=.5):
    found = erkennen(gray, known)
    ids = sorted(found)
    pixels = np.concatenate([found[i] for i in ids]).astype(np.float32)
    world = np.concatenate([known[i] for i in ids]).astype(np.float32)
    hull_area = cv2.contourArea(cv2.convexHull(world))
    reference_area = cv2.contourArea(cv2.convexHull(np.concatenate(list(known.values()))))
    coverage = hull_area / reference_area
    if coverage < .25:
        raise ValueError("Marken liegen zu eng beieinander. Marken an mehreren Seiten sichtbar lassen.")
    matrix, inliers = cv2.findHomography(pixels, world, cv2.RANSAC, max_error)
    if matrix is None or inliers is None or int(inliers.sum()) < 12:
        raise ValueError("Keine stabile Entzerrung. Unterlage flach legen und neu fotografieren.")
    projected = cv2.perspectiveTransform(pixels.reshape(-1, 1, 2), matrix).reshape(-1, 2)
    errors = np.linalg.norm(projected - world, axis=1)
    per_marker = {str(mid): {"mittel_mm": float(errors[n*4:n*4+4].mean()),
                             "maximum_mm": float(errors[n*4:n*4+4].max()),
                             "inlier_ecken": int(inliers[n*4:n*4+4].sum())}
                  for n, mid in enumerate(ids)}
    # All observed corners count: RANSAC must not hide a warped reference.
    if float(errors.max()) > max_error:
        raise ValueError(f"Markenabweichung {errors.max():.3f} mm überschreitet {max_error:.3f} mm. Unterlage und Druck prüfen.")
    return matrix, {"ids": ids, "restfehler_mittel_mm": float(errors.mean()),
                    "restfehler_maximum_mm": float(errors.max()),
                    "je_marke": per_marker, "referenzabdeckung": coverage}


def foto_masse(photo, reference, output, roi=None, max_error=.5):
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError("Ausgabeordner ist nicht leer. Einen neuen Laufordner verwenden.")
    with Image.open(photo) as source:
        rgb = np.asarray(ImageOps.exif_transpose(source).convert("RGB"))
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    known, size, axes = referenz_laden(reference)
    matrix, quality = registrieren(gray, known, max_error)
    s = 10.0
    flip = "markerboard" if "nach oben" in axes else "blatt"
    target = np.array([[s, 0, 0], [0, -s, size[1]*s], [0, 0, 1]]) if flip == "markerboard" else np.diag([s, s, 1])
    rectified = cv2.warpPerspective(rgb, target @ matrix,
                                    (round(size[0]*s), round(size[1]*s)),
                                    borderValue=(255, 255, 255))
    result = {"status": "registriert", "einheit": "mm", "achsen": axes,
              "foto_sha256": hashlib.sha256(Path(photo).read_bytes()).hexdigest(),
              "referenz_sha256": hashlib.sha256(Path(reference).read_bytes()).hexdigest(),
              "marken": quality, "bild_zu_mm": matrix.tolist(),
              "warnungen": ["Keine Kamerakalibrierung: Objektivverzeichnung ungeprüft.",
                            "Markenrestfehler ist keine zugesicherte Messgenauigkeit am Teil.",
                            "Teilhöhe und Parallaxe ungeprüft; Messschieber hat Vorrang."],
              "teil": None}
    if roi is not None:
        x0, y0, x1, y1 = map(float, roi)
        if not (0 <= x0 < x1 <= size[0] and 0 <= y0 < y1 <= size[1]):
            raise ValueError("Messbereich liegt außerhalb der Referenzfläche.")
        for points in known.values():
            if (points[:, 0].min() < x1 and points[:, 0].max() > x0
                    and points[:, 1].min() < y1 and points[:, 1].max() > y0):
                raise ValueError("Messbereich enthält eine Referenzmarke. Bereich enger wählen.")
        a, b = (size[1]-y1, size[1]-y0) if flip == "markerboard" else (y0, y1)
        crop = rectified[round(a*s):round(b*s), round(x0*s):round(x1*s)]
        g = cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY)
        _, mask = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
        contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        choices = [] if hierarchy is None else [i for i, c in enumerate(contours)
                    if hierarchy[0][i][3] == -1 and cv2.contourArea(c) / s**2 > 2]
        if len(choices) != 1:
            raise ValueError(f"{len(choices)} mögliche Teile im Messbereich. Ein Teil auf hellem mattem Grund isolieren.")
        index = choices[0]
        contour = contours[index]
        coords = contour.reshape(-1, 2)
        if (coords.min(axis=0) <= 1).any() or (coords.max(axis=0) >= np.array([crop.shape[1]-2, crop.shape[0]-2])).any():
            raise ValueError("Teil berührt Messbereichsrand. Bereich erweitern.")
        _, dims, _ = cv2.minAreaRect(contour)
        result["teil"] = {"box_mm": sorted(float(d/s) for d in dims),
                          "flaeche_mm2": float(cv2.contourArea(contour)/s**2),
                          "unsicherheit_mm": None,
                          "unsicherheit_status": "ohne Kalibrierung und Prüfkörper nicht bestimmt"}
        result["warnungen"].append("Helligkeitssegmentierung: Schatten, Kreuze und Skala können die Kontur verfälschen; Bohrungen noch nicht vermessen.")
    output.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rectified).save(output / "entzerrt-lokal.png")
    (output / "masse.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("foto")
    parser.add_argument("--referenz", required=True)
    parser.add_argument("--ausgabe", required=True)
    parser.add_argument("--roi", nargs=4, type=float, metavar=("X0", "Y0", "X1", "Y1"))
    parser.add_argument("--max-fehler-mm", type=float, default=.5)
    parser.add_argument("--schluessel", action="store_true", help="Schulterbreite und Schaftrichtung im Farbkontrastmodus messen")
    args = parser.parse_args()
    try:
        if not 0 < args.max_fehler_mm <= 2:
            raise ValueError("Fehlergrenze muss zwischen 0 und 2 mm liegen.")
        if args.schluessel:
            from schluessel_bild import messen
            result = messen(args.foto, args.referenz, args.ausgabe, max_error=args.max_fehler_mm)
        else:
            result = foto_masse(args.foto, args.referenz, args.ausgabe, args.roi, args.max_fehler_mm)
        print(json.dumps({"status": result["status"], "ausgabe": args.ausgabe}, ensure_ascii=False))
    except Exception as exc:
        print(json.dumps({"status": "fehler", "meldung": str(exc),
                          "hinweis": "Foto, Referenz und freien Ausgabeordner prüfen."}, ensure_ascii=False))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
