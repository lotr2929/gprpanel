import sys, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
f = r"C:\_myProjects\+GPR\GPRTool\lai\enrich_images.py"
txt = open(f, encoding="utf-8", errors="replace").read()

# Fix encoding artifacts in docstring/prints
txt = re.sub(r'[\ufffd][\u201c\u201d]?', '-', txt)
txt = txt.replace('\u201c', '"').replace('\u201d', '"')

# Fix progress: replace per-species prints with in-place update
OLD = (
    "                print(f'  [{done:>6}/{total}] - [{src}] {species}')\n"
    "                print(f'  [{done:>6}/{total}] - (no image) {species}')\n"
    "            # Print summary every 500 species"
)
# Find and replace the two print lines inside the worker callback
txt = re.sub(
    r"print\(f'  \[.*?\] .*? \{species\}'\)",
    "pass  # progress below",
    txt
)

# Add in-place progress after the done increment
OLD2 = "            done += 1\n"
NEW2 = (
    "            done += 1\n"
    "            if done % 10 == 0 or done == total:\n"
    "                elapsed = time.time() - t0\n"
    "                rate = done / elapsed if elapsed > 0 else 1\n"
    "                eta = (total - done) / rate if rate > 0 else 0\n"
    "                pct = int(done / total * 100)\n"
    "                bar = '#' * (pct // 5) + '-' * (20 - pct // 5)\n"
    "                lbl = (species[:10]) if 'species' in dir() else ''\n"
    "                line = f'  [{bar}] {pct:>3}%  {done:>6}/{total}  {int(elapsed//60)}m{int(elapsed%60):02d}s  eta {int(eta//60)}m{int(eta%60):02d}s  hits:{found}'\n"
    "                print('\\r' + line[:76].ljust(76), end='', flush=True)\n"
)
if OLD2 in txt:
    txt = txt.replace(OLD2, NEW2, 1)

open(f, "w", encoding="utf-8").write(txt)
print("enrich_images.py fixed.")
