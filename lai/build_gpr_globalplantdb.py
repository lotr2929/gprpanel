import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
"""
build_gpr_globalplantdb.py
==========================
Builds gpr_globalplantdb.csv — the GPRI Global Plant Database.

Merges all LAI sources in tier priority order (highest tier wins on duplicate).

Sources (priority order):
  1. LAI_global.csv              Tier 1-4, manually curated (592 species)
  2. LAI_categorised.csv         Tier 2, ORNL + TRY measured (760 species)
  3. LAI_gbif_comprehensive.csv  Tier 4, GBIF PFT mean (33,432 species)
  4. LAI_usda_tier4.csv          Tier 4, USDA PFT mean (if available)

Output  : gpr_globalplantdb.csv
Schema  : 28 fields in 6 sections (see gpr_globalplantdb_schema.md)
Version : 1.0.0

Run: python build_gpr_globalplantdb.py
"""

import csv, re
from pathlib import Path
from datetime import date
from collections import Counter

BASE    = Path(r"C:\_myProjects\+GPR\GPRTool\lai")
OUT     = BASE / "gpr_globalplantdb.csv"
VERSION = "1.0.0"
TODAY   = date.today().isoformat()

# ── Field order mirrors the 6 schema sections ─────────────────────────────
FIELDS = [
    # ── TAXONOMY
    "id", "species", "accepted_name", "gbif_taxon_key",
    "family", "order", "common_name",
    # ── BOTANICAL CLASSIFICATION
    "growth_form", "landscape_category", "leaf_phenology",
    # ── BIOGEOGRAPHY
    "native_region", "native_koppen",
    # ── LAI DATA
    "lai_mean", "lai_min", "lai_max", "lai_sd", "lai_n",
    "lai_method", "lai_context", "lai_measurement_koppen", "pft",
    # ── PROVENANCE
    "tier", "tier_source", "urban_context", "sources", "notes",
    # ── RECORD METADATA
    "entry_date", "data_version",
    # ── AI PROVENANCE
    "ai_assisted", "ai_model",
]

# ── Controlled vocabularies ────────────────────────────────────────────────
GROWTH_FORM_MAP = {
    "Tree":        "tree",
    "Shrub":       "shrub",
    "Groundcover": "herb",
    "Grass":       "graminoid",
    "Climber":     "liana",
    "Bamboo":      "bamboo",
    "Palm":        "palm",
    "Mangrove":    "mangrove",
    "REVIEW":      "",
}

# Rough native Köppen from climate string — enriched later by enrich_koppen.py
CLIMATE_KOPPEN = {
    "tropical":      "Af,Am,Aw",
    "subtropical":   "Cfa,Cwa,Cwb",
    "temperate":     "Cfb,Dfb,Dfc",
    "mediterranean": "Csa,Csb",
}

# tier_source -> (lai_context, urban_context, lai_method)
TIER_SOURCE_META = {
    "Direct_Urban_Field":  ("urban",    "TRUE",    "LAI-2000"),
    "ORNL_TRY_Measured":   ("natural",  "FALSE",   "mixed"),
    "Genus_Mean":          ("inferred", "UNKNOWN", "PFT-inferred"),
    "PFT_Mean_GBIF":       ("inferred", "UNKNOWN", "PFT-inferred"),
    "PFT_Mean_USDA":       ("inferred", "UNKNOWN", "PFT-inferred"),
}

BINOMIAL_RE = re.compile(r"^[A-Z][a-z]+([-\s][a-z]+)+$")

def is_valid_binomial(name):
    parts = name.strip().split()
    return len(parts) == 2 and bool(BINOMIAL_RE.match(name.strip()))

def infer_phenology(deciduous_str, pft=""):
    d = str(deciduous_str).strip().upper()
    if d == "TRUE":
        # Tropical/subtropical deciduous = drought-deciduous
        return "drought-deciduous" if (pft.startswith("Tr") or pft.startswith("Su")) else "deciduous"
    if d == "FALSE":
        return "evergreen"
    return ""

