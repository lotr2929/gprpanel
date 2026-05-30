import sys, os, gzip, shutil, sqlite3, time, requests, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from _credentials import SUPABASE_URL, SUPABASE_KEY, HEADERS
BASE         = os.path.dirname(__file__)
SOURCE_DIR   = os.path.join(BASE, "source_data")
DB_PATH      = os.path.join(SOURCE_DIR, "usda_plants.db")
GZ_PATH      = os.path.join(SOURCE_DIR, "usda_plants.db.gz")
UPSERT_BATCH = 200
PRINT_EVERY  = 10
_warnings    = []  # module-level so flush_buffer can append

def clean_name(raw):
    """Strip HTML tags and author names, return lowercase binomial."""
    clean = re.sub(r"<[^>]+>", "", raw or "").strip()
    parts = clean.split()
    if len(parts) >= 2:
        return (parts[0] + " " + parts[1]).lower()
    return clean.lower()

def find_db():
    if os.path.exists(DB_PATH): return DB_PATH
    if os.path.exists(GZ_PATH):
        print("  Decompressing usda_plants.db.gz ...")
        with gzip.open(GZ_PATH, "rb") as fi, open(DB_PATH, "wb") as fo:
            shutil.copyfileobj(fi, fo)
        return DB_PATH
    return None

def nv(v):
    return v.lower().strip() if v and str(v).strip().lower() not in ("none","","null") else None

