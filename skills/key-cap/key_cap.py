"""Parametric TPU key cap for FreeCAD (run inside FreeCAD through the freecad MCP tool execute_code).

Usage inside execute_code:
    exec(open(r"<kit>/skills/key-cap/key_cap.py", encoding="utf-8").read())
    cap = build_key_cap(doc_name="Cap_" + time.strftime("%H%M%S"), head_d=20.9, head_t=1.8,
                        shoulder_lo=-3.76, shoulder_hi=5.76, shaft_angle_deg=90.28, out_dir=r"<kit>/output")
    print(check_key_cap(cap))

Geometry (all derived from the caliper values; these numbers fitted on our printed TPU 95A cap):
    groove diameter = head_d + 0.3         lip opening = head_d - 2.0
    groove height   = head_t + 0.3         wall = 1.5, lip thickness = 1.0
    shaft passage   = shoulder edges -/+ 0.15 mm, in the groove height only (lips stay closed all round)
shoulder_lo / shoulder_hi: edges of the shoulder next to the head, measured ACROSS the shaft, mm, from the shaft axis
through the head centre. Positive = counter-clockwise from the shaft direction rotated by -90 deg (see measure_key output).
shaft_angle_deg: shaft direction, counter-clockwise from +X.
"""
import math
import os
import time

import FreeCAD
import Part
from FreeCAD import Vector as V


def build_key_cap(doc_name, head_d, head_t, shoulder_lo, shoulder_hi, shaft_angle_deg,
                  clear_groove_d=0.3, clear_groove_h=0.3, lip_reduction=2.0, wall=1.5, lip_t=1.0,
                  passage_extra=0.15, out_dir=None, name="Cap"):
    r_groove = (head_d + clear_groove_d) / 2
    r_lip = (head_d - lip_reduction) / 2
    r_out = r_groove + wall
    groove_h = head_t + clear_groove_h
    height = 2 * lip_t + groove_h
    if r_lip <= 2 or shoulder_hi <= shoulder_lo:
        raise ValueError("Check head_d and the shoulder edges (hi must be larger than lo).")
    doc = FreeCAD.newDocument(doc_name)          # FreeCAD renames duplicates silently: use a unique name
    body = Part.makeCylinder(r_out, height).cut(Part.makeCylinder(r_lip, height))
    body = body.cut(Part.makeCylinder(r_groove, groove_h, V(0, 0, lip_t)))
    q_lo, q_hi = shoulder_lo - passage_extra, shoulder_hi + passage_extra
    passage = Part.makeBox(q_hi - q_lo, r_out + 2, groove_h, V(q_lo, 0, lip_t))   # local +y = shaft direction
    passage.rotate(V(0, 0, 0), V(0, 0, 1), shaft_angle_deg - 90.0)
    shape = body.cut(passage)
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape
    doc.recompute()
    obj.Label = name
    obj_params = dict(head_d=head_d, head_t=head_t, shoulder_lo=shoulder_lo, shoulder_hi=shoulder_hi,
                      shaft_angle_deg=shaft_angle_deg, r_out=r_out, r_groove=r_groove, r_lip=r_lip,
                      lip_t=lip_t, groove_h=groove_h, height=height, q_lo=q_lo, q_hi=q_hi)
    obj.addProperty("App::PropertyString", "CapParams", "Cap", "build parameters").CapParams = repr(obj_params)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        stem = os.path.join(out_dir, "cap_" + time.strftime("%Y%m%d-%H%M%S"))
        Part.export([obj], stem + ".step")
        import MeshPart
        mesh = MeshPart.meshFromShape(Shape=obj.Shape, LinearDeflection=0.01, AngularDeflection=0.05)
        mesh.write(stem + ".stl")
        obj_params["files"] = [stem + ".step", stem + ".stl"]
        print("exported", stem + ".step", stem + ".stl")
    return obj


def check_key_cap(obj):
    """Independent self-check with probe points. Returns a dict; 'ok' is True only if every check passed."""
    p = eval(obj.CapParams)
    s = obj.Shape
    th = math.radians(p["shaft_angle_deg"])
    u = (math.cos(th), math.sin(th))             # shaft direction
    w = (math.sin(th), -math.cos(th))            # across, positive = shoulder_hi side

    def inside(x, y, z):
        return s.isInside(V(x, y, z), 1e-6, True)

    res = {"valid": s.isValid(), "solids": len(s.Solids)}
    # 1) lips closed all round (also over the passage): material at z in the middle of each lip
    bad = 0
    for az in range(0, 360, 2):
        for z in (p["lip_t"] / 2, p["height"] - p["lip_t"] / 2):
            for r in (p["r_lip"] + 0.3, (p["r_lip"] + p["r_out"]) / 2):
                if not inside(r * math.cos(math.radians(az)), r * math.sin(math.radians(az)), z):
                    bad += 1
    res["lips_closed"] = bad == 0
    # 2) head space free: ring between lip and groove wall, mid groove height
    zmid = p["lip_t"] + p["groove_h"] / 2
    bad = sum(1 for az in range(0, 360, 4) for r in (p["r_lip"] + 0.2, p["r_groove"] - 0.2)
              if inside(r * math.cos(math.radians(az)), r * math.sin(math.radians(az)), zmid))
    res["groove_free"] = bad == 0
    # 3) passage free over the whole shoulder width (with 0.05 mm margin), through the wall to the outside
    bad = 0
    for q in [p["q_lo"] + 0.05 + (p["q_hi"] - p["q_lo"] - 0.1) * i / 14 for i in range(15)]:
        for a in [p["r_groove"] - 0.3 + 0.25 * i for i in range(int((p["r_out"] - p["r_groove"] + 0.8) / 0.25))]:
            for z in (p["lip_t"] + 0.05, zmid, p["lip_t"] + p["groove_h"] - 0.05):
                if inside(a * u[0] + q * w[0], a * u[1] + q * w[1], z):
                    bad += 1
    res["passage_free"] = bad == 0
    # 4) wall opposite the passage is closed in groove height
    opp = th + math.pi
    r_mid = (p["r_groove"] + p["r_out"]) / 2
    res["back_wall_closed"] = bool(inside(r_mid * math.cos(opp), r_mid * math.sin(opp), zmid))
    # 5) size
    bb = s.BoundBox
    res["size_xyz"] = [round(bb.XLength, 3), round(bb.YLength, 3), round(bb.ZLength, 3)]
    res["size_ok"] = abs(bb.ZLength - p["height"]) < 1e-3 and abs(bb.XLength - 2 * p["r_out"]) < 0.3
    res["volume_mm3"] = round(s.Volume, 3)
    res["ok"] = all(res[k] for k in ("valid", "lips_closed", "groove_free", "passage_free", "back_wall_closed", "size_ok")) and res["solids"] == 1
    return res
