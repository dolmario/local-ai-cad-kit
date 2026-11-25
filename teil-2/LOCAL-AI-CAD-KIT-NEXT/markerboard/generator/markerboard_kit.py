"""Markerboard v5-KIT (OPUS 17.11.2026): wie v4, aber Wandfuesse mit mehr Luft in der T-Nut:
seitlich Kopf 0,5 / Steg 0,35 / Zunge 0,35 mm je Seite, Kopf 0,2 mm unter der Kammerdecke und 0,2 mm ueber dem Kammerboden.
Platte und alle Markenpositionen unveraendert gegenueber v4 (markerboard.json bleibt fuer die Platte identisch).

Vorher: Markerboard v4 (Waende mit schmaleren Fuessen, Platte unveraendert zu v3): Platte 200 mm, drei Steckwaende mit T-Nut, Eckstoss mit Nut, zwei Farben.

Farben: Grund (Platte, Waende, Ruhezonen der Marken; Farbe waehlt der Nutzer, hell und matt) und Schwarz
(Markenzellen, Kreuze, Massstab als 0,6 mm tiefe Einlagen). Kein Weiss-Koerper: weniger Farbwechsel, kleiner Reinigungsturm.

Ausgabe in ./out/markerboard: je Teil <TEIL>.obj/.mtl, <TEIL>_grund.stl, <TEIL>_schwarz.stl, <TEIL>.3mf,
markerboard.json (3D-Eckpunkte aller Marken, Pruefwerte).
Teile: PLATTE, WAND-LINKS, WAND-HINTEN, WAND-RECHTS. Waende liegend drucken, Markenseite oben.
Marken ID 0..11 auf der Platte (20 mm), 12..17 auf den Waenden (40 mm), 6x6 Zellen, Rand schwarz.
Koordinaten global: Ursprung Plattenecke unten links, z=0 Plattenunterseite, Plattenoberseite z=3.
"""
import json
import zipfile
from pathlib import Path

import cadquery as cq
import cv2
import numpy as np
import trimesh

OUT = Path(__file__).resolve().parent.parent  # schreibt direkt nach local-ai-cad-kit/markerboard
DICT = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
ZEILE = chr(10)

K = 200.0
D = 3.0
H = 110.0
WD = 3.0
WAND_X = 8.0
RAND_HINTEN = K - 8.0
INNEN = 1.5
Y_VORNE = 64.0
Y_HINTEN_INNEN = RAND_HINTEN - INNEN
L_SEITE = Y_HINTEN_INNEN - Y_VORNE
L_HINTEN = (K - WAND_X + INNEN) - (WAND_X - INNEN)

STEG_H = 1.0
KOPF_H = 1.2
NUT_UNTEN = 0.6
Z_KOPF0 = D - STEG_H - KOPF_H
ZUNGE_L = 1.8  # v5-KIT: 0,4 mm Luft am Nutgrund (Nut 2,2 tief)
# Nut in Platte und Rueckwand (Masse wie v3, unveraendert): Kammer 3,4, Steg 1,6, Zungennut 1,6
NUT_KAMMER_B, NUT_STEG_B, NUT_ZUNGE_B = 3.4, 1.6, 1.6
# Fuss und Zunge der Waende (v4 schmaler, je Seite ca. 0,3 mm Luft statt 0,1): Steg 1,0, Kopf 2,6, Zunge 1,0
STEG_B, KOPF_B, ZUNGE_D = 0.9, 2.4, 0.9
# v5-KIT: Fuss-Kopf 1,0 hoch und tiefer gesetzt (Steglaenge 1,2), damit oben 0,2 mm Luft unter der Kammerdecke bleibt
FUSS_STEG_H, FUSS_KOPF_H = 1.2, 1.0
FUSS_RAND = 3.0

EINLAGE_T, MARKE_WAND, MULDE_WAND, ZELLEN = 0.6, 40.0, 50.0, 6
MARKE_PLATTE = 20.0
FARBEN = {"grund": "#F2F2F2", "schwarz": "#101010"}

_pos = ([(24.0, y) for y in (60.0, 95.0, 130.0, 165.0)] + [(K - 24.0, y) for y in (60.0, 95.0, 130.0, 165.0)]
        + [(x, 20.0) for x in (40.0, 80.0, 120.0, 160.0)])
