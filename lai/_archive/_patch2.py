import sys, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
f = r"C:\_myProjects\+GPR\gprpanel\index.html"
txt = open(f, encoding="utf-8", errors="replace").read()

idx = txt.find("11 primary sources</div></div>")
if idx > 0:
    region = txt[idx:idx+300]
    print(repr(region))
