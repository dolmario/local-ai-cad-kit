"""part_report(shape): size, volume and every cylinder face (hole or round) of a FreeCAD shape. Run via execute_code."""
import FreeCAD


def part_report(shape):
    bb = shape.BoundBox
    holes = {}
    for f in shape.Faces:
        if type(f.Surface).__name__ != "Cylinder":
            continue
        c = f.Surface
        u0, u1, v0, v1 = f.ParameterRange
        um, vm = (u0 + u1) / 2, (v0 + v1) / 2
        p, n = f.valueAt(um, vm), f.normalAt(um, vm)
        axp = c.Center + c.Axis * ((p - c.Center).dot(c.Axis))
        radial = p - axp
        radial.normalize()
        kind = "hole" if n.dot(radial) < 0 else "round"
        length = round(f.Area / (3.141592653589793 * 2 * c.Radius), 2) if c.Radius else 0   # full-circle estimate
        key = (kind, round(2 * c.Radius, 2), round(c.Center.x, 2), round(c.Center.y, 2), round(c.Center.z, 2),
               tuple(round(abs(a), 1) for a in c.Axis))
        holes[key] = length
    return {"valid": shape.isValid(), "solids": len(shape.Solids),
            "size_xyz": [round(bb.XLength, 3), round(bb.YLength, 3), round(bb.ZLength, 3)],
            "volume_mm3": round(shape.Volume, 2),
            "cylinders": [{"kind": k[0], "diameter": k[1], "centre_xyz": list(k[2:5]), "axis": list(k[5]), "length_estimate": v}
                          for k, v in sorted(holes.items())],
            "note": "centre = point on the cylinder axis (read the position with the axis direction); length_estimate assumes a full circle."}
