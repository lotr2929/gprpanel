import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
f = r"C:\_myProjects\+GPR\gprpanel\index.html"
txt = open(f, encoding="utf-8", errors="replace").read()
orig = txt

OLD = '    </div>\n    <div id="doc-section-view" class="doc-section">\n      <div class="doc-back" onclick="closeDocSection()">\n        <i class="ti ti-arrow-left"></i> Contents\n      </div>\n      <div class="doc-body" id="doc-body"></div>\n    </div>\n  </div>'
NEW = '    </div>\n    </div>  <!-- /doc-contents-wrap -->\n    <div id="doc-section-view" class="doc-section-wrap">\n      <div class="doc-body" id="doc-body" style="padding:12px;line-height:1.65;overflow-y:auto;flex:1;"></div>\n    </div>\n  </div>'
if OLD in txt:
    txt = txt.replace(OLD, NEW, 1); open(f,"w",encoding="utf-8").write(txt); print("fixed OK")
else:
    print("MISS"); print("doc-section-view present:", "doc-section-view" in txt)
