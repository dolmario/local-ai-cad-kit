"""Helpers for execute_code in FreeCAD. Load with:
    exec(open(os.environ["LOCAL_AI_CAD_KIT"] + "/skills/drawing-to-part/cad_helpers.py", encoding="utf-8").read())
(the starter passes the kit and output paths through environment variables)

KIT                      absolute kit path (forward slashes)
export_part(obj, name)   write STEP + STL to CAD_EVAL_OUTPUT and print size + validity
profile_solid(pts, h, ...)  extrude a closed 2D profile (list of points, optional arcs) by h along Z
bbox_info(shape)         print + return size, min/max, valid, solids, volume (use it instead of BoundBox attributes)
l_bracket(...)           bent plate (base + wall) with a real inner/outer bend radius, as ONE solid, no fillet needed
cyl_cut(shape, d, centre, axis, length)   cut a through hole / bore, returns the new shape
"""
import os
import FreeCAD as App
import Part
import MeshPart

KIT = os.environ.get("LOCAL_AI_CAD_KIT")
if not KIT:
    from pathlib import Path
    for candidate in (Path.cwd(), *Path.cwd().parents):
        if (candidate / "skills/drawing-to-part/cad_helpers.py").is_file():
            KIT = candidate.as_posix()
            break
if not KIT:
    raise RuntimeError("Set LOCAL_AI_CAD_KIT or launch FreeCAD from the CAD workspace")
OUT = os.environ.get("CAD_EVAL_OUTPUT", KIT + "/output")


def export_part(obj, name):
    """Export a FreeCAD object to STEP and STL in the kit output folder. Prints what it wrote."""
    os.makedirs(OUT, exist_ok=True)
    shape = obj.Shape
    step, stl = "%s/%s.step" % (OUT, name), "%s/%s.stl" % (OUT, name)
    Part.export([obj], step)
    MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.05, AngularDeflection=0.1).write(stl)
    bb = shape.BoundBox
    print("valid", shape.isValid(), "solids", len(shape.Solids), "size", round(bb.XLength, 3), round(bb.YLength, 3), round(bb.ZLength, 3))
    print("STEP", step, os.path.getsize(step), "bytes")
    print("STL ", stl, os.path.getsize(stl), "bytes")
    return step, stl


def bbox_info(shape):
    """Print and return the bounding box. FreeCAD attribute names are XMin XMax YMin YMax ZMin ZMax XLength YLength ZLength
    (there is no BoundingBox, Xmax or Min). Works on solids and compounds."""
    bb = shape.BoundBox
    d = {"xmin": round(bb.XMin, 3), "xmax": round(bb.XMax, 3), "ymin": round(bb.YMin, 3), "ymax": round(bb.YMax, 3),
         "zmin": round(bb.ZMin, 3), "zmax": round(bb.ZMax, 3),
         "size": (round(bb.XLength, 3), round(bb.YLength, 3), round(bb.ZLength, 3))}
    print("bbox", d, "valid", shape.isValid(), "solids", len(shape.Solids), "volume", round(shape.Volume, 2))
    return d


def cyl_cut(shape, d, centre, axis, length=1000.0):
    """Cut a cylinder of diameter d through shape. centre = point on the axis (x, y, z), axis = (ax, ay, az)."""
    ax = App.Vector(*axis)
    ax.normalize()
    start = App.Vector(*centre) - ax * (length / 2)
    return shape.cut(Part.makeCylinder(d / 2.0, length, start, ax))


def l_bracket(thickness, inner_r, base_len, wall_h, width):
    """Bent plate: a flat base (X from 0 to base_len, Z 0..thickness) and a vertical wall at X = 0..thickness going up to Z = wall_h.
    base_len and wall_h are OUTER sizes measured from the outer corner (X=0, Z=0). Width along Y (0..width).
    The bend is a real arc (inner radius inner_r, outer radius inner_r + thickness), built as a profile - no fillet call.
    Returns a single Part solid."""
    t, r = float(thickness), float(inner_r)
    R = r + t
    V = App.Vector
    # outer corner arc centre at (R, R); inner arc centre at (R, R)
    pts = []
    e = []
    # start at outer bottom (R, 0) -> along bottom to (base_len, 0) -> up to (base_len, t) -> back along base top to (R, t)
    e.append(Part.LineSegment(V(R, 0, 0), V(base_len, 0, 0)))
    e.append(Part.LineSegment(V(base_len, 0, 0), V(base_len, t, 0)))
    e.append(Part.LineSegment(V(base_len, t, 0), V(R, t, 0)))
    # inner arc from (R, t) to (t, R), centre (R, R)  (concave side)
    c = V(R, R, 0)
    mid_in = V(R - r * 0.70710678, R - r * 0.70710678, 0)
    e.append(Part.Arc(V(R, t, 0), mid_in, V(t, R, 0)))
    e.append(Part.LineSegment(V(t, R, 0), V(t, wall_h, 0)))
    e.append(Part.LineSegment(V(t, wall_h, 0), V(0, wall_h, 0)))
    e.append(Part.LineSegment(V(0, wall_h, 0), V(0, R, 0)))
    mid_out = V(R - R * 0.70710678, R - R * 0.70710678, 0)
    e.append(Part.Arc(V(0, R, 0), mid_out, V(R, 0, 0)))
    wire = Part.Wire([x.toShape() for x in e])
    face = Part.Face(wire)
    # profile is in the XY plane (X = along base, Y = height). Extrude along Z (width), caller maps axes as needed.
    return face.extrude(V(0, 0, width))


def profile_solid(points, height, arcs=None):
    """Extrude a closed polygon (list of (x, y)) by height along Z. Returns a Part solid."""
    V = App.Vector
    p = [V(x, y, 0) for x, y in points]
    p.append(p[0])
    return Part.Face(Part.makePolygon(p)).extrude(V(0, 0, height))
