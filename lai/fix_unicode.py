import sys
files = [
    r"C:\_myProjects\+GPR\GPRTool\lai\download_usda_plants.py",
    r"C:\_myProjects\+GPR\GPRTool\lai\enrich_koppen.py",
    r"C:\_myProjects\+GPR\GPRTool\lai\upload_to_supabase.py",
    r"C:\_myProjects\+GPR\GPRTool\lai\build_gpr_globalplantdb.py",
]
HEADER = 'import sys\nsys.stdout.reconfigure(encoding="utf-8", errors="replace")\n'
REPLACEMENTS = [
    ("\u2717", "[FAIL]"),
    ("\u2713", "[OK]"),
    ("\u2192", "->"),
    ("\u2190", "<-"),
    ("\u2714", "[OK]"),
]
for f in files:
    text = open(f, encoding="utf-8").read()
    if "sys.stdout.reconfigure" not in text:
        text = HEADER + text
    for old, new in REPLACEMENTS:
        text = text.replace(old, new)
    open(f, "w", encoding="utf-8").write(text)
    print("Fixed: " + f.split("\\")[-1])
print("Done.")
