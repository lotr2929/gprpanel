import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
f = r"C:\_myProjects\+GPR\gprpanel\index.html"
txt = open(f, encoding="utf-8", errors="replace").read()
orig = txt
changes = []

# 1. Fix image CSS - always 300px tall, natural width, centred
OLD1 = "  .detail-illustration img { width: auto; max-width: 100%; height: auto; max-height: 300px; display: block; }"
NEW1 = "  .detail-illustration img { height: 300px; width: auto; max-width: 100%; display: block; margin: 0 auto; }"
if OLD1 in txt: txt = txt.replace(OLD1, NEW1, 1); changes.append("img CSS: fixed 300px height")
else: changes.append("MISS: img CSS")

# 2. Move credit outside illustration box, style as grey italic below
OLD2 = ("  .detail-img-credit { position: absolute; bottom: 3px; right: 6px; font-size: 9px;"
        " color: rgba(255,255,255,0.8); text-shadow: 0 1px 2px rgba(0,0,0,0.6); pointer-events: none; }")
NEW2 = ("  .detail-img-credit { display: block; font-size: 10px; color: var(--text-ter);"
        " font-style: italic; font-family: var(--font); padding: 3px 8px 6px;"
        " background: var(--bg); text-align: right; }")
if OLD2 in txt: txt = txt.replace(OLD2, NEW2, 1); changes.append("credit CSS: grey italic below")
else: changes.append("MISS: credit CSS")

# 3. Fix illustration container - remove position:relative (credit no longer overlays)
OLD3 = "  .detail-illustration { display: flex; justify-content: center; align-items: center;"
if OLD3 in txt:
    # Find full rule and remove position:relative if present
    idx = txt.find(OLD3)
    end = txt.find("}", idx) + 1
    rule = txt[idx:end]
    new_rule = rule.replace(" position: relative;", "").replace("position: relative;", "")
    txt = txt[:idx] + new_rule + txt[end:]
    changes.append("illustration: removed position:relative")

# 4. Fix onload - use fixed 300px height, move credit outside illus
OLD4 = ("          img.style.maxWidth  = img.naturalWidth + 'px';\n"
        "          img.style.maxHeight = '300px';\n"
        "          img.style.width     = 'auto';\n"
        "          img.style.height    = 'auto';\n"
        "          img.style.display   = 'block';\n"
        "          img.style.margin    = '0 auto';\n"
        "          img.alt = (p.species || p.name || '');\n"
        "          illus.innerHTML = '';\n"
        "          illus.appendChild(img);\n"
        "          const credit = document.createElement('span');\n"
        "          credit.className = 'detail-img-credit';\n"
        "          credit.textContent = 'Image: Wikimedia Commons contributors, CC BY-SA';\n"
        "          illus.appendChild(credit);\n")
NEW4 = ("          img.style.height  = '300px';\n"
        "          img.style.width   = 'auto';\n"
        "          img.style.display = 'block';\n"
        "          img.alt = (p.species || p.name || '');\n"
        "          illus.innerHTML = '';\n"
        "          illus.appendChild(img);\n"
        "          // Credit goes below the illustration box\n"
        "          const creditEl = illus.nextElementSibling?.classList.contains('detail-img-credit')\n"
        "            ? illus.nextElementSibling\n"
        "            : (() => { const c = document.createElement('div');\n"
        "                c.className = 'detail-img-credit';\n"
        "                illus.parentNode.insertBefore(c, illus.nextSibling); return c; })();\n"
        "          creditEl.textContent = 'Image: Wikimedia Commons contributors, CC BY-SA';\n")
if OLD4 in txt: txt = txt.replace(OLD4, NEW4, 1); changes.append("onload: 300px height, credit below")
else: changes.append("MISS: onload block")

open(f, "w", encoding="utf-8").write(txt)
for c in changes: print(c)
print("Done." if txt != orig else "NO CHANGES")
