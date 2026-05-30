import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
f = r"C:\_myProjects\+GPR\gprpanel\index.html"
txt = open(f, encoding="utf-8", errors="replace").read()
orig = txt

# The #tab-docs rule with display:flex overrides .tab-content { display:none }
# Fix: remove display:flex from #tab-docs, only set it on #tab-docs.active
OLD = "  #tab-docs { font-size: 12px; display: flex; flex-direction: column; }"
NEW = ("  #tab-docs { font-size: 12px; padding: 0; }\n"
       "  #tab-docs.active { display: flex; flex-direction: column; }")
if OLD in txt:
    txt = txt.replace(OLD, NEW, 1)
    open(f, "w", encoding="utf-8").write(txt)
    print("Fixed: display:flex removed from #tab-docs")
else:
    print("MISS - checking what's there:")
    import re
    m = re.search(r'#tab-docs \{[^}]+\}', txt)
    if m: print(repr(m.group(0)))