PLATTEN_MARKEN = dict(enumerate(_pos))
WAND_MARKEN = {"links": (12, 13), "hinten": (14, 15), "rechts": (16, 17)}
MARKEN_Y_WAND = (5.0, 5.0 + MULDE_WAND + 2.0)
KREUZ_ARM, KREUZ_B = 5.0, 0.8
KREUZ_X = [50.0 + 20.0 * i for i in range(6)]
KREUZ_Y = [55.0 + 20.0 * i for i in range(7)]
MASSSTAB_Y, MASSSTAB_X0, MASSSTAB_L = 40.0, 50.0, 100.0


def zellen(marker_id):
    return cv2.aruco.generateImageMarker(DICT, marker_id, ZELLEN, borderBits=1)


def zellpunkte(markers):
    """markers: Liste (id, cx, cy, marke); liefert Mittelpunkte der schwarzen Zellen je Zellgroesse."""
    erg = {}
    for mid, cx, cy, marke in markers:
        p = marke / ZELLEN
        bild = zellen(mid)
        x0, y1 = cx - marke / 2, cy + marke / 2
        for r in range(ZELLEN):
            for c in range(ZELLEN):
                if bild[r, c] == 0:
                    erg.setdefault(p, []).append((x0 + (c + 0.5) * p, y1 - (r + 0.5) * p))
    return erg


def einlagen(markers, kreuze=False, extra=0.0):
    """Schwarze Einlagen (Markenzellen, optional Kreuze und Massstab), Hoehe EINLAGE_T + extra."""
    z0 = D - EINLAGE_T
    kleiner = 0.004 if extra > 0 else 0.02
    teile = None
    for p, punkte in zellpunkte(markers).items():
        q = p - kleiner
        k = cq.Workplane("XY").workplane(offset=z0).pushPoints(punkte).rect(q, q).extrude(EINLAGE_T + extra)
        teile = k if teile is None else teile.union(k)
    if kreuze:
        gruppen = [[(x, y, 2 * KREUZ_ARM, KREUZ_B) for x in KREUZ_X for y in KREUZ_Y],
                   [(x, y, KREUZ_B, 2 * KREUZ_ARM) for x in KREUZ_X for y in KREUZ_Y],
                   [(MASSSTAB_X0 + MASSSTAB_L / 2, MASSSTAB_Y, MASSSTAB_L, KREUZ_B)],
                   [(MASSSTAB_X0 + 10.0 * i, MASSSTAB_Y + 1.5, KREUZ_B, 3.0 + KREUZ_B) for i in range(11)]]
        for gruppe in gruppen:
            w = cq.Workplane("XY").workplane(offset=z0)
            for x, y, b, h in gruppe:
                w = w.center(x, y).rect(b, h).center(-x, -y)
            k = w.extrude(EINLAGE_T + extra)
            teile = k if teile is None else teile.union(k)
    return teile


def ecken_lokal(cx, cy, marke):
    h = marke / 2
    return [(cx - h, cy + h), (cx + h, cy + h), (cx + h, cy - h), (cx - h, cy - h)]


def t_nut(achse, c, ende_lo, ende_hi):
    """T-Nut in der Platte; achse 'y': Nut entlang y bei x=c, 'x': entlang x bei y=c."""
    laenge = ende_hi - ende_lo
    mitte = (ende_lo + ende_hi) / 2

    def quader(breite, z0, hoehe):
        w = cq.Workplane("XY").workplane(offset=z0)
        if achse == "y":
            return w.center(c, mitte).rect(breite, laenge).extrude(hoehe)
        return w.center(mitte, c).rect(laenge, breite).extrude(hoehe)

    kammer = quader(NUT_KAMMER_B, NUT_UNTEN, Z_KOPF0 + KOPF_H - NUT_UNTEN)
    steg = quader(NUT_STEG_B, Z_KOPF0 + KOPF_H, STEG_H + 0.01)
    return kammer.union(steg)


def platte():
    k = cq.Workplane("XY").box(K, K, D, centered=(False, False, False))
    seite_hi = Y_HINTEN_INNEN - 2.5
    hinten_hi = (WAND_X - INNEN) + (L_HINTEN - FUSS_RAND) + 0.5
    for ach, c, lo, hi in (("y", WAND_X, -0.01, seite_hi), ("y", K - WAND_X, -0.01, seite_hi), ("x", RAND_HINTEN, -0.01, hinten_hi)):
        k = k.cut(t_nut(ach, c, lo, hi))
    markers = [(i, c[0], c[1], MARKE_PLATTE) for i, c in PLATTEN_MARKEN.items()]
    return k.cut(einlagen(markers, kreuze=True, extra=0.01)), einlagen(markers, kreuze=True)


