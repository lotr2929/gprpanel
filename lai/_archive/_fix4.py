import sys, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
f = r"C:\_myProjects\+GPR\GPRTool\lai\enrich_usda_traits.py"
txt = open(f, encoding="utf-8", errors="replace").read()

# Fix the progress call — store species name alongside id in updates
OLD = ("    # Match all in memory\n"
       "    updates, last_sp = [], \"\"\n"
       "    for row in rows:\n"
       "        sp  = clean_name(row[\"species\"] or \"\")\n"
       "        acc = clean_name(row.get(\"accepted_name\") or \"\")\n"
       "        traits = usda.get(sp) or usda.get(acc)\n"
       "        if not traits:\n"
       "            genus = sp.split()[0] + \" \" if sp else \"\"\n"
       "            traits = next((v for k, v in usda.items() if k.startswith(genus) and k == sp), None)\n"
       "        if traits:\n"
       "            updates.append({\"id\": row[\"id\"], \"enrichment_sources\": \"USDA_PlantAtlas\", **traits})\n"
       "            last_sp = row[\"species\"] or sp")
NEW = ("    # Match all in memory — store (_species_name, payload) tuples\n"
       "    updates = []\n"
       "    for row in rows:\n"
       "        sp  = clean_name(row[\"species\"] or \"\")\n"
       "        acc = clean_name(row.get(\"accepted_name\") or \"\")\n"
       "        traits = usda.get(sp) or usda.get(acc)\n"
       "        if traits:\n"
       "            updates.append((row[\"species\"] or sp,\n"
       "                            {\"id\": row[\"id\"], \"enrichment_sources\": \"USDA_PlantAtlas\", **traits}))")

OLD2 = ("    buf, done = [], 0\n"
        "    for update in updates:\n"
        "        buf.append(update)\n"
        "        done += 1\n"
        "        if len(buf) >= UPSERT_BATCH:\n"
        "            flush_buffer(buf); buf = []\n"
        "        if done % PRINT_EVERY == 0 or done == matched:\n"
        "            sp = update.get(\"enrichment_sources\", \"\")\n"
        "            # find original species name\n"
        "            progress(done, matched, total, t0, updates[done-1].get(\"id\",\"\") and\n"
        "                     next((r[\"species\"] for r in rows if r[\"id\"]==update[\"id\"]), \"\"))\n"
        "\n"
        "    flush_buffer(buf)\n"
        "    progress(matched, matched, total, t0, \"\")")
NEW2 = ("    buf, done = [], 0\n"
        "    for sp_name, payload in updates:\n"
        "        buf.append(payload)\n"
        "        done += 1\n"
        "        if len(buf) >= UPSERT_BATCH:\n"
        "            flush_buffer(buf); buf = []\n"
        "        if done % PRINT_EVERY == 0 or done == matched:\n"
        "            progress(done, matched, total, t0, sp_name)\n"
        "\n"
        "    flush_buffer(buf)\n"
        "    progress(matched, matched, total, t0, \"complete\")")

ok = []
if OLD in txt:
    txt = txt.replace(OLD, NEW, 1); ok.append("match loop fixed")
else:
    ok.append("MISS: match loop")
if OLD2 in txt:
    txt = txt.replace(OLD2, NEW2, 1); ok.append("upsert loop fixed")
else:
    ok.append("MISS: upsert loop")

open(f, "w", encoding="utf-8").write(txt)
for m in ok: print(m)
