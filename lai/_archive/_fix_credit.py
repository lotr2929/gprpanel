import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
f = r"C:\_myProjects\+GPR\gprpanel\index.html"
lines = open(f, encoding="utf-8", errors="replace").readlines()
for i, line in enumerate(lines):
    if "detail-img-credit" in line and "position: absolute" in line:
        lines[i] = "  .detail-img-credit { display: block; font-size: 10px; color: var(--text-ter); font-style: italic; font-family: var(--font); padding: 3px 8px 6px; background: var(--bg); text-align: right; }\n"
        print(f"Fixed credit CSS at line {i}")
        break
open(f, "w", encoding="utf-8").write("".join(lines))
