import sys, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
f = r"C:\_myProjects\+GPR\gprpanel\index.html"
txt = open(f, encoding="utf-8", errors="replace").read()
original = txt
changes = []

# ── 1. Detail panel: fill full width (remove extra side padding) ───────────
OLD1 = "  .detail-body { padding: 12px 12px 0; }"
NEW1 = "  .detail-body { padding: 12px 0 0; }"
if OLD1 in txt: txt = txt.replace(OLD1, NEW1, 1); changes.append("detail-body padding fixed")
else: changes.append("MISS: detail-body padding")

# ── 2. Add Full Account button CSS ────────────────────────────────────────
OLD2 = "  .detail-select.selected { background: var(--text-info); }"
NEW2 = ("  .detail-select.selected { background: var(--text-info); }\n"
        "  .detail-account { margin: 6px 10px 14px; padding: 6px; background: transparent;\n"
        "    border: 0.5px solid var(--green); border-radius: var(--radius); font-size: 11px;\n"
        "    font-weight: 600; cursor: pointer; width: calc(100% - 20px);\n"
        "    color: var(--green); letter-spacing: 0.2px; }\n"
        "  .detail-account:hover { background: var(--green-lt); }")
if OLD2 in txt: txt = txt.replace(OLD2, NEW2, 1); changes.append("detail-account CSS added")
else: changes.append("MISS: detail-account CSS anchor")

# ── 3. Add Full Account button HTML after Select button ───────────────────
OLD3 = '      <button class="detail-select" id="detail-select-btn" onclick="selectFromDetail()">Select this plant</button>\n    </div>\n  </div>'
NEW3 = ('      <button class="detail-select" id="detail-select-btn" onclick="selectFromDetail()">Select this plant</button>\n'
        '      <button class="detail-account" id="detail-account-btn" onclick="openFullAccount()">Full Account \u2192</button>\n'
        '    </div>\n  </div>')
if OLD3 in txt: txt = txt.replace(OLD3, NEW3, 1); changes.append("Full Account button HTML added")
else: changes.append("MISS: Full Account button HTML anchor")

# ── 4. Doc tab bar CSS ────────────────────────────────────────────────────
OLD4 = "  #tab-docs { font-size: 12px; }"
NEW4 = ("  #tab-docs { font-size: 12px; display: flex; flex-direction: column; }\n"
        "  .doc-inner-tabs { display: none; flex-shrink: 0; overflow-x: auto;\n"
        "    border-bottom: 0.5px solid var(--border); background: var(--bg-sec); }\n"
        "  .doc-inner-tabs.visible { display: flex; }\n"
        "  .doc-inner-tab { padding: 7px 11px; font-size: 11px; white-space: nowrap;\n"
        "    cursor: pointer; color: var(--text-sec); border-bottom: 2px solid transparent;\n"
        "    margin-bottom: -1px; user-select: none; flex-shrink: 0; }\n"
        "  .doc-inner-tab.active { color: var(--green); border-bottom-color: var(--green);\n"
        "    font-weight: 600; background: var(--bg); }\n"
        "  .doc-inner-tab:hover:not(.active) { background: var(--green-lt); }\n"
        "  .doc-contents-wrap { flex: 1; overflow-y: auto; padding: 4px 10px; }\n"
        "  .doc-section-wrap { display: none; flex: 1; overflow-y: auto; }\n"
        "  .doc-section-wrap.active { display: flex; flex-direction: column; }")
if OLD4 in txt: txt = txt.replace(OLD4, NEW4, 1); changes.append("doc tab CSS added")
else: changes.append("MISS: doc tab CSS anchor")

# ── 5. Doc tab bar HTML inside #tab-docs ─────────────────────────────────
OLD5 = '  <div id="tab-docs" class="tab-content">\n    <div id="doc-contents" class="doc-contents">'
NEW5 = ('  <div id="tab-docs" class="tab-content">\n'
        '    <!-- inner tab bar (hidden until a section is opened) -->\n'
        '    <div id="doc-inner-tabs" class="doc-inner-tabs">\n'
        '      <div class="doc-inner-tab" onclick="docGoContents()">&#9776; Contents</div>\n'
        '    </div>\n'
        '    <div id="doc-contents-wrap" class="doc-contents-wrap">\n'
        '    <div id="doc-contents" class="doc-contents">')
if OLD5 in txt: txt = txt.replace(OLD5, NEW5, 1); changes.append("doc inner tabs HTML added")
else: changes.append("MISS: doc inner tabs HTML anchor")

