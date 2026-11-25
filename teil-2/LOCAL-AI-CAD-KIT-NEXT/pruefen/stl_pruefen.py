"""Quick STL check before printing: one body, watertight, size, volume.

Run: uv run --project ../foto-mcp --with trimesh --with networkx python stl_pruefen.py <file.stl> [expected_x expected_y expected_z]
"""
import sys

import numpy as np
import trimesh


def main():
    if len(sys.argv) not in (2, 5):
        print(__doc__)
        return 2
    m = trimesh.load(sys.argv[1], force="mesh")
    bodies = len(m.split(only_watertight=False))
    ext = np.round(m.extents, 3).tolist()
    print(f"bodies: {bodies}  watertight: {m.is_watertight}  consistent normals: {m.is_winding_consistent}")
    print(f"size (x y z): {ext} mm   volume: {m.volume:.2f} mm3")
    ok = bodies == 1 and m.is_watertight and m.is_winding_consistent
    if len(sys.argv) == 5:
        soll = [float(v) for v in sys.argv[2:5]]
        diff = [round(a - b, 3) for a, b in zip(ext, soll)]
        print(f"difference to expected size: {diff} mm")
        ok &= all(abs(d) <= 0.05 for d in diff)
    print("OK for slicing" if ok else "CHECK THIS MODEL before printing")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
