import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
f = r"C:\_myProjects\+GPR\GPRTool\lai\enrich_usda_traits.py"
txt = open(f, encoding="utf-8", errors="replace").read()
changes = []

# 1. Move _warnings to module level (before flush_buffer definition)
OLD1 = 'UPSERT_BATCH = 200\nPRINT_EVERY  = 10'
NEW1 = 'UPSERT_BATCH = 200\nPRINT_EVERY  = 10\n_warnings    = []  # module-level so flush_buffer can append'
if OLD1 in txt: txt = txt.replace(OLD1, NEW1, 1); changes.append("_warnings module-level")
else: changes.append("MISS: UPSERT_BATCH block")

# 2. Remove the local _warnings from main()
OLD2 = '    buf, done, _warnings = [], 0, []'
NEW2 = '    _warnings.clear()\n    buf, done = [], 0'
if OLD2 in txt: txt = txt.replace(OLD2, NEW2, 1); changes.append("local _warnings removed")
else: changes.append("MISS: local _warnings")

# 3. Shorten label to 10 chars max so line stays under 76
OLD3 = '    sp      = (last_sp[:14] + "..") if len(last_sp) > 16 else last_sp'
NEW3 = '    sp      = last_sp[:10]'
if OLD3 in txt: txt = txt.replace(OLD3, NEW3, 1); changes.append("label capped at 10 chars")
else: changes.append("MISS: label cap")

open(f, "w", encoding="utf-8").write(txt)
for c in changes: print(c)
