"""
enrich_panel_db.py
==================
Enriches the plugin plants_db.json with rich data from:
  1. gpr_globalplantdb_enriched.csv  (LAI provenance, tier, sources, koppen, phenology)
  2. Wikipedia REST API              (mature height, growth rate, canopy spread, common names)
  3. GBIF Species API                (family, accepted name, native distribution)
  4. USDA PlantAtlas SQLite          (growth_rate, drought/shade/fire/salinity tolerance)
     - Download from https://data.plantatlas.ai/ -> source_data/usda_plants.db
  5. Koppen description lookup       (plain-English climate from native_koppen codes)

Output: plants_db_enriched.json  (all categories, rich schema v2.0)
        plants_db_enriched_brief.json  (brief-view fields only, for panel display)

Run:    python enrich_panel_db.py
Author: Boon Lay Ong / GPRI  2026-05-28
"""

import csv, json, re, time, os, sys, sqlite3
import urllib.request, urllib.parse
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE        = r"C:\_myProjects\_GPR\GPR-PlantDB\lai"
GLOBAL_CSV  = os.path.join(BASE, "gpr_globalplantdb_enriched.csv")
PANEL_JSON  = r"C:\_myProjects\_GPR\GPR+AutoCAD\www\plants_db.json"
USDA_DB     = os.path.join(BASE, "source_data", "usda_plants.db")
OUT_FULL    = os.path.join(BASE, "plants_db_enriched.json")
OUT_BRIEF   = os.path.join(BASE, "plants_db_enriched_brief.json")
RATE_LIMIT  = 0.4   # seconds between API calls

# ── Koppen plain-English descriptions ──────────────────────────────────────────
KOPPEN_DESC = {
    "Af":  "Tropical rainforest",
    "Am":  "Tropical monsoon",
    "Aw":  "Tropical savanna (dry winter)",
    "As":  "Tropical savanna (dry summer)",
    "BWh": "Hot desert",
    "BWk": "Cold desert",
    "BSh": "Hot semi-arid (steppe)",
    "BSk": "Cold semi-arid (steppe)",
    "Csa": "Hot-summer mediterranean",
    "Csb": "Warm-summer mediterranean",
    "Csc": "Cold-summer mediterranean",
    "Cwa": "Humid subtropical, dry winter",
    "Cwb": "Subtropical highland, dry winter",
    "Cwc": "Cold subtropical highland",
    "Cfa": "Humid subtropical",
    "Cfb": "Temperate oceanic",
    "Cfc": "Subpolar oceanic",
    "Dsa": "Hot-summer continental, dry summer",
    "Dsb": "Warm-summer continental, dry summer",
    "Dsc": "Cold continental, dry summer",
    "Dwa": "Hot-summer continental, dry winter",
    "Dwb": "Warm-summer continental, dry winter",
    "Dwc": "Cold continental, dry winter",
    "Dfa": "Hot-summer humid continental",
    "Dfb": "Warm-summer humid continental",
    "Dfc": "Subarctic",
    "Dfd": "Extremely cold subarctic",
    "ET":  "Tundra",
    "EF":  "Ice cap",
}

def koppen_to_english(codes_str):
    """Convert 'Af,Am,Cfb' to 'Tropical rainforest, tropical monsoon, temperate oceanic'."""
    if not codes_str:
        return ""
    codes = [c.strip() for c in codes_str.split(",") if c.strip()]
    descs = []
    for c in codes:
        d = KOPPEN_DESC.get(c)
        if d and d not in descs:
            descs.append(d)
    return ", ".join(descs)

# ── Growth rate label ──────────────────────────────────────────────────────────
def growth_label(rate_str):
    r = (rate_str or "").lower().strip()
    if r in ("rapid", "fast"):    return "fast"
    if r in ("moderate", "med"): return "moderate"
    if r in ("slow",):           return "slow"
    return r

