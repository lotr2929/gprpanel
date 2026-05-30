"""
build_lai_master.py
===================
Merges all LAI data sources into one master database: LAI_master.csv

Sources in priority order:
  1. LAI_global.csv       — Tiers 1-4 (592 species, manually curated)
  2. LAI_usda_tier4.csv   — USDA PLANTS (~30,000-40,000 species)
  3. LAI_gbif_tier4.csv   — GBIF targeted genera (~2,000-5,000 species)

Deduplicates by species name (case-insensitive, earlier source wins).
Assigns final sequential IDs.

Run AFTER:
  python build_lai_global.py          (already done — 592 species)
  python download_usda_plants.py      (run first — downloads ~45K species)
  python download_gbif_plants.py      (run second — targeted tropical genera)

Then run:
  python build_lai_master.py

Output: LAI_master.csv (30,000+ species)
"""

import csv
from pathlib import Path
from collections import Counter

BASE = Path(r"C:\_myProjects\+GPR\GPRTool\lai")

SOURCES = [
    BASE / "LAI_global.csv",      # Tier 1-4, manually curated (highest priority)
    BASE / "LAI_usda_tier4.csv",  # USDA PLANTS (broad coverage)
    BASE / "LAI_gbif_tier4.csv",  # GBIF targeted genera
]

OUT = BASE / "LAI_master.csv"

FIELDS = [
    "id","species","common_name","category","mean_lai","lai_min","lai_max",
    "measurement_count","pft","canopy_form","climate","deciduous",
    "tier","tier_source","sources","notes"
]

def build():
    seen    = {}   # species_lower → row
    uid     = 1

    for src_path in SOURCES:
        if not src_path.exists():
            print(f"MISSING (skipping): {src_path.name}")
            continue
        count = 0
        with open(src_path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                sp_lower = row.get("species","").strip().lower()
                if not sp_lower or sp_lower in seen:
                    continue
                seen[sp_lower] = row
                count += 1
        print(f"Added from {src_path.name}: {count:,} species")

    # Sort: Tier 1 first, then by category, then alphabetically
    all_rows = list(seen.values())
    all_rows.sort(key=lambda r: (
        int(r.get("tier",4)),
        r.get("category",""),
        r.get("species","")
    ))

    # Reassign sequential IDs
    for i, row in enumerate(all_rows, 1):
        row["id"] = i

    # Write master
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(all_rows)

    # Summary
    tiers = Counter(r.get("tier",4) for r in all_rows)
    cats  = Counter(r.get("category","") for r in all_rows)

    print(f"\n{'='*60}")
    print(f"  LAI_master.csv: {len(all_rows):,} species")
    print(f"  Tier 1 (urban field measured): {tiers.get(1,0):,}")
    print(f"  Tier 2 (ORNL/TRY measured):    {tiers.get(2,0):,}")
    print(f"  Tier 3 (genus mean):            {tiers.get(3,0):,}")
    print(f"  Tier 4 (PFT mean):              {tiers.get(4,0):,}")
    print(f"\n  By category:")
    for cat, n in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"    {cat:<20} {n:,}")
    print(f"  Output: {OUT}")
    print(f"{'='*60}")

if __name__ == "__main__":
    build()
