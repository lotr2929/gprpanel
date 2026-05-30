import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
f = r"C:\_myProjects\+GPR\gprpanel\index.html"
lines = open(f, encoding="utf-8", errors="replace").readlines()

# Find the forEach block
for i, line in enumerate(lines):
    if "data.forEach(p =>" in line:
        forEach_start = i
        break

# Find its closing }); 
depth = 0
forEach_end = -1
for j in range(forEach_start, forEach_start + 30):
    for ch in lines[j]:
        if ch == '{': depth += 1
        if ch == '}': depth -= 1
    if depth == 0 and j > forEach_start:
        forEach_end = j
        break

print(f"forEach: lines {forEach_start}-{forEach_end}")
for k in range(forEach_start, forEach_end+1):
    print(f"  {k}: {repr(lines[k][:90])}")

# Replace entire forEach with clean version
NEW = (
    "  data.forEach(p => {\n"
    "    const tr = document.createElement('tr'); tr.className = 'pr';\n"
    "    const cn = p.common_name ? ` <span style=\"color:var(--text-ter);font-style:normal\">(${esc(p.common_name)})</span>` : '';\n"
    "    const imBadge = p.image_url ? ' <span class=\"tb\" style=\"background:#fff;color:var(--text-sec)\">Im</span>' : '';\n"
    "    tr.innerHTML = `<td><em>${esc(p.species)}</em>${cn} <span class=\"tb t${p.tier}\">T${p.tier}</span>${imBadge}</td><td class=\"r\">${(+p.lai_mean).toFixed(1)}</td>`;\n"
    "    tr.addEventListener('click', () => {\n"
    "      document.querySelectorAll('.pr').forEach(r => r.classList.remove('sel'));\n"
    "      tr.classList.add('sel');\n"
    "      writeSelection({ type: currentType, species: p.species, lai: p.lai_mean, shape: p.growth_form||'' });\n"
    "    });\n"
    "    tr.addEventListener('dblclick', () => openDetail(p));\n"
    "    tbody.appendChild(tr);\n"
    "  });\n"
)

new_lines = lines[:forEach_start] + [NEW] + lines[forEach_end+1:]
open(f, "w", encoding="utf-8").write("".join(new_lines))
print("forEach rewritten cleanly.")
