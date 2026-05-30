import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
f = r"C:\_myProjects\+GPR\gprpanel\index.html"
lines = open(f, encoding="utf-8", errors="replace").readlines()

# Find all tr.innerHTML assignments in the renderList area and keep only the new one
# New one has 'imBadge', old one has 'shape'
new_block_start = old_block_start = -1
for i, line in enumerate(lines):
    if 'const cn =' in line and 'common_name' in line:
        new_block_start = i
    if "const shape = p.growth_form" in line:
        old_block_start = i

print(f"new_block_start={new_block_start}, old_block_start={old_block_start}")

# Remove old block: from "const shape" through its tr.innerHTML closing backtick
if old_block_start > 0:
    end = old_block_start
    for j in range(old_block_start, old_block_start + 10):
        if '`;' in lines[j] and 'td class="r"' in lines[j]:
            end = j
            break
    print(f"Removing old block lines {old_block_start}-{end}:")
    for k in range(old_block_start, end+1):
        print(f"  {k}: {repr(lines[k][:80])}")
        lines[k] = ""
    print("Done.")

open(f, "w", encoding="utf-8").write("".join(lines))
