import sys, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
f = r"C:\_myProjects\+GPR\gprpanel\index.html"
txt = open(f, encoding="utf-8", errors="replace").read()
orig = txt
changes = []

# ── 1. Panel min-width 390px (mobile phone proportions) ───────────────────
OLD1 = '#app { display: flex; flex-direction: column; height: 100vh; width: 100%; max-width: 840px; background: var(--bg); box-shadow: 0 0 24px rgba(0,0,0,0.12); }'
NEW1 = '#app { display: flex; flex-direction: column; height: 100vh; width: 100%; min-width: 390px; max-width: 840px; background: var(--bg); box-shadow: 0 0 24px rgba(0,0,0,0.12); }'
if OLD1 in txt: txt = txt.replace(OLD1, NEW1, 1); changes.append("min-width 390px")
else: changes.append("MISS: #app width")

# ── 2. Add tab-plants padding (search bar + list) ─────────────────────────
OLD2 = '  #tab-calc { padding: 10px; }\n  #tab-docs { padding: 0; }'
NEW2 = '  #tab-plants { padding: 10px 10px 0; }\n  #tab-calc { padding: 10px; }\n  #tab-docs { padding: 0; }'
if OLD2 in txt: txt = txt.replace(OLD2, NEW2, 1); changes.append("tab-plants padding")
else: changes.append("MISS: tab padding block")

# ── 3. Remove plant-list inline padding (now on tab) ─────────────────────
OLD3 = '    <div id="plant-list" style="padding: 0 10px;">'
NEW3 = '    <div id="plant-list">'
if OLD3 in txt: txt = txt.replace(OLD3, NEW3, 1); changes.append("plant-list inline padding removed")

# ── 4. Scientific name: fix HTML rendering (esc wrapping em tags) ─────────
OLD4 = '    [\'Scientific name\', `<em>${esc(p.species||p.name||\'\')}</em>`],'
NEW4 = '    [\'Scientific name\', `<em>${esc(p.species||p.name||\'\')}</em>`, true],'
if OLD4 in txt: txt = txt.replace(OLD4, NEW4, 1); changes.append("scientific name raw flag")
else: changes.append("MISS: scientific name row")

# ── 5. Image icon: change to camera emoji, query already fetches image_url ─
OLD5 = "    const imgDot = p.image_url ? '<span class=\"sp-img-dot\" title=\"Image available\">\u25cf</span>' : '';\n    tr.innerHTML = `<td>${imgDot}<em>${esc(p.species)}</em>"
NEW5 = "    const imgIcon = p.image_url ? '\U0001f4f7 ' : '\u00a0\u00a0\u00a0 ';\n    tr.innerHTML = `<td><span style=\"font-size:10px;opacity:0.6\">${imgIcon}</span><em>${esc(p.species)}</em>"
if OLD5 in txt: txt = txt.replace(OLD5, NEW5, 1); changes.append("image icon camera")
else: changes.append("MISS: imgDot")

# ── 6. Rename Full Account to Full Description ────────────────────────────
OLD6 = 'Full Account \u2192</button>'
NEW6 = 'Full Description \u2192</button>'
if OLD6 in txt: txt = txt.replace(OLD6, NEW6, 1); changes.append("Full Account -> Full Description")
else: changes.append("MISS: Full Account text")

