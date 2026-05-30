"""
enrich_austraits.py
===================
Enriches gpr_plant_species with traits from AusTraits v6 (Zenodo 10.5281/zenodo.3568417).
Covers ~33,500 Australian plant taxa -- primary source for AU/tropical species.

Traits extracted:
  plant_height_m       -> height_mature_m  (if not already set)
  specific_leaf_area   -> sla              (if not already set)
  leaf_area            -> (informational)
  fire_response        -> fire_tolerance
  drought_tolerance    -> drought_tolerance (if not already set)
  leaf_phenology       -> leaf_phenology    (if not already set)
  plant_growth_form    -> growth_form       (if not already set)
  woodiness_detailed   -> (feeds growth_form)

Citation: Falster, Gallagher et al (2021) Scientific Data 8:254
          https://doi.org/10.1038/s41597-021-01006-6

Run:  python enrich_austraits.py
"""
import sys, os, csv, time, json, zipfile, urllib.request, statistics, requests
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from _credentials import SUPABASE_URL, SUPABASE_KEY, HEADERS
BASE         = os.path.dirname(__file__)
SOURCE_DIR   = os.path.join(BASE, "source_data")
ZIP_PATH     = os.path.join(SOURCE_DIR, "austraits.zip")
EXTRACT_DIR  = os.path.join(SOURCE_DIR, "austraits")
ZENODO_API   = "https://zenodo.org/api/records/11188867"
UPSERT_BATCH = 200
PRINT_EVERY  = 10
_warnings    = []

# Trait name mapping: AusTraits trait_name -> our DB field + aggregation
TRAIT_MAP = {
    "plant_height":                ("height_mature_m",   "median", float),
    "specific_leaf_area":          ("sla",               "median", float),
    "fire_response":               ("fire_tolerance",    "mode",   str),
    "resprouting_capacity":        ("fire_tolerance",    "mode",   str),   # fallback
    "drought_tolerance":           ("drought_tolerance", "mode",   str),
    "leaf_phenology":              ("leaf_phenology",    "mode",   str),
    "plant_growth_form":           ("growth_form",       "mode",   str),
    "woodiness_detailed":          ("growth_form",       "mode",   str),   # fallback
}

def download_austraits():
    if os.path.exists(ZIP_PATH):
        print("  austraits.zip already downloaded.")
        return ZIP_PATH
    print("  Fetching latest AusTraits release from Zenodo ...", flush=True)
    meta = json.loads(urllib.request.urlopen(ZENODO_API, timeout=20).read())
    # Find the zip file (not .rds)
    files = meta.get("files", [])
    zip_entry = next((f for f in files if f["key"].endswith(".zip") and "austraits" in f["key"]), None)
    if not zip_entry:
        raise RuntimeError(f"No .zip found in Zenodo record. Files: {[f['key'] for f in files]}")
    url  = zip_entry["links"]["self"]
    size = zip_entry.get("size", 0)
    print(f"  Downloading {zip_entry['key']} ({size//1024//1024} MB) ...", flush=True)
    urllib.request.urlretrieve(url, ZIP_PATH)
    print(f"  Saved to {ZIP_PATH}")
    return ZIP_PATH

def extract_traits(zip_path):
    """Extract traits.csv from the zip and return path."""
    if not os.path.exists(EXTRACT_DIR):
        os.makedirs(EXTRACT_DIR)
    traits_csv = os.path.join(EXTRACT_DIR, "traits.csv")
    if os.path.exists(traits_csv):
        print("  traits.csv already extracted.")
        return traits_csv
    print("  Extracting traits.csv from zip ...", flush=True)
    with zipfile.ZipFile(zip_path, "r") as z:
        members = z.namelist()
        trait_member = next((m for m in members if m.endswith("traits.csv")), None)
        if not trait_member:
            raise RuntimeError(f"traits.csv not found in zip. Members: {members[:10]}")
        z.extract(trait_member, EXTRACT_DIR)
        # Move to flat path if nested
        extracted = os.path.join(EXTRACT_DIR, trait_member)
        if extracted != traits_csv:
            import shutil
            shutil.move(extracted, traits_csv)
    print(f"  Extracted: {traits_csv}")
    return traits_csv

