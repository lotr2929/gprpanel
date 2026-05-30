import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
f = r"C:\_myProjects\+GPR\gprpanel\index.html"
lines = open(f, encoding="utf-8", errors="replace").readlines()

# Fix the imgIcon line - remove it, we'll inline it
for i, line in enumerate(lines):
    if "const imgIcon" in line and "image_url" in line:
        lines[i] = ""  # remove, inlining below
        icon_line = i
        print(f"Removed imgIcon at {i}")
        break

# Fix tr.innerHTML
for i, line in enumerate(lines):
    if '${imgIcon}' in line and 'tr.innerHTML' in line:
        lines[i] = (
            "    const cn = p.common_name ? ` <span style=\"color:var(--text-ter);font-style:normal\">(${esc(p.common_name)})</span>` : '';\n"
            "    const imBadge = p.image_url ? ' <span class=\"tb\" style=\"background:#fff;color:var(--text-sec);border:0.5px solid var(--border)\">Im</span>' : '';\n"
            "    tr.innerHTML = `<td><em>${esc(p.species)}</em>${cn}\n"
            "      <span class=\"tb t${p.tier}\">T${p.tier}</span>${imBadge}</td>\n"
            "      <td class=\"r\">${(+p.lai_mean).toFixed(1)}</td>`;\n"
        )
        print(f"Fixed tr.innerHTML at {i}")
        break

open(f, "w", encoding="utf-8").write("".join(lines))
