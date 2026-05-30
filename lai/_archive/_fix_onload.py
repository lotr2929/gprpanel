import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
f = r"C:\_myProjects\+GPR\gprpanel\index.html"
lines = open(f, encoding="utf-8", errors="replace").readlines()

# Replace lines 640-655 (the Wikipedia onload block)
NEW_ONLOAD = (
    "        img.onload = () => {\n"
    "          img.style.maxWidth  = img.naturalWidth + 'px';\n"
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
    "          illus.appendChild(credit);\n"
    "        };\n"
)

new_lines = lines[:640] + [NEW_ONLOAD] + lines[656:]
open(f, "w", encoding="utf-8").write("".join(new_lines))
print(f"Replaced {656-640} lines with clean onload. Done.")