def load_usda(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT p.scientific_name,
               c.growth_rate, c.drought_tolerance, c.shade_tolerance,
               c.salinity_tolerance, c.fire_tolerance, c.fire_resistant,
               c.height_mature_feet, c.root_depth_minimum,
               c.moisture_use, c.toxicity,
               c.temperature_minimum_f, c.frost_free_days_minimum,
               c.shape_and_orientation, c.foliage_texture,
               c.leaf_retention, c.anaerobic_tolerance,
               c.adapted_to_coarse_textured_soils,
               c.adapted_to_fine_textured_soils,
               c.palatable_human, c.known_allelopath
        FROM plant_characteristics c
        JOIN plants p ON p.id = c.plant_id
    """).fetchall()
    conn.close()

    data = {}
    for row in rows:
        name = clean_name(row["scientific_name"])
        if not name or " " not in name:
            continue

        ht = None
        try:
            ft = float(row["height_mature_feet"] or 0)
            ht = round(ft * 0.3048, 1) if ft > 0 else None
        except: pass

        rd = None
        try:
            rdv = float(row["root_depth_minimum"] or 0)
            rd = "deep" if rdv > 36 else "medium" if rdv > 12 else "shallow" if rdv > 0 else None
        except: pass

        frost_c = None
        try:
            fv = float(row["temperature_minimum_f"] or 0)
            frost_c = round((fv - 32) * 5/9, 1) if fv != 0 else None
        except: pass

        entry = {k: v for k, v in {
            "growth_rate":         nv(row["growth_rate"]),
            "drought_tolerance":   nv(row["drought_tolerance"]),
            "shade_tolerance":     nv(row["shade_tolerance"]),
            "salinity_tolerance":      nv(row["salinity_tolerance"]),
            "fire_tolerance":      nv(row["fire_tolerance"]),
            "fire_resistant":      nv(row["fire_resistant"]),
            "height_mature_m":     ht,
            "root_depth":          rd,
            "moisture_use":        nv(row["moisture_use"]),
            "toxicity":            nv(row["toxicity"]),
            "frost_hardiness_c":   frost_c,
            "canopy_shape":        nv(row["shape_and_orientation"]),
            "foliage_texture":     nv(row["foliage_texture"]),
            "leaf_retention":      nv(row["leaf_retention"]),
            "anaerobic_tolerance": nv(row["anaerobic_tolerance"]),
        }.items() if v is not None}

        if entry:
            data[name] = entry

    return data

def fetch_all_species():
    rows, offset = [], 0
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/gpr_plant_species",
            headers=HEADERS,
            params={"select":"id,species,accepted_name","order":"id.asc",
                    "offset":offset,"limit":1000}, timeout=30)
        r.raise_for_status()
        batch = r.json()
        if not batch: break
        rows.extend(batch)
        if len(batch) < 1000: break
        offset += 1000
    return rows

def flush_buffer(buf):
    if not buf: return
    for attempt in range(3):
        try:
            r = requests.post(f"{SUPABASE_URL}/rest/v1/gpr_plant_species",
                headers=HEADERS, json=buf, timeout=30)
            r.raise_for_status()
            return
        except Exception as e:
            if attempt == 2:
                body = ""
                try: body = e.response.text[:200]
                except: pass
                _warnings.append(f"WARN 400: {body or str(e)[:120]}")
            else: time.sleep(2)

def progress(done, matched, total, t0, last_sp):
    elapsed = time.time() - t0
    rate    = done / elapsed if elapsed > 0 else 1
    eta     = (matched - done) / rate if rate > 0 and matched > done else 0
    pct     = int(done / matched * 100) if matched else 0
    bar     = "#" * (pct // 5) + "-" * (20 - pct // 5)
    sp      = last_sp[:10]
    line    = f"  [{bar}] {pct:>3}%  {done:>5}/{matched}  {int(elapsed//60)}m{int(elapsed%60):02d}s  eta {int(eta//60)}m{int(eta%60):02d}s  {sp}"
    # Pad/truncate to exactly 76 chars so line never wraps and \r always works
    line = line[:76].ljust(76)
    print("\r" + line, end="", flush=True)

def main():
    t0 = time.time()
    print("GPR Global Plant Database -- USDA Traits Enrichment")
    print("Source: USDA PLANTS via plantatlas.ai\n")

    db_path = find_db()
    if not db_path:
        print("ERROR: usda_plants.db not found in source_data/"); sys.exit(1)

    print("Loading USDA SQLite ...", end=" ", flush=True)
    usda = load_usda(db_path)
    print(f"{len(usda):,} species loaded.")

    print("Fetching Supabase species ...", end=" ", flush=True)
    rows = fetch_all_species()
    total = len(rows)
    print(f"{total:,} rows fetched.\n")

    # Match all in memory — store (_species_name, payload) tuples
    updates = []
    for row in rows:
        sp  = clean_name(row["species"] or "")
        acc = clean_name(row.get("accepted_name") or "")
        traits = usda.get(sp) or usda.get(acc)
        if traits:
            updates.append((row["species"] or sp,
                            {"id": row["id"], "enrichment_sources": "USDA_PlantAtlas", **traits}))

    matched = len(updates)
    print(f"  Matches: {matched:,}/{total:,} ({matched/total*100:.1f}%)")
    print(f"  Fields: growth_rate, drought/shade/salt/fire tolerance, height, root depth,")
    print(f"          toxicity, frost hardiness, canopy shape, foliage texture")
    print(f"  Upsert batch: {UPSERT_BATCH} | Progress every {PRINT_EVERY} rows\n")

    if matched == 0:
        print("No matches found. Check species name format.")
        # Debug: show first 5 USDA keys vs first 5 Supabase names
        print("First 5 USDA keys:", list(usda.keys())[:5])
        print("First 5 Supabase:", [r["species"] for r in rows[:5]])
        return

    _warnings.clear()
    buf, done = [], 0
    for sp_name, payload in updates:
        buf.append(payload)
        done += 1
        if len(buf) >= UPSERT_BATCH:
            flush_buffer(buf); buf = []
        if done % PRINT_EVERY == 0 or done == matched:
            progress(done, matched, total, t0, sp_name)

    flush_buffer(buf)
    progress(matched, matched, total, t0, "done")

    elapsed = time.time() - t0
    print()
    for w in _warnings: print(f"  {w}")
    print(f"\nDone in {int(elapsed//60)}m {int(elapsed%60)}s.")
    print(f"Enriched: {matched:,}/{total:,} species ({matched/total*100:.1f}% match rate).")

if __name__ == "__main__":
    main()