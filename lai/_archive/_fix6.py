import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
f = r"C:\_myProjects\+GPR\GPRTool\lai\enrich_usda_zones.py"
txt = open(f, encoding="utf-8", errors="replace").read()

OLD = '        print(f"\\r  [{i:>5}/{total_u}] {pct:>3}% done  zone: {zone:<12}", end="", flush=True)'
NEW = ('        line = f"  [{i:>5}/{total_u}] {pct:>3}% done  zone: {str(zone):<12}"\n'
       '        print("\\r" + line[:76].ljust(76), end="", flush=True)')
if OLD in txt:
    txt = txt.replace(OLD, NEW, 1)
    open(f, "w", encoding="utf-8").write(txt)
    print("zones progress fixed")
else:
    print("MISS")