def fuss(x0, x1):
    kopf = (cq.Workplane("XY").workplane(offset=(WD - KOPF_B) / 2).center((x0 + x1) / 2, -FUSS_STEG_H - FUSS_KOPF_H / 2)
            .rect(x1 - x0, FUSS_KOPF_H).extrude(KOPF_B))
    steg = (cq.Workplane("XY").workplane(offset=(WD - STEG_B) / 2).center((x0 + x1) / 2, -FUSS_STEG_H / 2 + 0.005)
            .rect(x1 - x0, FUSS_STEG_H + 0.01).extrude(STEG_B))
    return kopf.union(steg)


def wand(name):
    laenge = L_HINTEN if name == "hinten" else L_SEITE
    w = cq.Workplane("XY").box(laenge, H, WD, centered=False)
    if name == "hinten":
        w = w.union(fuss(FUSS_RAND, laenge - FUSS_RAND))
        for gx in (WAND_X, K - WAND_X):
            lx = gx - (WAND_X - INNEN)
            tiefe = ZUNGE_L + 0.2
            nut = (cq.Workplane("XY").workplane(offset=WD - tiefe).center(lx, H / 2)
                   .rect(NUT_ZUNGE_B, H + 0.02).extrude(tiefe + 0.01))
            w = w.cut(nut)
    else:
        if name == "links":
            w = w.union(fuss(FUSS_RAND, laenge - FUSS_RAND - 0.5))
            zx0, zx1 = laenge - 0.01, laenge + ZUNGE_L
        else:
            w = w.union(fuss(FUSS_RAND + 0.5, laenge - FUSS_RAND))
            zx0, zx1 = -ZUNGE_L, 0.01
        zunge = (cq.Workplane("XY").workplane(offset=(WD - ZUNGE_D) / 2).center((zx0 + zx1) / 2, H / 2)
                 .rect(zx1 - zx0, H).extrude(ZUNGE_D))
        w = w.union(zunge)
    pts = [(laenge / 2, my + MULDE_WAND / 2) for my in MARKEN_Y_WAND]
    ids = WAND_MARKEN[name]
    markers = [(ids[i], pts[i][0], pts[i][1], MARKE_WAND) for i in range(2)]
    return w.cut(einlagen(markers, extra=0.01)), einlagen(markers), laenge, pts


def nach_global(name):
    if name == "links":
        return np.array([[0, 0, 1, WAND_X - INNEN], [1, 0, 0, Y_VORNE], [0, 1, 0, D], [0, 0, 0, 1]], float)
    if name == "rechts":
        return np.array([[0, 0, -1, K - WAND_X + INNEN], [-1, 0, 0, Y_HINTEN_INNEN], [0, 1, 0, D], [0, 0, 0, 1]], float)
    return np.array([[1, 0, 0, WAND_X - INNEN], [0, 0, -1, RAND_HINTEN + INNEN], [0, 1, 0, D], [0, 0, 0, 1]], float)


def netz(shape, pfad):
    cq.exporters.export(shape, str(pfad))
    return trimesh.load(str(pfad))


