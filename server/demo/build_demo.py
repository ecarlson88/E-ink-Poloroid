"""Builds a self-contained, playable demo of the upload page (published as a claude.ai artifact).

    python3 server/demo/build_demo.py OUT.html

It takes the real server/static/index.html, drops the document wrapper (the artifact host adds
one), and puts shim.js in front of the page's script: a stand-in server that keeps photos in
memory, crops them to 3:4 and dithers the magnet preview on a canvas. A demo band adds buttons
to simulate the magnet waking up, a low battery and a reset. Nothing leaves the browser.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
shim = (HERE / "shim.js").read_text()
s = (HERE.parent / "static" / "index.html").read_text()
s = re.sub(r"<!doctype html>\s*", "", s, flags=re.I)
for t in ('<html lang="en">', "</html>", "<head>", "</head>", "<body>", "</body>"):
    s = s.replace(t, "")
s = re.sub(r'<meta charset="utf-8">\s*', "", s)
s = re.sub(r'<meta name="viewport"[^>]*>\s*', "", s)
s = s.replace("<title>Fridge magnet photos</title>", "<title>Fridge Magnet Photos</title>")
s = s.replace("</style>", """  :root { color-scheme: light; }
  .demo-band { margin: -4px 0 16px; padding: 10px 12px; border-radius: 12px; background: #FFF7E0; border: 1px solid #F0DFA8; color: #5A4A12; display: flex; flex-wrap: wrap; align-items: center; gap: 8px 10px; font-size: 13px; }
  .demo-band b { font-weight: 700; }
  .demo-band span { flex: 1 1 220px; min-width: 0; }
  .demo-band button { border: 1px solid #E3CF8A; background: #FFFFFF; color: #3D3210; border-radius: 9px; min-height: 40px; padding: 0 12px; font-weight: 600; font-size: 13px; }
  .demo-band button:hover { background: #FFF1C9; }
  .demo-note { margin: 0; font-size: 12px; color: var(--muted); }
</style>""", 1)
main = '<main class="wrap" id="app" hidden>'
assert s.count(main) == 1
s = s.replace(main, main + """
  <section class="demo-band" aria-label="Demo controls">
    <span><b>Demo.</b> Everything stays in your browser. Act as the magnet you're looking at (on Library, all of them):</span>
    <button type="button" id="demo-wake">Magnet wakes up</button>
    <button type="button" id="demo-low">Battery low</button>
    <button type="button" id="demo-reset">Reset demo</button>
  </section>""")
login = '<button class="primary">Log in</button>'
assert s.count(login) == 1
s = s.replace(login, login + '\n  <p class="demo-note">Demo: type any password.</p>')
i = s.index("<script>")
s = s[:i] + "<script>\n" + shim + "\n</script>\n" + s[i:]
s = s.rstrip() + """
<script>
$("demo-wake").onclick = async () => { await window.__demo.checkIn(view); refresh(); };
$("demo-low").onclick = async () => { await window.__demo.lowBattery(view); refresh(); };
$("demo-reset").onclick = async () => { panelView.clear(); await window.__demo.reset(); setView("library"); refresh(); };
</script>
"""
Path(sys.argv[1]).write_text(s)
print(f"wrote {sys.argv[1]} ({len(s)} bytes)")
