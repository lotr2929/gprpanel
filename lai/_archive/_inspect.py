import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
f = r"C:\_myProjects\+GPR\gprpanel\index.html"
lines = open(f, encoding="utf-8", errors="replace").readlines()

# Find the fetchWikipediaImage img.onload block and replace it
for i, line in enumerate(lines):
    if "img.onload = () => {" in line and i > 630:  # Wikipedia function area
        onload_start = i
        # Find end of this onload (closing };)
        for j in range(i+1, i+15):
            if lines[j].strip() in ("};", "};"[::-1]) or (lines[j].strip().startswith("}") and "img.src" in lines[j+1]):
                onload_end = j
                break
        print(f"Wikipedia onload: lines {onload_start}-{onload_end}")
        for k in range(onload_start, onload_end+1):
            print(f"  {k}: {repr(lines[k][:80])}")
        break