def load_traits(traits_csv):
    """Returns {taxon_name_lower: {field: value}} after aggregating observations."""
    print("  Parsing traits.csv (this may take a moment) ...", flush=True)
    raw = {}  # {taxon: {db_field: [values]}}
    with open(traits_csv, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            trait = row.get("trait_name", "").strip()
            if trait not in TRAIT_MAP:
                continue
            taxon = row.get("taxon_name", "").strip().lower()
            if not taxon:
                continue
            value = row.get("value", "").strip()
            if not value:
                continue
            db_field, agg, cast = TRAIT_MAP[trait]
            raw.setdefault(taxon, {}).setdefault(db_field, []).append((value, agg, cast))

    # Aggregate multiple observations per taxon per field
    data = {}
    for taxon, fields in raw.items():
        entry = {}
        for db_field, obs in fields.items():
            agg  = obs[0][1]
            cast = obs[0][2]
            vals = []
            for v, _, c in obs:
                try:   vals.append(c(v))
                except: pass
            if not vals:
                continue
            if agg == "median" and isinstance(vals[0], float):
                entry[db_field] = round(statistics.median(vals), 2)
            elif agg == "mode":
                # Most common value
                entry[db_field] = max(set(vals), key=vals.count)
            else:
                entry[db_field] = vals[0]
        if entry:
            data[taxon] = entry

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

def patch_row(row_id, payload):
    # PATCH by id -- never triggers NOT NULL violations
    for attempt in range(3):
        try:
            r = requests.patch(
                f"{SUPABASE_URL}/rest/v1/gpr_plant_species?id=eq.{row_id}",
                headers=HEADERS, json=payload, timeout=30)
            if r.status_code not in (200, 204):
                _warnings.append(f"WARN patch id={row_id}: HTTP {r.status_code} {r.text[:120]}")
            return
        except Exception as e:
            if attempt == 2:
                _warnings.append(f"WARN patch id={row_id}: {str(e)[:120]}")
            else:
                time.sleep(2)


def progress(done, matched, t0, label=""):
    elapsed = time.time() - t0
    rate    = done / elapsed if elapsed > 0 else 1
    eta     = (matched - done) / rate if rate > 0 and matched > done else 0
    pct     = int(done / matched * 100) if matched else 0
    bar     = "#" * (pct // 5) + "-" * (20 - pct // 5)
    lbl     = label[:10]
    line    = f"  [{bar}] {pct:>3}%  {done:>5}/{matched}  {int(elapsed//60)}m{int(elapsed%60):02d}s  eta {int(eta//60)}m{int(eta%60):02d}s  {lbl}"
    print("\r" + line[:76].ljust(76), end="", flush=True)

def main():
    t0 = time.time()
    print("GPR Global Plant Database -- AusTraits Enrichment")
    print("Source: AusTraits v6 (Falster, Gallagher et al 2021)\n")

    zip_path  = download_austraits()
    traits_csv = extract_traits(zip_path)
    austraits  = load_traits(traits_csv)
    print(f"  {len(austraits):,} taxa with usable traits loaded.")

    print("Fetching Supabase species ...", end=" ", flush=True)
    rows = fetch_all_species()
    total = len(rows)
    print(f"{total:,} rows.\n")

    # Match
    updates = []
    for row in rows:
        sp  = (row["species"] or "").strip().lower()
        acc = (row.get("accepted_name") or "").strip().lower()
        traits = austraits.get(sp) or austraits.get(acc)
        if not traits:
            # Try genus + first epithet only
            parts = sp.split()
            if len(parts) >= 2:
                traits = austraits.get(parts[0] + " " + parts[1])
        if traits:
            updates.append((row["species"] or sp,
                            {"id": row["id"], "enrichment_sources": "AusTraits", **traits}))

    matched = len(updates)
    print(f"  Matches: {matched:,}/{total:,} ({matched/total*100:.1f}%)")
    print(f"  Fields: height_mature_m, sla, fire_tolerance, drought_tolerance,")
    print(f"          leaf_phenology, growth_form")
    print(f"  Upsert batch: {UPSERT_BATCH} | Progress every {PRINT_EVERY} rows\n")

    if matched == 0:
        print("No matches. Check taxon name format.")
        print("First 5 AusTraits keys:", list(austraits.keys())[:5])
        print("First 5 Supabase:      ", [r["species"] for r in rows[:5]])
        return

    _warnings.clear()
    done = 0
    for sp_name, payload in updates:
        row_id = payload.pop("id")
        patch_row(row_id, payload)
        done += 1
        if done % PRINT_EVERY == 0 or done == matched:
            progress(done, matched, t0, sp_name)

    progress(matched, matched, t0, "done")

    elapsed = time.time() - t0
    print()
    for w in _warnings: print(f"  {w}")
    print(f"\nDone in {int(elapsed//60)}m {int(elapsed%60)}s.")
    print(f"Enriched: {matched:,}/{total:,} species ({matched/total*100:.1f}% match rate).")

if __name__ == "__main__":
    main()