def schreibe_3mf(pfad, teile):
    mats = "".join(f'<base name="{n}" displaycolor="{c}FF"/>' for n, c in FARBEN.items())
    objs, items = [], []
    for i, (farbe, m) in enumerate(teile, start=2):
        v = "".join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in m.vertices)
        t = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in m.faces)
        objs.append(f'<object id="{i}" name="{farbe}" type="model" pid="1" pindex="{list(FARBEN).index(farbe)}">'
                    f'<mesh><vertices>{v}</vertices><triangles>{t}</triangles></mesh></object>')
        items.append(f'<item objectid="{i}"/>')
    modell = ('<?xml version="1.0" encoding="UTF-8"?><model unit="millimeter" xml:lang="en-US" '
              'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"><resources>'
              f'<basematerials id="1">{mats}</basematerials>{"".join(objs)}</resources>'
              f'<build>{"".join(items)}</build></model>')
    with zipfile.ZipFile(pfad, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml",
                   '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                   '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
        z.writestr("_rels/.rels",
                   '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
        z.writestr("3D/3dmodel.model", modell)


def schreibe_obj(pfad, teile):
    """Eine OBJ mit Material je Farbe; Lage bleibt erhalten, MTL daneben."""
    mtl = pfad.with_suffix(".mtl")
    zeilen = []
    for n, c in FARBEN.items():
        r, g, b = (int(c[i:i + 2], 16) / 255 for i in (1, 3, 5))
        zeilen += [f"newmtl {n}", f"Kd {r:.3f} {g:.3f} {b:.3f}", "Ka 0 0 0", "Ks 0 0 0", "d 1", ""]
    mtl.write_text(ZEILE.join(zeilen), encoding="utf-8")
    zeilen = [f"mtllib {mtl.name}"]
    off = 1
    for farbe, m in teile:
        zeilen += [f"o {farbe}", f"usemtl {farbe}"]
        zeilen += [f"v {x:.4f} {y:.4f} {z:.4f}" for x, y, z in m.vertices]
        zeilen += [f"f {a + off} {b + off} {c + off}" for a, b, c in m.faces]
        off += len(m.vertices)
    pfad.write_text(ZEILE.join(zeilen) + ZEILE, encoding="utf-8")


def teil_schreiben(name, grund, schwarz):
    teile = [("grund", netz(grund, OUT / f"{name}_grund.stl")), ("schwarz", netz(schwarz, OUT / f"{name}_schwarz.stl"))]
    schreibe_3mf(OUT / f"{name}.3mf", teile)
    schreibe_obj(OUT / f"{name}.obj", teile)
    return {f: {"wasserdicht": bool(m.is_watertight), "volumen_mm3": round(float(m.volume), 1),
                "grenzen_mm": [round(float(v), 2) for v in m.extents]} for f, m in teile}


def volumen_schnitt(a, b):
    try:
        return round(float(a.intersect(b).Volume()), 3)
    except Exception as e:
        return f"Fehler: {e}"


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    info = {"einheit": "mm", "platte_mm": [K, K, D], "farben": list(FARBEN), "marker_3d": {}, "teile": {}, "kollision_mm3": {},
            "hinweis": "Markerebene = Plattenoberseite bzw. Wandflaeche (Einlage buendig); Ecken tl,tr,br,bl aus Sicht von oben bzw. innen; Marke = schwarzer Rand ohne Ruhezone-Streifen"}
    p, ps = platte()
    info["teile"]["PLATTE"] = teil_schreiben("PLATTE", p, ps)
    for mid, (cx, cy) in PLATTEN_MARKEN.items():
        info["marker_3d"][str(mid)] = {"teil": "PLATTE", "ecken_mm": [[x, y, D] for x, y in ecken_lokal(cx, cy, MARKE_PLATTE)]}
    welt = {"PLATTE": p.val()}
    for name in ("links", "hinten", "rechts"):
        w, sw, laenge, pts = wand(name)
        tn = f"WAND-{name.upper()}"
        info["teile"][tn] = teil_schreiben(tn, w, sw)
        m = nach_global(name)
        for i, mid in enumerate(WAND_MARKEN[name]):
            ecken = [m @ np.array([x, y, D, 1.0]) for x, y in ecken_lokal(*pts[i], MARKE_WAND)]
            info["marker_3d"][str(mid)] = {"teil": tn, "ecken_mm": [[round(float(v), 3) for v in e[:3]] for e in ecken]}
        pl = cq.Plane(origin=tuple(float(v) for v in m[:3, 3]), xDir=tuple(float(v) for v in m[:3, 0]),
                      normal=tuple(float(v) for v in m[:3, 2]))
        welt[tn] = w.val().moved(cq.Location(pl))
    namen = list(welt)
    for i, a in enumerate(namen):
        for b in namen[i + 1:]:
            info["kollision_mm3"][f"{a} / {b}"] = volumen_schnitt(welt[a], welt[b])
    info["luft_pruefung_mm3"] = {}
    for tn in [n for n in namen if n != "PLATTE"]:
        for name_v, (dx, dy, dz) in {"quer+0.30": (0.30, 0, 0), "quer-0.30": (-0.30, 0, 0), "laengs_quer+0.30": (0, 0.30, 0),
                                     "laengs_quer-0.30": (0, -0.30, 0), "hoch+0.15": (0, 0, 0.15)}.items():
            moved = welt[tn].moved(cq.Location(cq.Vector(dx, dy, dz)))
            info["luft_pruefung_mm3"][f"{tn} {name_v}"] = volumen_schnitt(welt["PLATTE"], moved)
    (OUT / "markerboard.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
    print(json.dumps({"teile": {k: {f: (v["wasserdicht"], v["grenzen_mm"]) for f, v in t.items()} for k, t in info["teile"].items()},
                      "kollision_mm3": info["kollision_mm3"]}))
