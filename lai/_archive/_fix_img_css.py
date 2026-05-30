import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
f = r"C:\_myProjects\+GPR\gprpanel\index.html"
txt = open(f, encoding="utf-8", errors="replace").read()

OLD = "  .detail-illustration img { max-width: 100%; max-height: 300px; object-fit: contain; display: block; }"
NEW = "  .detail-illustration img { width: auto; max-width: 100%; height: auto; max-height: 300px; display: block; }"

if OLD in txt:
    open(f,"w",encoding="utf-8").write(txt.replace(OLD,NEW,1))
    print("Fixed image CSS")
else:
    print("MISS")