def blank_row():
    return {f: "" for f in FIELDS}

def make_row(**kw):
    row = blank_row()
    row["entry_date"]    = TODAY
    row["data_version"]  = VERSION
    row["lai_n"]         = 0
    row["urban_context"] = "UNKNOWN"
    row["ai_assisted"]   = ""
    row["ai_model"]      = ""
    row.update(kw)
    return row

# ── Source loaders ─────────────────────────────────────────────────────────

def load_global(seen):
    """LAI_global.csv — manually curated Tier 1-4 entries."""
    path = BASE / "LAI_global.csv"
    if not path.exists():
        print(f"  MISSING: {path.name}"); return []
    rows, added = [], 0
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            sp = r.get("species","").strip()
            if not sp or sp.lower() in seen:
                continue
            ts  = r.get("tier_source","").strip()
            pft = r.get("pft","").strip()
            cat = r.get("category","").strip()
            ctx, urban, method = TIER_SOURCE_META.get(ts, ("inferred","UNKNOWN","PFT-inferred"))
            # Tier 3 (genus mean) was AI-assisted; Tier 1 field measurements were not
            ai = "TRUE" if ts == "Genus_Mean" else "FALSE"
            rows.append(make_row(
                species           = sp,
                common_name       = r.get("common_name","").strip(),
                growth_form       = GROWTH_FORM_MAP.get(cat,""),
                landscape_category= cat,
                leaf_phenology    = infer_phenology(r.get("deciduous",""), pft),
                native_koppen     = CLIMATE_KOPPEN.get(r.get("climate","").strip(),""),
                lai_mean          = r.get("mean_lai",""),
                lai_min           = r.get("lai_min",""),
                lai_max           = r.get("lai_max",""),
                lai_n             = r.get("measurement_count","0"),
                lai_method        = method,
                lai_context       = ctx,
                pft               = pft,
                tier              = r.get("tier",""),
                tier_source       = ts,
                urban_context     = urban,
                sources           = r.get("sources","").strip(),
                notes             = r.get("notes","").strip(),
                ai_assisted       = ai,
                ai_model          = "claude-sonnet-4-6" if ai == "TRUE" else "",
            ))
            seen.add(sp.lower()); added += 1
    print(f"  LAI_global.csv              {added:>7,}  (Tier 1-4 curated)")
    return rows


def load_ornl_try(seen):
    """LAI_categorised.csv — ORNL + TRY Tier 2 measured."""
    path = BASE / "LAI_categorised.csv"
    if not path.exists():
        print(f"  MISSING: {path.name}"); return []
    rows, added, review = [], 0, 0
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            sp  = r.get("species","").strip()
            if not sp or sp.lower() in seen:
                continue
            cat = r.get("category","").strip()
            if not is_valid_binomial(sp):
                cat = "REVIEW"; review += 1
            tropical = str(r.get("tropical","")).strip().lower() == "true"
            src = r.get("sources","").strip()
            ds  = r.get("datasets","").strip()
            if ds and ds not in src:
                src = f"{src}; {ds}".strip("; ")
            note = "Measured in natural/plantation context; not urban."
            if cat == "REVIEW":
                note += " Non-standard name — flagged for review."
            rows.append(make_row(
                species           = sp,
                growth_form       = GROWTH_FORM_MAP.get(cat,""),
                landscape_category= cat,
                native_koppen     = "Af,Am,Aw" if tropical else "Cfb,Dfb,Dfc",
                lai_mean          = r.get("mean_lai",""),
                lai_min           = r.get("min_lai",""),
                lai_max           = r.get("max_lai",""),
                lai_n             = r.get("measurement_count","0"),
                lai_method        = "mixed",
                lai_context       = "natural",
                tier              = 2,
                tier_source       = "ORNL_TRY_Measured",
                urban_context     = "FALSE",
                sources           = src,
                notes             = note,
                ai_assisted       = "FALSE",
                ai_model          = "",
            ))
            seen.add(sp.lower()); added += 1
    print(f"  LAI_categorised.csv (ORNL+TRY){added:>6,}  ({review} flagged REVIEW)")
    return rows


