import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
f = r"C:\_myProjects\+GPR\gprpanel\index.html"
txt = open(f, encoding="utf-8", errors="replace").read()
orig = txt
changes = []

# ── 1. plant-list padding (it uses a table inside, add padding to search+table wrapper)
OLD1 = '    <div id="plant-list">'
NEW1 = '    <div id="plant-list" style="padding: 0 10px;">'
if OLD1 in txt: txt = txt.replace(OLD1, NEW1, 1); changes.append("plant-list padding added")
else: changes.append("MISS: plant-list div")

# ── 2. Image icon in table row (tr.innerHTML)
OLD2 = "    tr.innerHTML = `<td><em>${esc(p.species)}</em>\n      <span class=\"tb t${p.tier}\">T${p.tier}</span>\n      <span style=\"color:var(--text-ter);font-size:10px\"> (${shape})</span></td>\n      <td class=\"r\">${(+p.lai_mean).toFixed(1)}</td>`;"
NEW2 = "    const imgDot = p.image_url ? '<span class=\"sp-img-dot\" title=\"Image available\">\u25cf</span>' : '<span class=\"sp-img-dot\" style=\"opacity:0\">\u25cf</span>';\n    tr.innerHTML = `<td>${imgDot}<em>${esc(p.species)}</em>\n      <span class=\"tb t${p.tier}\">T${p.tier}</span>\n      <span style=\"color:var(--text-ter);font-size:10px\"> (${shape})</span></td>\n      <td class=\"r\">${(+p.lai_mean).toFixed(1)}</td>`;"
if OLD2 in txt: txt = txt.replace(OLD2, NEW2, 1); changes.append("image dot in row")
else:
    # Try without the exact whitespace
    if "tr.innerHTML = `<td><em>${esc(p.species)}</em>" in txt:
        old_simple = 'tr.innerHTML = `<td><em>${esc(p.species)}</em>'
        new_simple = 'const imgDot = p.image_url ? \'<span class="sp-img-dot" title="Image available">\u25cf</span>\' : \'\';\n    tr.innerHTML = `<td>${imgDot}<em>${esc(p.species)}</em>'
        txt = txt.replace(old_simple, new_simple, 1)
        changes.append("image dot in row (simple match)")
    else:
        changes.append("MISS: tr.innerHTML")

# ── 3. Full Account button — ensure it shows in detail view  ─────────────
# Check if the button already exists in HTML (it does based on our scan)
if 'detail-account-btn' in txt:
    changes.append("Full Account button already present in HTML")
else:
    changes.append("MISS: Full Account button")

open(f, "w", encoding="utf-8").write(txt)
for c in changes: print(c)