# ── 7. Replace alert stub with real modal ─────────────────────────────────
# Add modal CSS first
OLD7 = '  .sp-img-dot { color: var(--green); font-size: 7px; vertical-align: middle;\n    margin-right: 4px; opacity: 0.7; }'
NEW7 = ('  /* Full Description modal */\n'
        '  .fdesc-overlay { display:none; position:fixed; inset:0; background:rgba(0,0,0,0.45); z-index:100;\n'
        '    justify-content:center; align-items:flex-start; padding:20px; overflow-y:auto; }\n'
        '  .fdesc-overlay.open { display:flex; }\n'
        '  .fdesc-box { background:#fff; border-radius:10px; width:100%; max-width:680px;\n'
        '    box-shadow:0 8px 32px rgba(0,0,0,0.2); overflow:hidden; }\n'
        '  .fdesc-header { background:var(--green); color:#fff; padding:12px 16px;\n'
        '    display:flex; justify-content:space-between; align-items:center; }\n'
        '  .fdesc-header h2 { font-size:14px; font-weight:600; font-style:italic; }\n'
        '  .fdesc-header button { background:transparent; border:none; color:#fff;\n'
        '    font-size:20px; cursor:pointer; line-height:1; padding:0 4px; }\n'
        '  .fdesc-body { padding:16px; font-size:12px; line-height:1.7; overflow-y:auto; max-height:80vh; }\n'
        '  .fdesc-section { margin-bottom:16px; }\n'
        '  .fdesc-section h3 { font-size:11px; font-weight:700; text-transform:uppercase;\n'
        '    letter-spacing:0.5px; color:var(--text-sec); margin-bottom:8px;\n'
        '    border-bottom:0.5px solid var(--border); padding-bottom:4px; }\n'
        '  .fdesc-row { display:flex; justify-content:space-between; padding:3px 0;\n'
        '    border-bottom:0.5px solid var(--border); }\n'
        '  .fdesc-row span:first-child { color:var(--text-sec); }\n'
        '  .fdesc-row span:last-child { text-align:right; font-weight:500; max-width:60%; }')
if OLD7 in txt: txt = txt.replace(OLD7, NEW7, 1); changes.append("fdesc modal CSS added")
else:
    # CSS anchor not found, append before </style>
    txt = txt.replace('</style>', NEW7 + '\n</style>', 1)
    changes.append("fdesc modal CSS appended")

# ── 8. Add modal HTML before </body> ─────────────────────────────────────
if 'fdesc-overlay' not in txt or 'class="fdesc-overlay"' not in txt:
    MODAL_HTML = (
        '\n  <!-- Full Description modal -->\n'
        '  <div id="fdesc-overlay" class="fdesc-overlay" onclick="if(event.target===this)closeFdesc()">\n'
        '    <div class="fdesc-box">\n'
        '      <div class="fdesc-header">\n'
        '        <h2 id="fdesc-title"></h2>\n'
        '        <button onclick="closeFdesc()">&times;</button>\n'
        '      </div>\n'
        '      <div class="fdesc-body" id="fdesc-body"></div>\n'
        '    </div>\n'
        '  </div>\n')
    txt = txt.replace('</body>', MODAL_HTML + '</body>', 1)
    changes.append("fdesc modal HTML added")

# ── 9. Replace openFullAccount stub ──────────────────────────────────────
OLD9 = ('function openFullAccount() {\n'
        '  const p = _detailPlant; if (!p) return;\n'
        '  // TODO: open full account modal -- species: p.species\n'
        '  alert(\'Full Account: \' + (p.species || p.name) + \'\\n(Full account view coming in next session)\');\n'
        '}')
