import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
"""
enrich_koppen.py
================
Second-pass enrichment for gpr_globalplantdb.csv.

Populates three fields for species that currently have them blank:
  - gbif_taxon_key   : GBIF backbone taxon ID
  - native_region    : Biogeographic realm (from GBIF distribution data)
  - native_koppen    : Köppen climate codes (inferred from native region/
                       occurrence data; full Beck-map integration is future work)

Runs AFTER build_gpr_globalplantdb.py.
Rate-limited to ~4 requests/second to be polite to GBIF API.

Run: python enrich_koppen.py
"""

import csv, time, requests, json
from pathlib import Path
from tqdm import tqdm

BASE  = Path(r"C:\_myProjects\+GPR\GPRTool\lai")
DB    = BASE / "gpr_globalplantdb.csv"
DELAY = 0.25  # seconds between GBIF API calls

GBIF_SPECIES  = "https://api.gbif.org/v1/species/match"
GBIF_DIST     = "https://api.gbif.org/v1/species/{key}/distributions"

# Biogeographic realm -> typical Köppen codes
# Source: Olson et al. (2001) biomes; Beck et al. (2018) Köppen map
REALM_KOPPEN = {
    "Afrotropical":  "Af,Am,Aw,BSh,BWh,Cfb",
    "Australasian":  "Af,Am,BWh,BSh,Cfa,Cfb,Csb",
    "Indomalayan":   "Af,Am,Aw,Cwa",
    "Nearctic":      "Dfb,Dfc,Cfa,Cfb,BSk,BWk,Csa",
    "Neotropical":   "Af,Am,Aw,BSh,Cfb,Cfa",
    "Palearctic":    "Cfb,Dfb,Dfc,Csa,Csb,BWk,BSk,ET",
    "Oceanian":      "Af,Am,Cfb,BSh",
}

# GBIF locality/country text -> realm (simplified heuristic)
LOCALITY_REALM = {
    "africa":         "Afrotropical",
    "subsaharan":     "Afrotropical",
    "ethiopia":       "Afrotropical",
    "kenya":          "Afrotropical",
    "nigeria":        "Afrotropical",
    "south africa":   "Afrotropical",
    "australia":      "Australasian",
    "new zealand":    "Australasian",
    "papua":          "Australasian",
    "indonesia":      "Indomalayan",
    "malaysia":       "Indomalayan",
    "india":          "Indomalayan",
    "thailand":       "Indomalayan",
    "singapore":      "Indomalayan",
    "china":          "Palearctic",
    "japan":          "Palearctic",
    "europe":         "Palearctic",
    "russia":         "Palearctic",
    "mediterranean":  "Palearctic",
    "united states":  "Nearctic",
    "canada":         "Nearctic",
    "mexico":         "Neotropical",
    "brazil":         "Neotropical",
    "colombia":       "Neotropical",
    "pacific":        "Oceanian",
}

FIELDS = [
    "id","species","accepted_name","gbif_taxon_key","family","order","common_name",
    "growth_form","landscape_category","leaf_phenology",
    "native_region","native_koppen",
    "lai_mean","lai_min","lai_max","lai_sd","lai_n",
    "lai_method","lai_context","lai_measurement_koppen","pft",
    "tier","tier_source","urban_context","sources","notes",
    "entry_date","data_version",
]


def infer_realm_from_distributions(distributions):
    """Parse GBIF distribution records to guess biogeographic realm."""
    text = " ".join(
        ((d.get("locality","") or "") + " " + (d.get("country","") or "")).lower()
        for d in distributions
    )
    for keyword, realm in LOCALITY_REALM.items():
        if keyword in text:
            return realm
    return ""


def enrich_species(species):
    """
    Query GBIF for one species.
    Returns (taxon_key, accepted_name, family, order, realm, koppen) or blanks.
    """
    try:
        r = requests.get(GBIF_SPECIES, params={"name": species, "kingdom": "Plantae"}, timeout=10)
        if not r.ok:
            return ("","","","","","")
        m = r.json()
        if m.get("matchType","NONE") == "NONE":
            return ("","","","","","")

        key           = str(m.get("usageKey",""))
        accepted_name = m.get("species","") or m.get("canonicalName","")
        family        = m.get("family","")
        order         = m.get("order","")

        # Get distribution data for realm inference
        realm = ""
        if key:
            time.sleep(DELAY)
            dr = requests.get(GBIF_DIST.format(key=key), timeout=10)
            if dr.ok:
                dists = dr.json().get("results",[])
                realm = infer_realm_from_distributions(dists)

        koppen = REALM_KOPPEN.get(realm,"")
        return (key, accepted_name, family, order, realm, koppen)

    except Exception:
        return ("","","","","","")


def enrich(max_species=None, tier_filter=None):
    """
    Enrich gpr_globalplantdb.csv with GBIF-derived fields.

    max_species  : limit for testing (None = all)
    tier_filter  : only enrich this tier (e.g. 1 for Tier 1 first)
    """
    if not DB.exists():
        print(f"ERROR: {DB} not found — run build_gpr_globalplantdb.py first")
        return

    with open(DB, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # Select rows to enrich: missing gbif_taxon_key
    to_enrich = [
        r for r in rows
        if not r.get("gbif_taxon_key","").strip()
        and (tier_filter is None or str(r.get("tier","")) == str(tier_filter))
    ]
    if max_species:
        to_enrich = to_enrich[:max_species]

    print(f"Rows to enrich: {len(to_enrich):,} (of {len(rows):,} total)")

    updated = 0
    for row in tqdm(to_enrich, desc="Enriching from GBIF"):
        key, aname, fam, ord_, realm, koppen = enrich_species(row["species"])
        if key:
            row["gbif_taxon_key"] = key
            if aname and not row.get("accepted_name",""):
                row["accepted_name"] = aname
            if fam and not row.get("family",""):
                row["family"] = fam
            if ord_ and not row.get("order",""):
                row["order"] = ord_
        if realm and not row.get("native_region",""):
            row["native_region"] = realm
        if koppen and not row.get("native_koppen",""):
            row["native_koppen"] = koppen
        if key or realm:
            updated += 1
        time.sleep(DELAY)

    # Write back
    with open(DB, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    print(f"\nEnriched: {updated:,} rows updated -> {DB.name}")
    print("Note: native_koppen is inferred from realm; full Beck-map")
    print("integration (occurrence-level) is a future enhancement.")


if __name__ == "__main__":
    # Default: enrich Tier 1+2 first (fast — only ~650 species)
    # Then run again with tier_filter=None for full 34K+ (slow, ~3 hrs)
    import sys
    if "--all" in sys.argv:
        enrich()
    else:
        print("Enriching Tier 1 and 2 species first (fast pass)...")
        enrich(tier_filter=1)
        enrich(tier_filter=2)
        print("\nTo enrich all 34K+ species (slow, ~3 hours):")
        print("  python enrich_koppen.py --all")
