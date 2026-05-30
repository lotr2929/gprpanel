import sys, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
f = r"C:\_myProjects\+GPR\gprpanel\index.html"
txt = open(f, encoding="utf-8", errors="replace").read()
orig = txt
changes = []

# ── 1. Move #status INSIDE tab-calc (before its closing </div>) ───────────
# The status bar is between tab-calc and tab-docs, causing doc to render outside tabs
OLD1 = ('  </div>\n\n  <div id="status">Connecting\u2026</div>\n\n  <!-- '
        '\U0001f4c4\u2665 TAB 3: DOCUMENTATION \U0001f4c4\u2665 -->\n  <div id="tab-docs"')
NEW1 = ('  </div>\n\n  <!-- \U0001f4c4\u2665 TAB 3: DOCUMENTATION \U0001f4c4\u2665 -->\n  <div id="tab-docs"')
if OLD1 in txt:
    txt = txt.replace(OLD1, NEW1, 1); changes.append("status moved inside tab-calc")
else:
    # Try simpler match
    OLD1b = '  <div id="status">Connecting\u2026</div>\n\n  <!-- '
    if OLD1b in txt:
        txt = txt.replace('  <div id="status">Connecting\u2026</div>\n', '', 1)
        changes.append("status removed from between tabs")
    else:
        changes.append("MISS: status placement")

# ── 2. Status bar: add it back inside tab-calc before closing div ─────────
OLD2 = ('    <div class="share-url-row" id="share-url-row">\n'
        '      <input type="text" id="share-url" readonly onclick="this.select()" />\n'
        '      <button onclick="copyShareUrl()">Copy</button>\n'
        '    </div>\n'
        '  </div>')
NEW2 = ('    <div class="share-url-row" id="share-url-row">\n'
        '      <input type="text" id="share-url" readonly onclick="this.select()" />\n'
        '      <button onclick="copyShareUrl()">Copy</button>\n'
        '    </div>\n'
        '  </div>\n'
        '  <div id="status">Connecting\u2026</div>')
if OLD2 in txt:
    txt = txt.replace(OLD2, NEW2, 1); changes.append("status added after tab-calc")
else:
    changes.append("MISS: share-url-row close")

# ── 3. Fix tab-content padding — remove from ALL, add back selectively ─────
# The padding: 10px on .tab-content is narrowing plant-detail
OLD3 = '  .tab-content { display: none; padding: 10px; overflow-y: auto; flex: 1; }'
NEW3 = ('  .tab-content { display: none; overflow-y: auto; flex: 1; }\n'
        '  #tab-calc { padding: 10px; }\n'
        '  #tab-docs { padding: 0; }')
if OLD3 in txt:
    txt = txt.replace(OLD3, NEW3, 1); changes.append("tab padding fixed")
else:
    changes.append("MISS: tab-content padding")

# ── 4. Fix plant-list padding so species list still has some indent ────────
OLD4 = '  #plant-list { flex: 1; overflow-y: auto; }'
NEW4 = '  #plant-list { flex: 1; overflow-y: auto; padding: 0 10px; }'
if OLD4 in txt:
    txt = txt.replace(OLD4, NEW4, 1); changes.append("plant-list padding added")
else:
    changes.append("MISS: plant-list")

# ── 5. Tab inner labels — replace number-only with short titles ────────────
OLD5 = ("const DOC_TAB_LABELS = ['Abs','1','2','3','4','5','6','7','8','9'];\n"
        "const DOC_TAB_TITLES = ['Abstract','Background','Methods','Data Records',\n"
        "  'Validation','Usage','Limitations','Future','Code','References'];")
NEW5 = ("const DOC_TAB_LABELS = ['Abstract','Background','Methods','Records',\n"
        "  'Validation','Usage','Limits','Future','Code','Refs'];\n"
        "const DOC_TAB_TITLES = DOC_TAB_LABELS;  // labels are already the titles")
if OLD5 in txt:
    txt = txt.replace(OLD5, NEW5, 1); changes.append("tab labels updated")
else:
    changes.append("MISS: DOC_TAB_LABELS")

# ── 6. Search list image icon — add to renderList ─────────────────────────
OLD6 = "      li.innerHTML = `<span class=\"sp-name\">${esc(p.species||p.name||'')}</span>"
NEW6 = ("      const imgIcon = p.image_url ? '<span class=\"sp-img-dot\" title=\"Image available\">\u25cf</span>' : '';\n"
        "      li.innerHTML = `${imgIcon}<span class=\"sp-name\">${esc(p.species||p.name||'')}</span>")
if OLD6 in txt:
    txt = txt.replace(OLD6, NEW6, 1); changes.append("image icon in list")
else:
    changes.append("MISS: renderList innerHTML")

# ── 7. Image icon CSS ─────────────────────────────────────────────────────
OLD7 = '  .detail-account:hover { background: var(--green-lt); }'
NEW7 = ('  .detail-account:hover { background: var(--green-lt); }\n'
        '  .sp-img-dot { color: var(--green); font-size: 7px; vertical-align: middle;\n'
        '    margin-right: 4px; opacity: 0.7; }')
if OLD7 in txt:
    txt = txt.replace(OLD7, NEW7, 1); changes.append("sp-img-dot CSS added")
else:
    changes.append("MISS: detail-account hover")

open(f, "w", encoding="utf-8").write(txt)
for c in changes: print(c)
print("Done." if txt != orig else "NO CHANGES.")