# ── 6. Close the doc-contents-wrap div ────────────────────────────────────
# Find closing </div> after doc-toc-items and close the wrap
OLD6 = ('      <div class="doc-toc-item" onclick="openDocSection(9)">\n'
        '        <span class="doc-toc-num">9</span>\n'
        '        <div><div class="doc-toc-title">References</div>\n'
        '             <div class="doc-toc-sub">11 primary sources</div></div>\n'
        '      </div>\n'
        '    </div>  <!-- /doc-contents -->')
NEW6 = ('      <div class="doc-toc-item" onclick="openDocSection(9)">\n'
        '        <span class="doc-toc-num">9</span>\n'
        '        <div><div class="doc-toc-title">References</div>\n'
        '             <div class="doc-toc-sub">11 primary sources</div></div>\n'
        '      </div>\n'
        '    </div>  <!-- /doc-contents -->\n'
        '    </div>  <!-- /doc-contents-wrap -->')
if OLD6 in txt: txt = txt.replace(OLD6, NEW6, 1); changes.append("doc-contents-wrap closed")
else:
    # Try without the comment
    ALT6 = ('      </div>\n    </div>  <!-- /doc-contents -->')
    if ALT6 in txt:
        # Find it properly
        idx = txt.rfind('</div>  <!-- /doc-contents -->')
        if idx >= 0:
            txt = txt[:idx+len('</div>  <!-- /doc-contents -->')] + '\n    </div>  <!-- /doc-contents-wrap -->' + txt[idx+len('</div>  <!-- /doc-contents -->'):]
            changes.append("doc-contents-wrap closed (alt)")
        else:
            changes.append("MISS: doc-contents closing div")
    else:
        changes.append("MISS: doc-contents closing")

# ── 7. Update showDetail JS to show more fields + use detail-body padding ─
OLD7 = ('  const props = [\n'
        "    ['Type',       p.landscape_category || currentType],\n"
        "    ['Growth form',p.growth_form || p.shape || '\\u2014'],\n"
        "    ['Mean LAI',   lai],\n"
        "    ['Data tier',  `T${tier} \\u2014 ${['','Urban field','Open-ground','Genus mean','PFT inferred'][tier] || '\\u2014'}`],\n"
        "    ['Sources',    (p.sources || p.source || '\\u2014').substring(0, 60)],\n"
        '  ];')
# Try simpler match
if "    ['Type',       p.landscape_category" in txt:
    # find the block
    start = txt.find("  const props = [")
    end   = txt.find("  ];", start) + 4
    if start > 0 and end > start:
        OLD_BLOCK = txt[start:end]
        TIER_LABELS = "['','Urban field','Open-ground','Genus mean','PFT inferred']"
        NEW_BLOCK = (
            "  const tierLabel = " + TIER_LABELS + "[tier] || '';\n"
            "  const laiRange  = (p.lai_min && p.lai_max)\n"
            "    ? `${(+p.lai_min).toFixed(1)}\u2013${(+p.lai_max).toFixed(1)} (mean ${lai})` : lai;\n"
            "  const laiRow    = tier == 1\n"
            "    ? `${laiRange} \u2014 <em>${esc(p.sources||p.source||'')}</em>` : laiRange;\n"
            "  const klimat    = p.native_koppen ? `${esc(p.native_koppen)}` : '\u2014';\n"
            "  const heightVal = p.height_mature_m ? `${p.height_mature_m}\u2009m` : (p.height ? `${p.height}\u2009m` : '\u2014');\n"
            "  const spreadVal = p.canopy_radius_m  ? `${p.canopy_radius_m}\u2009m radius` : (p.radius ? `${p.radius}\u2009m` : '\u2014');\n"
            "  const growthVal = p.growth_rate_m_yr_display || p.growth_rate_label || '\u2014';\n"
            "  const props = [\n"
            "    ['Scientific name', `<em>${esc(p.species||p.name||'')}</em>`],\n"
            "    ['Common name/s',  esc(p.common_names||p.common_name||p.common||'\u2014')],\n"
            "    ['Plant type',     esc((p.landscape_category||currentType) + (p.leaf_phenology ? ' \u2014 ' + p.leaf_phenology : ''))],\n"
            "    ['Growth form',    esc(p.growth_form||p.shape||'\u2014')],\n"
            "    ['Growth rate',    esc(growthVal)],\n"
            "    ['Mature height',  esc(heightVal)],\n"
            "    ['Canopy spread',  esc(spreadVal)],\n"
            "    ['Climate',        esc(klimat)],\n"
            "    ['LAI',            laiRow, true],\n"
            "    ['Data tier',      tier ? `T${tier} \u2014 ${tierLabel}` : '\u2014'],\n"
            "    ['Sources',        esc((p.sources_other||p.sources||p.source||'\u2014').substring(0,80))],\n"
            "  ];"
        )
        txt = txt[:start] + NEW_BLOCK + txt[end:]
        changes.append("showDetail props expanded")
    else:
        changes.append("MISS: props block bounds not found")
