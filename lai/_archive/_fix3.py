import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
f = r"C:\_myProjects\+GPR\gprpanel\index.html"
txt = open(f, encoding="utf-8", errors="replace").read()
orig = txt

OLD = ("function docGoContents() {\n"
       "  document.getElementById('doc-inner-tabs').classList.remove('visible');\n"
       "  document.getElementById('doc-contents-wrap').style.display = '';\n"
       "  document.getElementById('doc-body').style.display = 'none';\n"
       "}")
NEW = ("function docGoContents() {\n"
       "  document.getElementById('doc-inner-tabs').classList.remove('visible');\n"
       "  document.getElementById('doc-contents-wrap').style.display = '';\n"
       "  document.getElementById('doc-section-view').classList.remove('active');\n"
       "}")
if OLD in txt:
    txt = txt.replace(OLD, NEW, 1); open(f,"w",encoding="utf-8").write(txt); print("docGoContents fixed")
else:
    print("MISS")
