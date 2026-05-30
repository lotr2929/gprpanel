import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
f = r"C:\_myProjects\+GPR\gprpanel\index.html"
txt = open(f, encoding="utf-8", errors="replace").read()
orig = txt
changes = []

# ── 1. Fix body/app to maintain consistent width ─────────────────────────
OLD1 = "  html, body { height: 100%; background: #e8e8e8; font-family: var(--font); font-size: 13px; color: var(--text); display: flex; justify-content: center; }"
NEW1 = "  html, body { height: 100%; background: #e8e8e8; font-family: var(--font); font-size: 13px; color: var(--text); display: flex; justify-content: center; align-items: flex-start; }"
if OLD1 in txt: txt = txt.replace(OLD1, NEW1, 1); changes.append("body align-items fixed")
else: changes.append("MISS: body css")

OLD2 = "#app { display: flex; flex-direction: column; height: 100vh; width: 100%; min-width: 390px; max-width: 840px;"
NEW2 = "#app { display: flex; flex-direction: column; height: 100vh; width: min(840px, 100%);"
if OLD2 in txt: txt = txt.replace(OLD2, NEW2, 1); changes.append("app width fixed to min(840px,100%)")
else: changes.append("MISS: #app width")

# ── 2. Revert select to only valid Supabase fields ────────────────────────
OLD3 = ".select('species, common_name, common_names, lai_mean, lai_min, lai_max, tier, landscape_category, growth_form, leaf_phenology, native_koppen, family, height_mature_m, canopy_radius_m, growth_rate_label, drought_tolerance, shade_tolerance, fire_tolerance, salinity_tolerance, frost_hardiness_c, canopy_shape, root_depth, moisture_use, toxicity, sources, tier_source, image_url, image_credit, image_source')"
NEW3 = ".select('species, common_name, lai_mean, lai_min, lai_max, tier, landscape_category, growth_form, leaf_phenology, native_koppen, family, height_mature_m, growth_rate, drought_tolerance, shade_tolerance, fire_tolerance, salinity_tolerance, frost_hardiness_c, canopy_shape, root_depth, moisture_use, toxicity, sources, tier_source, image_url, image_credit, image_source')"
if OLD3 in txt: txt = txt.replace(OLD3, NEW3, 1); changes.append("select fixed - removed invalid fields")
else: changes.append("MISS: select statement")

# ── 3. Fix references to common_names / growth_rate_label in modal JS ─────
txt = txt.replace("p.common_names||p.common_name||p.common||''", "p.common_name||p.common||''")
txt = txt.replace("p.growth_rate_label||''", "p.growth_rate||''")
txt = txt.replace("p.growth_rate_m_yr_display || p.growth_rate_label || ", "p.growth_rate || ")
changes.append("field name refs fixed in JS")

open(f, "w", encoding="utf-8").write(txt)
for c in changes: print(c)
print("Done." if txt != orig else "NO CHANGES")