else:
    changes.append("MISS: props block")

# ── 8. Update detail-props rendering to allow HTML (for italic LAI source) 
OLD8 = "  ).join('');"
# Be specific — find the join after the props map
OLD8_CTX = "    `<div class=\"detail-prop\"><span class=\"detail-prop-label\">${l}</span><span class=\"detail-prop-val\">${esc(String(v))}</span></div>`\n  ).join('');"
NEW8_CTX = ("    (raw ? `<div class=\"detail-prop\"><span class=\"detail-prop-label\">${l}</span>"
            "<span class=\"detail-prop-val\">${v}</span></div>`\n"
            "         : `<div class=\"detail-prop\"><span class=\"detail-prop-label\">${l}</span>"
            "<span class=\"detail-prop-val\">${esc(String(v))}</span></div>`)\n  ).join('');")
if OLD8_CTX in txt: txt = txt.replace(OLD8_CTX, NEW8_CTX, 1); changes.append("props rendering HTML flag added")
else: changes.append("MISS: props rendering")

# Update the props.map signature to destructure raw flag
OLD9 = "  ).join('') = props.map(([l,v]) =>"
# Don't try this — find the map call
if "props.map(([l,v]) =>" in txt:
    txt = txt.replace("props.map(([l,v]) =>", "props.map(([l,v,raw]) =>", 1)
    changes.append("props.map signature updated")
else:
    changes.append("MISS: props.map signature")

# ── 9. openDocSection JS — add tab bar logic ─────────────────────────────
OLD_OPEN = ("function openDocSection(i) {\n"
            "  document.getElementById('doc-contents').style.display = 'none';\n")
NEW_OPEN = ("// doc section labels for inner tab bar\n"
            "const DOC_TAB_LABELS = ['Abs','1','2','3','4','5','6','7','8','9'];\n"
            "const DOC_TAB_TITLES = ['Abstract','Background','Methods','Data Records',\n"
            "  'Validation','Usage','Limitations','Future','Code','References'];\n\n"
            "function buildDocTabs(activeIdx) {\n"
            "  const bar = document.getElementById('doc-inner-tabs');\n"
            "  bar.innerHTML = '<div class=\"doc-inner-tab\" onclick=\"docGoContents()\">&#9776; Contents</div>';\n"
            "  DOC_TAB_LABELS.forEach((lbl, idx) => {\n"
            "    const t = document.createElement('div');\n"
            "    t.className = 'doc-inner-tab' + (idx === activeIdx ? ' active' : '');\n"
            "    t.title = DOC_TAB_TITLES[idx];\n"
            "    t.textContent = lbl;\n"
            "    t.onclick = () => openDocSection(idx);\n"
            "    bar.appendChild(t);\n"
            "  });\n"
            "  bar.classList.add('visible');\n"
            "}\n\n"
            "function docGoContents() {\n"
            "  document.getElementById('doc-inner-tabs').classList.remove('visible');\n"
            "  document.getElementById('doc-contents-wrap').style.display = '';\n"
            "  document.getElementById('doc-body').style.display = 'none';\n"
            "}\n\n"
            "function openDocSection(i) {\n"
            "  document.getElementById('doc-contents-wrap').style.display = 'none';\n"
            "  buildDocTabs(i);\n")
if OLD_OPEN in txt: txt = txt.replace(OLD_OPEN, NEW_OPEN, 1); changes.append("openDocSection tab logic added")
else: changes.append("MISS: openDocSection function")

# ── 10. docBack becomes docGoContents ────────────────────────────────────
OLD_BACK = "  document.getElementById('doc-contents').style.display = '';\n"
if OLD_BACK in txt: txt = txt.replace(OLD_BACK, "  docGoContents();\n", 1); changes.append("docBack updated")
else: changes.append("MISS: docBack")

# ── 11. openFullAccount stub ─────────────────────────────────────────────
if "function openFullAccount()" not in txt:
    # Add before closing </script>
    STUB = ("\nfunction openFullAccount() {\n"
            "  const p = _detailPlant; if (!p) return;\n"
            "  // TODO: open full account modal — species: p.species\n"
            "  alert('Full Account: ' + (p.species || p.name) + '\\n(Full account view coming in next session)');\n"
            "}\n")
    txt = txt.replace("</script>", STUB + "</script>", 1)
    changes.append("openFullAccount stub added")

# ── Write ────────────────────────────────────────────────────────────────
if txt != original:
    open(f, "w", encoding="utf-8").write(txt)
    print("index.html updated.")
else:
    print("No changes made.")

for c in changes:
    print(" ", c)
