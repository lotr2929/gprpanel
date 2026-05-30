import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
f = r"C:\_myProjects\+GPR\gprpanel\index.html"
lines = open(f, encoding="utf-8", errors="replace").readlines()

# Find the exact lines
for i, line in enumerate(lines):
    if "function openFullAccount()" in line:
        start = i
    if start and "alert('Full Account:" in line:
        alert_line = i
    if start and line.strip() == "}" and i > start:
        end = i
        break

# Replace lines start..end (inclusive) with proper implementation
new_fn = (
    "function openFullAccount() {\n"
    "  const p = _detailPlant; if (!p) return;\n"
    "  document.getElementById('fdesc-title').textContent = p.species || p.name || '';\n"
    "  const TIER = ['','Urban field (T1)','Open-ground (T2)','Genus mean (T3)','PFT mean (T4)'];\n"
    "  const rw = (l,v) => (v && String(v) !== 'undefined' && String(v) !== '') ?\n"
    "    '<div class=\"fdesc-row\"><span>'+l+'</span><span>'+v+'</span></div>' : '';\n"
    "  const ht = p.height_mature_m ? p.height_mature_m+'\u2009m' : '\u2014';\n"
    "  const kl = p.native_koppen || '\u2014';\n"
    "  const lv = p.lai_mean ? (+p.lai_mean).toFixed(1) : '\u2014';\n"
    "  document.getElementById('fdesc-body').innerHTML =\n"
    "    '<div class=\"fdesc-section\"><h3>Identity</h3>'+\n"
    "    rw('Scientific name','<em>'+esc(p.species||'')+'</em>')+\n"
    "    rw('Common name/s',esc(p.common_names||p.common_name||p.common||''))+\n"
    "    rw('Family',esc(p.family||''))+\n"
    "    rw('Plant type',esc((p.landscape_category||'')+(p.leaf_phenology?' \u2014 '+p.leaf_phenology:'')))+\n"
    "    rw('Growth form',esc(p.growth_form||p.shape||''))+'</div>'+\n"
    "    '<div class=\"fdesc-section\"><h3>LAI &amp; GPR Data</h3>'+\n"
    "    rw('LAI mean',lv)+\n"
    "    rw('Data tier',p.tier?'T'+p.tier+' \u2014 '+(TIER[p.tier]||''):'')+\n"
    "    rw('Source',esc(p.sources||p.source||p.tier_source||''))+'</div>'+\n"
    "    '<div class=\"fdesc-section\"><h3>Morphology &amp; Climate</h3>'+\n"
    "    rw('Mature height',ht)+\n"
    "    rw('Growth rate',esc(p.growth_rate_label||''))+\n"
    "    rw('Climate',esc(kl))+\n"
    "    rw('Drought tolerance',esc(p.drought_tolerance||''))+\n"
    "    rw('Shade tolerance',esc(p.shade_tolerance||''))+\n"
    "    rw('Fire tolerance',esc(p.fire_tolerance||''))+\n"
    "    rw('Frost hardiness',p.frost_hardiness_c!=null?p.frost_hardiness_c+'\u00b0C':'')+'</div>'+\n"
    "    '<div class=\"fdesc-section\"><h3>Urban</h3>'+\n"
    "    rw('Root depth',esc(p.root_depth||''))+\n"
    "    rw('Moisture use',esc(p.moisture_use||''))+\n"
    "    rw('Toxicity',esc(p.toxicity||''))+'</div>';\n"
    "  document.getElementById('fdesc-overlay').classList.add('open');\n"
    "}\n"
    "function closeFdesc() {\n"
    "  document.getElementById('fdesc-overlay').classList.remove('open');\n"
    "}\n"
)

new_lines = lines[:start] + [new_fn] + lines[end+1:]
open(f, "w", encoding="utf-8").write("".join(new_lines))
print(f"Replaced lines {start}-{end} with openFullAccount implementation.")
