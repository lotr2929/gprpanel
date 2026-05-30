import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
f = r"C:\_myProjects\+GPR\gprpanel\index.html"
txt = open(f, encoding="utf-8", errors="replace").read()

# Fix 1: Wikipedia onload - cap maxWidth at natural width
OLD1 = ("        img.onload = () => {\n"
        "          const ratio = img.naturalWidth / img.naturalHeight;\n"
        "          illus.appendChild(img);\n"
        "          illus.appendChild(credit);\n")
NEW1 = ("        img.onload = () => {\n"
        "          img.style.maxWidth = img.naturalWidth + 'px';\n"
        "          illus.appendChild(img);\n"
        "          illus.appendChild(credit);\n")
if OLD1 in txt: txt = txt.replace(OLD1, NEW1, 1); print("Wikipedia onload fixed")
else: print("MISS: Wikipedia onload")

# Fix 2: second onload (iNaturalist/GBIF path)
OLD2 = "    img.onload = () => {\n"
NEW2 = "    img.onload = () => {\n      img.style.maxWidth = img.naturalWidth + 'px';\n"
if OLD2 in txt: txt = txt.replace(OLD2, NEW2, 1); print("iNat onload fixed")
else: print("MISS: iNat onload")

open(f, "w", encoding="utf-8").write(txt)
