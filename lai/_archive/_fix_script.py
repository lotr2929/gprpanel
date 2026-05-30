import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
f = r"C:\_myProjects\+GPR\gprpanel\index.html"
lines = open(f, encoding="utf-8", errors="replace").readlines()
changes = []

# ── 1. Fix panel width: add flex-shrink:0 to #app ─────────────────────────
for i, line in enumerate(lines):
    if "#app { display: flex; flex-direction: column; height: 100vh; width: min(840px, 100%);" in line:
        lines[i] = lines[i].replace(
            "width: min(840px, 100%);",
            "width: 840px; max-width: 100%; flex-shrink: 0;"
        )
        changes.append(f"app width fixed at line {i}")
        break

# ── 2. Find the broken script tag containing openFullAccount ──────────────
# Find line with <script src="jspdf..." that contains function content
jspdf_line = -1
func_end = -1
for i, line in enumerate(lines):
    if 'jspdf' in line and '<script src=' in line:
        jspdf_line = i
    if jspdf_line >= 0 and '</script>' in line and i > jspdf_line:
        func_end = i
        break

changes.append(f"jspdf script block: lines {jspdf_line}-{func_end}")

# Extract function content (lines between jspdf tag and </script>)
func_lines = lines[jspdf_line+1:func_end]

# Rebuild: proper self-closing jspdf script + separate script block with function
new_block = (
    # Proper jspdf loader
    '<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>\n'
    '<script>\n'
    + "".join(func_lines)
    + '</script>\n'
)

lines = lines[:jspdf_line] + [new_block] + lines[func_end+1:]
changes.append("openFullAccount moved to own script block")

open(f, "w", encoding="utf-8").write("".join(lines))
for c in changes: print(c)