def load_csv_tier4(filename, tier_source_val, seen):
    """Generic loader for Tier 4 sources (GBIF, USDA)."""
    path = BASE / filename
    if not path.exists():
        print(f"  {filename:<35}not found — skipping"); return []
    rows, added = [], 0
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            sp = r.get("species","").strip()
            if not sp or sp.lower() in seen:
                continue
            cat = r.get("category","").strip()
            pft = r.get("pft","").strip()
            rows.append(make_row(
                species           = sp,
                common_name       = r.get("common_name","").strip(),
                growth_form       = GROWTH_FORM_MAP.get(cat,""),
                landscape_category= cat,
                leaf_phenology    = infer_phenology(r.get("deciduous",""), pft),
                native_koppen     = CLIMATE_KOPPEN.get(r.get("climate","").strip(),""),
                lai_mean          = r.get("mean_lai",""),
                lai_min           = r.get("lai_min",""),
                lai_max           = r.get("lai_max",""),
                lai_n             = 0,
                lai_method        = "PFT-inferred",
                lai_context       = "inferred",
                pft               = pft,
                tier              = 4,
                tier_source       = tier_source_val,
                urban_context     = "UNKNOWN",
                sources           = r.get("sources","").strip(),
                notes             = r.get("notes","").strip(),
                ai_assisted       = "TRUE",
                ai_model          = "claude-sonnet-4-6",
            ))
            seen.add(sp.lower()); added += 1
    label = filename[:35]
    print(f"  {label:<35}{added:>6,}  (Tier 4 PFT mean)")
    return rows

# ── Main build ─────────────────────────────────────────────────────────────

def build():
    print("=" * 62)
    print("  GPR Global Plant Database — Build")
    print(f"  Version {VERSION}  |  {TODAY}")
    print("=" * 62)
    print("\nLoading sources (priority order — higher tier always wins):\n")

    seen     = set()
    all_rows = []
    all_rows += load_global(seen)
    all_rows += load_ornl_try(seen)
    all_rows += load_csv_tier4("LAI_gbif_comprehensive.csv", "PFT_Mean_GBIF", seen)
    all_rows += load_csv_tier4("LAI_usda_tier4.csv",         "PFT_Mean_USDA", seen)

    # Sort: tier -> landscape_category -> species
    all_rows.sort(key=lambda r: (
        int(r.get("tier") or 4),
        r.get("landscape_category",""),
        r.get("species",""),
    ))

    # Assign sequential IDs
    for i, row in enumerate(all_rows, 1):
        row["id"] = i

    # Write output
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(all_rows)

    # ── Summary ────────────────────────────────────────────────────────────
    tiers = Counter(str(r.get("tier","?")) for r in all_rows)
    cats  = Counter(r.get("landscape_category","?") for r in all_rows)
    mb    = round(OUT.stat().st_size / 1_048_576, 2)

    print(f"\n{'=' * 62}")
    print(f"  OUTPUT: gpr_globalplantdb.csv")
    print(f"  Total species : {len(all_rows):,}")
    print(f"  File size     : {mb} MB")
    print(f"\n  By tier:")
    print(f"    Tier 1  urban field measured   : {int(tiers.get('1',0)):>7,}")
    print(f"    Tier 2  ORNL/TRY measured      : {int(tiers.get('2',0)):>7,}")
    print(f"    Tier 3  genus mean             : {int(tiers.get('3',0)):>7,}")
    print(f"    Tier 4  PFT mean               : {int(tiers.get('4',0)):>7,}")
    print(f"\n  By landscape category:")
    for c, n in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"    {c:<22} {n:>7,}")
    print(f"{'=' * 62}")
    print(f"\n  Next steps:")
    print(f"    python enrich_koppen.py      — populate native_koppen from GBIF")
    print(f"    python upload_to_supabase.py — push to Supabase gpr_plant_species")


if __name__ == "__main__":
    build()
