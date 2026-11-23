"""Check the acrylic case's bond stack: the vinyl mask (on the whole back of the sheet) and the
tape lie on the tray's rim, rib and ledge, so the rim must stop MaskT + TapeT below the sheet
and the overall thickness stays SheetT + InnerD + BackWall (7.15).

    python3 check_acrylic_stack.py [magnet_case_acrylic.json]    (needs solidcraft-cli on PATH or CLI=...)
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

here = Path(__file__).parent
script = Path(sys.argv[1]) if len(sys.argv) > 1 else here / "magnet_case_acrylic.json"
cli = os.environ.get("CLI", "solidcraft-cli")
cmds = json.loads(script.read_text())
params = {c["params"]["name"]: c["params"]["expression"] for c in cmds if c["command"] == "parameters.add"}
env = {"max": max, "min": min}
for name, expr in params.items():
    env[name] = eval(expr.replace(" mm", "").replace("mm", ""), {}, env)
mask, tape = env.get("MaskT", 0.0), env.get("TapeT", 0.0)
with tempfile.TemporaryDirectory() as tmp:
    out = Path(tmp) / "res.json"
    subprocess.run([cli, "run", str(script), "--results", "--quiet", "--json-out", str(out)], check=True,
                   capture_output=True)
    bodies = {b["name"]: b["bbox"] for b in json.loads(out.read_text())[-1]["bodies"]}
tray_top, sheet_lo, sheet_hi = bodies["Tray"]["max"][2], bodies["FrontSheet"]["min"][2], bodies["FrontSheet"]["max"][2]
ok = True
inset = env.get("SheetLip", 0.0) + env.get("SheetGap", 0.0)
sheet_x0, sheet_y0 = bodies["FrontSheet"]["min"][0], bodies["FrontSheet"]["min"][1]
for what, got, want in (("lip top flush with the sheet face", tray_top, env["ShellH"] + env["SheetT"]),
                        ("sheet back", sheet_lo, env["ShellH"]), ("overall", sheet_hi, 7.15),
                        ("sheet inset from the left edge (lip + gap)", sheet_x0, 0.95),
                        ("sheet inset from the bottom edge (lip + gap)", sheet_y0, 0.95)):
    good = abs(got - want) < 0.01
    ok &= good
    print(f"{'ok  ' if good else 'FAIL'} {what}: {got:.3f} (want {want:.3f})")
# The chin strip (a separate flat part, printed on the bed): LedgeT thick, its top flush with the rim,
# stopping short of the USB-C notch; it rests on a step in the tray's bottom and left walls.
strip = bodies.get("ChinStrip")
if strip is None:
    ok = False
    print("FAIL chin strip: no ChinStrip body (the ledge must be a separate part to print without supports)")
else:
    notch_x0 = env["UsbCX"] - env["UsbW"] / 2 - env["Clear"]
    for what, got, want in (("chin strip bottom", strip["min"][2], env["ShellH"] - mask - tape - env["LedgeT"]),
                            ("chin strip top", strip["max"][2], env["ShellH"] - mask - tape)):
        good = abs(got - want) < 0.01
        ok &= good
        print(f"{'ok  ' if good else 'FAIL'} {what}: {got:.3f} (want {want:.3f})")
    good = strip["max"][0] <= notch_x0 + 1e-6
    ok &= good
    print(f"{'ok  ' if good else 'FAIL'} chin strip ends at x {strip['max'][0]:.2f}, left of the USB-C notch ({notch_x0:.2f})")
rim = env["ShellH"] - mask - tape
print(f"mask {mask:g} + tape {tape:g} between the rim ({rim:.2f}) and the sheet")
sys.exit(0 if ok and tape > 0 else 1)
