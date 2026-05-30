import sys, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── 1. enrich_usda_zones.py — in-place progress ────────────────────────────
f = r"C:\_myProjects\+GPR\GPRTool\lai\enrich_usda_zones.py"
txt = open(f, encoding="utf-8", errors="replace").read()
OLD = "    for i, (row_id, zone) in enumerate(rows_to_update, 1):\n        retries = 3"
NEW = ("    total_u = len(rows_to_update)\n"
       "    for i, (row_id, zone) in enumerate(rows_to_update, 1):\n"
       "        pct = int(i / total_u * 100)\n"
       '        print(f"\\r  [{i:>5}/{total_u}] {pct:>3}% done  zone: {zone:<12}", end="", flush=True)\n'
       "        retries = 3")
if OLD in txt:
    open(f, "w", encoding="utf-8").write(txt.replace(OLD, NEW, 1))
    print("zones: progress added OK")
else:
    print("zones: OLD pattern not found — check indentation")

# ── 2. enrich_usda_traits.py — fix encoding (rewrite docstring) ────────────
f2 = r"C:\_myProjects\+GPR\GPRTool\lai\enrich_usda_traits.py"
txt2 = open(f2, encoding="utf-8", errors="replace").read()
# Replace garbled box-drawing characters in docstring with ASCII dashes
txt2_fixed = txt2.replace("\ufffd\u201c", "--").replace("\ufffd", "-").replace("\u201c", '"').replace("\u201d", '"')
# More aggressive: replace any non-ASCII in the top docstring with safe chars
lines = txt2_fixed.splitlines(keepends=True)
in_docstring = False
fixed_lines = []
for i, line in enumerate(lines):
    if i < 20:  # only fix top docstring area
        safe = line.encode("ascii", errors="replace").decode("ascii").replace(b"?".decode(), "-")
        fixed_lines.append(safe)
    else:
        fixed_lines.append(line)
open(f2, "w", encoding="utf-8").write("".join(fixed_lines))
print("traits: encoding fixed OK")
print("Done.")
