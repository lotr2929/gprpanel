import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
f = r"C:\_myProjects\+GPR\gprpanel\index.html"
lines = open(f, encoding="utf-8", errors="replace").readlines()

for i, line in enumerate(lines):
    if 'imgIcon' in line and ('image_url' in line or "dY" in line or "\U0001f4f7" in line or "📷" in line):
        # Replace with clean HTML entity approach
        lines[i] = "    const imgIcon = p.image_url ? '<span title=\"Image available\" style=\"color:var(--green);margin-right:3px;font-size:10px\">\u25a3</span>' : '<span style=\"margin-right:3px;display:inline-block;width:13px\"></span>';\n"
        print(f"Fixed imgIcon at line {i}")
        break

open(f, "w", encoding="utf-8").write("".join(lines))
