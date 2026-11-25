# Run with freecadcmd:  freecadcmd.exe key_cap_test.py   (CPU only). Rebuilds our real cap and compares it with the reference volume.
import os, sys
here = os.path.dirname(os.path.abspath(sys.argv[-1] if sys.argv[-1].endswith(".py") else __file__))
exec(open(os.path.join(here, "..", "skills", "key-cap", "key_cap.py"), encoding="utf-8").read())
cap = build_key_cap("CapTest", head_d=20.9, head_t=1.8, shoulder_lo=-3.76, shoulder_hi=5.76, shaft_angle_deg=90.2774, out_dir=os.environ.get("CAP_OUT"))
r = check_key_cap(cap)
print("RESULT", r)
ref = 551.2952   # sharp-edged reference volume of the printed cap (independent CAD calculation)
print("VOLUME_DIFF_TO_SHARP_REFERENCE", round(r["volume_mm3"] - ref, 3))
print("PASS" if r["ok"] and abs(r["volume_mm3"] - ref) < 0.5 else "FAIL")

# Negative test: a cap whose passage cuts through BOTH lips (a C-ring) must be rejected by the checker.
import Part
from FreeCAD import Vector as V
p = eval(cap.CapParams)
slot = Part.makeBox(p["q_hi"] - p["q_lo"], p["r_out"] + 2, p["height"] + 2, V(p["q_lo"], 0, -1))
slot.rotate(V(0, 0, 0), V(0, 0, 1), p["shaft_angle_deg"] - 90.0)
cap.Shape = cap.Shape.cut(slot)
bad = check_key_cap(cap)
print("NEGATIVE_TEST lips_closed =", bad["lips_closed"], "ok =", bad["ok"])
print("NEGATIVE PASS" if (not bad["lips_closed"] and not bad["ok"]) else "NEGATIVE FAIL")