# ── Load global DB ─────────────────────────────────────────────────────────────
def load_global_db():
    """Returns {species_lower: row_dict} from gpr_globalplantdb_enriched.csv"""
    data = {}
    if not os.path.exists(GLOBAL_CSV):
        print(f"  WARNING: {GLOBAL_CSV} not found"); return data
    with open(GLOBAL_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = row["species"].strip().lower()
            if key:
                data[key] = dict(row)
    print(f"  Global DB loaded: {len(data):,} species")
    return data

# ── Load USDA SQLite ───────────────────────────────────────────────────────────
def load_usda_db():
    """Returns {scientific_name_lower: traits} or {} if DB not present."""
    if not os.path.exists(USDA_DB):
        print("  USDA DB not found - skipping (download from https://data.plantatlas.ai/)")
        return {}
    try:
        conn = sqlite3.connect(USDA_DB)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT p.scientific_name,
                   c.growth_rate, c.drought_tolerance, c.shade_tolerance,
                   c.salinity_tolerance, c.fire_tolerance,
                   c.height_mature_feet, c.nitrogen_fixation
            FROM plant_characteristics c
            JOIN plants p ON p.id = c.plant_id
            WHERE p.rank = 'Species'
        """).fetchall()
        conn.close()
        data = {}
        for row in rows:
            name = (row["scientific_name"] or "").strip().lower()
            if name:
                data[name] = {
                    "growth_rate":       (row["growth_rate"] or "").lower() or None,
                    "drought_tolerance": (row["drought_tolerance"] or "").lower() or None,
                    "shade_tolerance":   (row["shade_tolerance"] or "").lower() or None,
                    "salt_tolerance":    (row["salinity_tolerance"] or "").lower() or None,
                    "fire_tolerance":    (row["fire_tolerance"] or "").lower() or None,
                    "height_mature_ft":  float(row["height_mature_feet"] or 0) or None,
                }
        print(f"  USDA DB loaded: {len(data):,} species")
        return data
    except Exception as e:
        print(f"  USDA DB error: {e}"); return {}

# ── Wikipedia API (improved) ───────────────────────────────────────────────────
WIKI_API = "https://en.wikipedia.org/api/rest_v1/page/summary/"

RE_HEIGHT = re.compile(
    r'(\d+(?:\.\d+)?)\s*(?:to|–|-|or)\s*(\d+(?:\.\d+)?)\s*m\b'
    r'|(?:up\s+to|reach(?:es|ing)?|grow[s]?\s+to|height\s+of|tall\s+as)\s+(\d+(?:\.\d+)?)\s*m\b'
    r'|(\d+(?:\.\d+)?)\s*m\s*(?:tall|high|in\s+height|in\s+stature)',
    re.IGNORECASE)

RE_SPREAD = re.compile(
    r'spread[s]?\s+(?:of\s+|to\s+)?(\d+(?:\.\d+)?)\s*(?:to|–|-)\s*(\d+(?:\.\d+)?)?\s*m\b'
    r'|canopy\s+(?:width|spread|diameter)\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*m\b'
    r'|(\d+(?:\.\d+)?)\s*m\s*wide',
    re.IGNORECASE)

RE_GROWTH_QUAL = re.compile(
    r'(?:grows?\s+(?:at\s+)?(?:a\s+)?|growth\s+rate\s+(?:is\s+)?)(rapid(?:ly)?|fast|moderate(?:ly)?|slow(?:ly)?)',
    re.IGNORECASE)

RE_GROWTH_QUANT = re.compile(
    r'(\d+(?:\.\d+)?)\s*(?:to|–|-)\s*(\d+(?:\.\d+)?)\s*cm\s*(?:per\s+year|a\s+year|\/year|annually)'
    r'|(?:annual\s+growth|grows?\s+)\s*(?:of\s+|up\s+to\s+)?(\d+(?:\.\d+)?)\s*cm',
    re.IGNORECASE)

def wiki_lookup(species_name):
    result = {}
    try:
        url = WIKI_API + urllib.parse.quote(species_name.replace(" ", "_"))
        req = urllib.request.Request(url, headers={"User-Agent": "GPRPanel/2.0 (GPRI)"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        extract = data.get("extract", "")
        thumb   = data.get("thumbnail", {}).get("source", "")
        if thumb:
            result["wiki_photo_url"] = thumb
        if extract:
            result["wiki_extract"] = extract[:600]

        # Height
        m = RE_HEIGHT.search(extract)
        if m:
            vals = [float(x) for x in m.groups() if x]
            if len(vals) >= 2:
                result["height_mature_m"] = round(sum(vals[:2]) / 2, 1)
            elif vals:
                result["height_mature_m"] = float(vals[0])

        # Spread
        m = RE_SPREAD.search(extract)
        if m:
            vals = [float(x) for x in m.groups() if x]
            if vals:
                result["canopy_radius_m"] = round(max(vals) / 2, 1)

        # Growth rate qualitative
        m = RE_GROWTH_QUAL.search(extract)
        if m:
            result["growth_rate_label"] = growth_label(m.group(1))

        # Growth rate quantitative
        m = RE_GROWTH_QUANT.search(extract)
        if m:
            vals = [float(x) for x in m.groups() if x]
            if len(vals) >= 2:
                result["growth_rate_cm_yr_min"] = vals[0]
                result["growth_rate_cm_yr_max"] = vals[1]
                mid = (vals[0] + vals[1]) / 2
            elif vals:
                result["growth_rate_cm_yr_min"] = vals[0]
                result["growth_rate_cm_yr_max"] = vals[0]
                mid = vals[0]
            else:
                mid = 0
            if mid and not result.get("growth_rate_label"):
                result["growth_rate_label"] = "fast" if mid > 60 else "moderate" if mid > 25 else "slow"

    except Exception:
        pass
    return result

def wiki_lookup(species_name):
    """Returns dict with height_m, spread_m, growth_rate_label, description, photo_url"""
    result = {}
    try:
        url = WIKI_API + urllib.parse.quote(species_name.replace(" ", "_"))
        req = urllib.request.Request(url, headers={"User-Agent": "GPRPanel/2.0 (GPRI)"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data    = json.loads(resp.read())
        extract = data.get("extract", "")
        thumb   = data.get("thumbnail", {}).get("source", "")
        if thumb:
            result["wiki_photo_url"] = thumb

        # Height
        m = RE_HEIGHT.search(extract)
        if m:
            if m.group(1) and m.group(2):
                result["height_mature_m"] = round((float(m.group(1)) + float(m.group(2))) / 2, 1)
            elif m.group(3):
                result["height_mature_m"] = float(m.group(3))

        # Spread
        m = RE_SPREAD.search(extract)
        if m:
            vals = [float(x) for x in m.groups() if x]
            if vals:
                result["canopy_radius_m"] = round(max(vals) / 2, 1)

        # Growth rate
        m = RE_GROWTH.search(extract)
        if m:
            if m.group(1):  # qualitative
                result["growth_rate_label"] = growth_label(m.group(1))
            elif m.group(2):  # cm/yr
                lo = float(m.group(2))
                hi = float(m.group(3)) if m.group(3) else lo
                result["growth_rate_cm_yr_min"] = lo
                result["growth_rate_cm_yr_max"] = hi
                mid = (lo + hi) / 2
                result["growth_rate_label"] = "fast" if mid > 60 else "moderate" if mid > 25 else "slow"

        result["wiki_extract"] = extract[:500] if extract else ""
    except Exception:
        pass
    return result

# ── GBIF Species API ───────────────────────────────────────────────────────────
GBIF_API = "https://api.gbif.org/v1/species/match?name="

def gbif_lookup(species_name):
    result = {}
    try:
        url = GBIF_API + urllib.parse.quote(species_name)
        req = urllib.request.Request(url, headers={"User-Agent": "GPRPanel/2.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read())
        if data.get("matchType") not in ("NONE", None):
            result["family"]        = data.get("family", "")
            result["order"]         = data.get("order", "")
            result["accepted_name"] = data.get("species", species_name)
            result["gbif_key"]      = data.get("usageKey", "")
    except Exception:
        pass
    return result

# ── Extract flat species list from panel JSON ──────────────────────────────────
def extract_panel_species(panel):
    """Returns flat list of (category, entry_dict) from nested panel JSON."""
    species = []
    cat_map = {
        "trees":       "Tree",
        "shrubs":      "Shrub",
        "groundcover": "Groundcover",
        "hedges":      "Shrub",
        "climbers":    "Climber",
        "palms":       "Palm",
        "bamboos":     "Bamboo",
        "grasses":     "Grass",
    }
    if isinstance(panel, list):
        for entry in panel:
            species.append(("Tree", entry))
    elif isinstance(panel, dict):
        for key, entries in panel.items():
            cat = cat_map.get(key.lower(), key.capitalize())
            if isinstance(entries, list):
                for entry in entries:
                    species.append((cat, entry))
    return species

# ── Build rich record ──────────────────────────────────────────────────────────
def build_record(cat, entry, global_db, usda_db):
    sp_name = entry.get("name", "").strip()
    sp_key  = sp_name.lower()

    # Base from panel
    rec = {
        "species":            sp_name,
        "landscape_category": cat,
        "lai_panel":          entry.get("lai"),
        "height_panel_m":     entry.get("height"),
        "canopy_radius_panel_m": entry.get("radius"),
        "canopy_shape":       entry.get("shape", ""),
        # placeholders
        "common_names":       entry.get("common", ""),
        "family":             "",
        "order":              "",
        "accepted_name":      "",
        "gbif_key":           "",
        "growth_form":        "",
        "leaf_phenology":     "",
        "native_region":      "",
        "native_koppen":      "",
        "koppen_description": "",
        "lai_mean":           None,
        "lai_min":            None,
        "lai_max":            None,
        "lai_sd":             None,
        "lai_n":              None,
        "lai_method":         "",
        "lai_context":        "",
        "pft":                "",
        "tier":               None,
        "tier_label":         "",
        "tier_source":        "",
        "urban_context":      "",
        "sources_lai":        entry.get("source", ""),
        "sources_other":      "",
        "notes":              "",
        "height_mature_m":    None,
        "canopy_radius_m":    None,
        "growth_rate_label":  "",
        "growth_rate_cm_yr_min": None,
        "growth_rate_cm_yr_max": None,
        "growth_rate_m_yr_display": "",
        "drought_tolerance":  "",
        "shade_tolerance":    "",
        "salt_tolerance":     "",
        "fire_tolerance":     "",
        "wiki_photo_url":     "",
        "wiki_extract":       "",
        "data_completeness":  "partial",
    }

    TIER_LABELS = {
        "1": "T1 — Urban field",
        "2": "T2 — Literature",
        "3": "T3 — Genus mean",
        "4": "T4 — PFT mean",
    }

    # ── 1. Merge from global DB ────────────────────────────────────────────────
    gdata = global_db.get(sp_key)
    if not gdata:
        # Try genus-level match
        genus = sp_name.split()[0].lower() + " "
        for k, v in global_db.items():
            if k.startswith(genus):
                gdata = v; break
    if gdata:
        rec["family"]           = gdata.get("family", "")
        rec["order"]            = gdata.get("order", "")
        rec["accepted_name"]    = gdata.get("accepted_name", sp_name)
        rec["gbif_key"]         = gdata.get("gbif_taxon_key", "")
        rec["growth_form"]      = gdata.get("growth_form", "")
        rec["leaf_phenology"]   = gdata.get("leaf_phenology", "")
        rec["native_region"]    = gdata.get("native_region", "")
        rec["native_koppen"]    = gdata.get("native_koppen", "")
        rec["koppen_description"] = koppen_to_english(gdata.get("native_koppen",""))
        rec["pft"]              = gdata.get("pft", "")
        rec["tier"]             = gdata.get("tier", "")
        rec["tier_label"]       = TIER_LABELS.get(str(gdata.get("tier","")), "")
        rec["tier_source"]      = gdata.get("tier_source", "")
        rec["urban_context"]    = gdata.get("urban_context", "")
        rec["sources_lai"]      = gdata.get("sources", rec["sources_lai"])
        rec["notes"]            = gdata.get("notes", "")
        if not rec["common_names"]:
            rec["common_names"] = gdata.get("common_name", "")
        for f in ["lai_mean","lai_min","lai_max","lai_sd","lai_n","lai_method","lai_context"]:
            val = gdata.get(f)
            if val not in (None,""):
                try:    rec[f] = float(val) if f != "lai_method" and f != "lai_context" else val
                except: rec[f] = val

    # ── 2. USDA traits ─────────────────────────────────────────────────────────
    udata = usda_db.get(sp_key)
    if not udata:
        # Try accepted name
        acc = rec["accepted_name"].lower()
        udata = usda_db.get(acc)
    if udata:
        for field in ["growth_rate","drought_tolerance","shade_tolerance","salt_tolerance","fire_tolerance"]:
            if udata.get(field):
                rec[field] = udata[field]
        if udata.get("height_mature_ft"):
            rec["height_mature_m"] = round(udata["height_mature_ft"] * 0.3048, 1)

    return rec

def finalise_record(rec, wiki):
    """Merge Wikipedia results and build display fields."""
    if wiki.get("height_mature_m") and not rec["height_mature_m"]:
        rec["height_mature_m"] = wiki["height_mature_m"]
    if wiki.get("canopy_radius_m") and not rec["canopy_radius_m"]:
        rec["canopy_radius_m"] = wiki["canopy_radius_m"]
    if wiki.get("growth_rate_label") and not rec["growth_rate_label"]:
        rec["growth_rate_label"] = wiki["growth_rate_label"]
    for f in ["growth_rate_cm_yr_min","growth_rate_cm_yr_max","wiki_photo_url","wiki_extract"]:
        if wiki.get(f):
            rec[f] = wiki[f]

    # Build display growth rate string
    lo = rec.get("growth_rate_cm_yr_min")
    hi = rec.get("growth_rate_cm_yr_max")
    label = rec.get("growth_rate_label","")
    if lo and hi:
        lo_m, hi_m = round(lo/100, 2), round(hi/100, 2)
        rec["growth_rate_m_yr_display"] = f"{lo_m}–{hi_m} m/yr ({label})" if label else f"{lo_m}–{hi_m} m/yr"
    elif label:
        rec["growth_rate_m_yr_display"] = label.capitalize()

    # Fall back height to panel value
    if not rec["height_mature_m"] and rec.get("height_panel_m"):
        rec["height_mature_m"] = rec["height_panel_m"]
    if not rec["canopy_radius_m"] and rec.get("canopy_radius_panel_m"):
        rec["canopy_radius_m"] = rec["canopy_radius_panel_m"]

    # Data completeness score
    filled = sum(1 for f in ["lai_mean","native_koppen","family","height_mature_m","growth_rate_label",
                              "drought_tolerance","shade_tolerance","tier"] if rec.get(f))
    rec["data_completeness"] = "full" if filled >= 7 else "good" if filled >= 5 else "partial"
    return rec

def brief(rec):
    """Return brief-view fields only."""
    return {
        "species":          rec["species"],
        "common_names":     rec["common_names"],
        "accepted_name":    rec["accepted_name"],
        "landscape_category": rec["landscape_category"],
        "growth_form":      rec["growth_form"],
        "leaf_phenology":   rec["leaf_phenology"],
        "koppen_description": rec["koppen_description"],
        "native_koppen":    rec["native_koppen"],
        "lai_mean":         rec["lai_mean"],
        "lai_min":          rec["lai_min"],
        "lai_max":          rec["lai_max"],
        "tier":             rec["tier"],
        "tier_label":       rec["tier_label"],
        "sources_lai":      rec["sources_lai"],
        "sources_other":    rec["sources_other"],
        "height_mature_m":  rec["height_mature_m"],
        "canopy_radius_m":  rec["canopy_radius_m"],
        "growth_rate_m_yr_display": rec["growth_rate_m_yr_display"],
        "drought_tolerance": rec["drought_tolerance"],
        "shade_tolerance":  rec["shade_tolerance"],
        "fire_tolerance":   rec["fire_tolerance"],
        "wiki_photo_url":   rec["wiki_photo_url"],
        "data_completeness": rec["data_completeness"],
    }

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    print("=" * 62)
    print("  GPR Panel DB Enrichment  v2.0")
    print("=" * 62 + "\n")

    # Load sources
    print("Loading data sources...")
    global_db = load_global_db()
    usda_db   = load_usda_db()

    # Load panel species
    with open(PANEL_JSON, encoding="utf-8") as f:
        panel = json.load(f)
    species_list = extract_panel_species(panel)
    total = len(species_list)
    print(f"  Panel species: {total}\n")

    # Check for GBIF — only call if family is missing
    use_gbif = True

    full_records = []
    brief_records = []
    wiki_hits = gbif_hits = usda_hits = global_hits = 0

    for i, (cat, entry) in enumerate(species_list, 1):
        sp_name = entry.get("name","").strip()
        if not sp_name:
            continue

        print(f"  [{i:>3}/{total}] {sp_name}")

        # Build base record
        rec = build_record(cat, entry, global_db, usda_db)
        if rec["tier"]:
            global_hits += 1
        if rec.get("drought_tolerance") or rec.get("growth_rate"):
            usda_hits += 1

        # GBIF lookup if family still missing
        if use_gbif and not rec["family"]:
            gdata = gbif_lookup(sp_name)
            if gdata:
                gbif_hits += 1
                for k, v in gdata.items():
                    if not rec.get(k):
                        rec[k] = v
            time.sleep(RATE_LIMIT)

        # Wikipedia lookup
        wiki = wiki_lookup(sp_name)
        if wiki.get("height_mature_m") or wiki.get("growth_rate_label"):
            wiki_hits += 1
        time.sleep(RATE_LIMIT)

        rec = finalise_record(rec, wiki)
        full_records.append(rec)
        brief_records.append(brief(rec))

    # Write outputs
    with open(OUT_FULL, "w", encoding="utf-8") as f:
        json.dump(full_records, f, indent=2, ensure_ascii=False)
    with open(OUT_BRIEF, "w", encoding="utf-8") as f:
        json.dump(brief_records, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 62}")
    print(f"  Done. {total} species processed.")
    print(f"  Global DB matches : {global_hits}/{total}")
    print(f"  USDA matches      : {usda_hits}/{total}")
    print(f"  Wikipedia hits    : {wiki_hits}/{total}")
    print(f"  GBIF hits         : {gbif_hits}/{total}")
    print(f"  Full output       : {OUT_FULL}")
    print(f"  Brief output      : {OUT_BRIEF}")
    print(f"{'=' * 62}")

    # Coverage report
    fields_to_check = ["family","native_koppen","lai_mean","tier","height_mature_m",
                        "growth_rate_label","drought_tolerance","shade_tolerance","fire_tolerance"]
    print("\n  Field coverage:")
    for fld in fields_to_check:
        n = sum(1 for r in full_records if r.get(fld))
        print(f"    {fld:<30} {n:>4}/{total}")

if __name__ == "__main__":
    main()