NEW9 = (
    'function openFullAccount() {\n'
    '  const p = _detailPlant; if (!p) return;\n'
    '  const ov = document.getElementById("fdesc-overlay");\n'
    '  document.getElementById("fdesc-title").textContent = p.species || p.name || "";\n'
    '  const TIER = ["","Urban field (T1)","Open-ground measured (T2)","Genus mean (T3)","PFT mean (T4)"];\n'
    '  const rows = (label, val) => val && val !== "\u2014" ? `<div class="fdesc-row"><span>${label}</span><span>${val}</span></div>` : "";\n'
    '  const ht = p.height_mature_m ? `${p.height_mature_m}\u2009m` : "\u2014";\n'
    '  const sp = p.canopy_radius_m  ? `${p.canopy_radius_m}\u2009m radius` : "\u2014";\n'
    '  const gr = p.growth_rate_m_yr_display || p.growth_rate_label || "\u2014";\n'
    '  const kl = p.koppen_description || p.native_koppen || "\u2014";\n'
    '  const laiVal = p.lai_mean ? `${(+p.lai_mean).toFixed(1)} (range ${(+( p.lai_min||p.lai_mean)).toFixed(1)}\u2013${(+(p.lai_max||p.lai_mean)).toFixed(1)})` : "\u2014";\n'
    '  document.getElementById("fdesc-body").innerHTML = `\n'
    '    <div class="fdesc-section"><h3>Identity</h3>\n'
    '      ${rows("Scientific name","<em>" + esc(p.species||"") + "</em>")}\n'
    '      ${rows("Common name/s", esc(p.common_names||p.common_name||p.common||""))}\n'
    '      ${rows("Family",        esc(p.family||""))}\n'
    '      ${rows("Plant type",    esc(p.landscape_category||"") + (p.leaf_phenology?" \u2014 "+esc(p.leaf_phenology):""))}\n'
    '      ${rows("Growth form",   esc(p.growth_form||p.shape||""))}\n'
    '    </div>\n'
    '    <div class="fdesc-section"><h3>LAI &amp; GPR Data</h3>\n'
    '      ${rows("LAI", laiVal)}\n'
    '      ${rows("Data tier", p.tier ? "T"+p.tier+" \u2014 "+(TIER[p.tier]||"") : "")}\n'
    '      ${rows("Source", esc(p.sources||p.source||p.tier_source||""))}\n'
    '    </div>\n'
    '    <div class="fdesc-section"><h3>Morphology</h3>\n'
    '      ${rows("Mature height", ht)}\n'
    '      ${rows("Canopy spread", sp)}\n'
    '      ${rows("Growth rate",   esc(gr))}\n'
    '      ${rows("Canopy shape",  esc(p.canopy_shape||""))}\n'
    '    </div>\n'
    '    <div class="fdesc-section"><h3>Climate &amp; Tolerance</h3>\n'
    '      ${rows("Climate", esc(kl))}\n'
    '      ${rows("Drought tolerance", esc(p.drought_tolerance||""))}\n'
    '      ${rows("Shade tolerance",   esc(p.shade_tolerance||""))}\n'
    '      ${rows("Fire tolerance",    esc(p.fire_tolerance||""))}\n'
    '      ${rows("Salt tolerance",    esc(p.salinity_tolerance||""))}\n'
    '      ${rows("Frost hardiness",   p.frost_hardiness_c!=null ? p.frost_hardiness_c+"\u00b0C" : "")}\n'
    '    </div>\n'
    '    <div class="fdesc-section"><h3>Urban Performance</h3>\n'
    '      ${rows("Root depth",    esc(p.root_depth||""))}\n'
    '      ${rows("Moisture use",  esc(p.moisture_use||""))}\n'
    '      ${rows("Toxicity",      esc(p.toxicity||""))}\n'
    '    </div>`;\n'
    '  ov.classList.add("open");\n'
    '}\n'
    'function closeFdesc() {\n'
    '  document.getElementById("fdesc-overlay").classList.remove("open");\n'
    '}')
if OLD9 in txt: txt = txt.replace(OLD9, NEW9, 1); changes.append("openFullAccount implemented")
else: changes.append("MISS: openFullAccount stub")

# ── 10. Update Supabase select to fetch new fields ────────────────────────
OLD10 = ".select('species, common_name, lai_mean, tier, landscape_category, growth_form, image_url, image_credit, image_source')"
NEW10 = ".select('species, common_name, common_names, lai_mean, lai_min, lai_max, tier, landscape_category, growth_form, leaf_phenology, native_koppen, family, height_mature_m, canopy_radius_m, growth_rate_label, drought_tolerance, shade_tolerance, fire_tolerance, salinity_tolerance, frost_hardiness_c, canopy_shape, root_depth, moisture_use, toxicity, sources, tier_source, image_url, image_credit, image_source')"
if OLD10 in txt: txt = txt.replace(OLD10, NEW10, 1); changes.append("select expanded")
else: changes.append("MISS: select statement")

open(f, "w", encoding="utf-8").write(txt)
for c in changes: print(c)
print("Done." if txt != orig else "NO CHANGES.")
