import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
f = r"C:\_myProjects\+GPR\gprpanel\index.html"
lines = open(f, encoding="utf-8", errors="replace").readlines()
changes = []

# Fix line 506-510: openFullAccount stub
# Lines are 0-indexed, so lines 505-509
if "function openFullAccount()" in lines[505]:
    lines[506] = "  const p = _detailPlant; if (!p) return;\n"
    lines[507] = "  const ov = document.getElementById('fdesc-overlay');\n"
    lines[508] = "  document.getElementById('fdesc-title').textContent = p.species || p.name || '';\n"
    lines[509] = "  const TIER = ['','Urban field (T1)','Open-ground measured (T2)','Genus mean (T3)','PFT mean (T4)'];\n"
    # Insert the rest after line 509 (index 509)
    rest = (
        "  const rw = (l,v) => (v && v !== '\u2014' && v !== 'undefined') ? `<div class=\"fdesc-row\"><span>${l}</span><span>${v}</span></div>` : '';\n"
        "  const ht = p.height_mature_m ? `${p.height_mature_m}\u2009m` : '\u2014';\n"
        "  const sp = p.canopy_radius_m ? `${p.canopy_radius_m}\u2009m radius` : '\u2014';\n"
        "  const gr = p.growth_rate_m_yr_display || p.growth_rate_label || '\u2014';\n"
        "  const kl = p.native_koppen || '\u2014';\n"
        "  const lv = p.lai_mean ? `${(+p.lai_mean).toFixed(1)}`  : '\u2014';\n"
        "  document.getElementById('fdesc-body').innerHTML =\n"
        "    '<div class=\"fdesc-section\"><h3>Identity</h3>' +\n"
        "    rw('Scientific name','<em>'+esc(p.species||'')+'</em>') +\n"
        "    rw('Common name/s', esc(p.common_names||p.common_name||p.common||'')) +\n"
        "    rw('Family', esc(p.family||'')) +\n"
        "    rw('Plant type', esc((p.landscape_category||'')+(p.leaf_phenology?' \u2014 '+p.leaf_phenology:''))) +\n"
        "    rw('Growth form', esc(p.growth_form||p.shape||'')) + '</div>' +\n"
        "    '<div class=\"fdesc-section\"><h3>LAI &amp; GPR Data</h3>' +\n"
        "    rw('LAI mean', lv) +\n"
        "    rw('Data tier', p.tier ? 'T'+p.tier+' \u2014 '+(TIER[p.tier]||'') : '') +\n"
        "    rw('Source', esc(p.sources||p.source||p.tier_source||'')) + '</div>' +\n"
        "    '<div class=\"fdesc-section\"><h3>Morphology</h3>' +\n"
        "    rw('Mature height', ht) + rw('Canopy spread', sp) +\n"
        "    rw('Growth rate', esc(gr)) + rw('Canopy shape', esc(p.canopy_shape||'')) + '</div>' +\n"
        "    '<div class=\"fdesc-section\"><h3>Climate &amp; Tolerance</h3>' +\n"
        "    rw('Climate', esc(kl)) + rw('Drought tolerance', esc(p.drought_tolerance||'')) +\n"
        "    rw('Shade tolerance', esc(p.shade_tolerance||'')) + rw('Fire tolerance', esc(p.fire_tolerance||'')) +\n"
        "    rw('Frost hardiness', p.frost_hardiness_c!=null ? p.frost_hardiness_c+'\u00b0C' : '') + '</div>' +\n"
        "    '<div class=\"fdesc-section\"><h3>Urban Performance</h3>' +\n"
        "    rw('Root depth', esc(p.root_depth||'')) + rw('Moisture use', esc(p.moisture_use||'')) +\n"
        "    rw('Toxicity', esc(p.toxicity||'')) + '</div>';\n"
        "  ov.classList.add('open');\n"
        "}\n"
        "function closeFdesc() {\n"
        "  document.getElementById('fdesc-overlay').classList.remove('open');\n"
        "}\n"
    )
    # Remove old lines 507-510 and replace with new content
    new_lines = lines[:507] + [rest] + lines[510:]
    lines = new_lines
    changes.append("openFullAccount implemented (line edit)")
else:
    changes.append("MISS: line 505 not openFullAccount")
    changes.append(repr(lines[505][:80]))

# Fix line 569: imgDot -> camera icon (find by content)
for i, line in enumerate(lines):
    if 'imgDot' in line or ('sp-img-dot' in line and 'const' in line):
        lines[i] = "    const imgIcon = p.image_url ? '\U0001f4f7 ' : '   ';\n"
        changes.append(f"imgDot -> imgIcon at line {i}")
        break

for i, line in enumerate(lines):
    if 'imgDot' in line and 'tr.innerHTML' in line:
        lines[i] = line.replace('${imgDot}', '${imgIcon}')
        changes.append(f"tr.innerHTML imgDot->imgIcon at line {i}")
        break
    if '${imgDot}' in line:
        lines[i] = line.replace('${imgDot}', '${imgIcon}')
        changes.append(f"template imgDot->imgIcon at line {i}")

open(f, "w", encoding="utf-8").write("".join(lines))
for c in changes: print(c)
