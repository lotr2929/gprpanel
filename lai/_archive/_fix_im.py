import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
f = r"C:\_myProjects\+GPR\gprpanel\index.html"
txt = open(f, encoding="utf-8", errors="replace").read()
OLD = "background:#fff;color:var(--text-sec);border:0.5px solid var(--border)"
NEW = "background:#fff;color:var(--text-sec)"
if OLD in txt:
    open(f,"w",encoding="utf-8").write(txt.replace(OLD,NEW,1)); print("Border removed from Im badge")
else:
    print("MISS")
